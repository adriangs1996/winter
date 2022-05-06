import logging
from pathlib import Path
from winter.settings import WinterSettings
import importlib


class LoaderError(Exception):
    pass


def to_package_format(path: Path) -> str:
    module_fs_path = ".".join(path.parts)
    # remove module last .py extension
    module = module_fs_path.replace(".py", "")
    # if module is like "path.to.module.__init__", then
    # leave it as "path.to.module"
    if module.endswith(".__init__"):
        return module.replace(".__init__", "")

    return module


def autodiscover_modules(settings: WinterSettings = WinterSettings()):
    logger = logging.getLogger("logger")
    app_root = Path(settings.app_root)

    if not app_root.is_dir():
        raise LoaderError(f"settings.app_root is not a dir: {app_root}")

    dirs: list[Path] = [app_root]
    while dirs:
        module = dirs.pop(0)
        for sub_module in module.iterdir():
            if sub_module.is_dir():
                dirs.append(sub_module)
            else:
                if sub_module.name.endswith(".py"):
                    try:
                        mod = to_package_format(sub_module)
                        logger.info(f"Loading module {mod}")
                        importlib.import_module(mod)
                    except ModuleNotFoundError as e:
                        raise LoaderError(str(e))
