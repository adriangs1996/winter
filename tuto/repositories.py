from tuto.viewmodels import AllocationsViewModel
from wintry.ioc import provider
from wintry.repository import Repository, IRepository
from .models import Product


@provider
class ProductRepository(Repository[Product, str], entity=Product):
    async def get_by_sku(self, *, sku: str) -> Product | None:
        ...

    async def get_by_batches__reference(
        self, *, batches__reference: str
    ) -> Product | None:
        ...


@provider
class AllocationViewModelRepository(
    IRepository, entity=AllocationsViewModel, for_backend="mongo"
):
    async def find_by_orderid(self, *, orderid: str) -> list[AllocationsViewModel]:
        ...

    async def create(self, *, entity: AllocationsViewModel) -> AllocationsViewModel:
        ...

    async def delete_by_orderid_and_sku(self, *, orderid: str, sku: str):
        ...
