from typing import Any, TypeVar
from winter import get_session, commit, close_session, rollback
from winter.repository.base import __RepositoryType__, NO_SQL
from winter.sessions import MongoSessionTracker
from winter.utils.keys import (
    __winter_manage_objects__,
    __winter_tracker__,
    __winter_session_key__,
    __RepositoryType__,
    __winter_backend_identifier_key__,
)

T = TypeVar("T")
TypeId = TypeVar("TypeId")


class UnitOfWorkError(Exception):
    pass


class UnitOfWork:
    def __init__(self, **kwargs: Any) -> None:
        self.repositories = kwargs.copy()
        self.session: Any | None = None

        for repository in self.repositories.values():
            self.backend = getattr(repository, __winter_backend_identifier_key__, "default")
            break

        backends = list(
            getattr(repository, __winter_backend_identifier_key__, "default")
            for repository in self.repositories.values()
        )

        if not all(backend == self.backend for backend in backends):
            raise UnitOfWorkError(f"UnitOfWork can not be configured for different backends: {backends}")

    async def commit(self) -> None:
        """
        Commits a sequence of statements
        """
        if self.session is not None:
            for repo in self.repositories.values():
                if (
                    getattr(repo, __winter_manage_objects__, False)
                    and getattr(repo, __RepositoryType__, None) == NO_SQL
                ):
                    tracker: MongoSessionTracker = getattr(repo, __winter_tracker__)
                    await tracker.flush(self.session)
            await commit(self.session, self.backend)

    async def rollback(self) -> None:
        if self.session is not None:
            await rollback(self.session, self.backend)

    async def __aenter__(self) -> "UnitOfWork":
        """
        Make a unify interface for sesssion management between
        repositories. `get_session()` returns a session based on
        the configured backend, and works on that interface.
        """
        self.session = await get_session(self.backend)
        # Repositories internally use a session for their operations.
        # If that session is None, then the operation is executed in
        # an isolated action, but if we managed the session from outside,
        # we can provide atomicity to a sequence of operations.

        # Trust that the provided session comes already initialized
        for repo in self.repositories.values():
            setattr(repo, __winter_session_key__, self.session)
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        """
        By deafault, `UnitOfWork` aborts transaction on context
        exit. This is intentionally to avoid unwanted changes
        to go to the DB, in fact, is safer than the alternative.
        Also, explicit commit makes read the code a little bit nicer
        """
        await self.rollback()
        await close_session(self.session, self.backend)
        self.session = None
        for repo in self.repositories.values():
            setattr(repo, __winter_session_key__, None)
            if (
                getattr(repo, __winter_manage_objects__, False)
                and getattr(repo, __RepositoryType__, None) == NO_SQL
            ):
                tracker: MongoSessionTracker = getattr(repo, __winter_tracker__)
                tracker.clean()

    def __getattribute__(self, __name: str) -> Any:
        """
        `UnitOfWork` is a handy place to provide access to all repositories.
        """
        repository = super().__getattribute__("repositories").get(__name, None)
        if repository is None:
            return super().__getattribute__(__name)
        else:
            return repository


__all__ = ["UnitOfWork"]
