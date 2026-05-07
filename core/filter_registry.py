import importlib
import pkgutil
import inspect
from core.filter_base import FilterBase


class FilterRegistry:
    _filters: dict[str, type[FilterBase]] = {}
    _by_category: dict[str, list[tuple[str, type[FilterBase]]]] = {}
    _loaded = False

    @classmethod
    def discover(cls):
        if cls._loaded:
            return
        cls._loaded = True
        import filters as pkg
        pkg_path = pkg.__path__
        for _, module_name, _ in pkgutil.iter_modules(pkg_path):
            module = importlib.import_module(f"filters.{module_name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type)
                        and issubclass(attr, FilterBase)
                        and attr is not FilterBase):
                    instance = attr()
                    cls._filters[instance.name] = attr
                    cat = instance.category or "Other"
                    cls._by_category.setdefault(cat, []).append(
                        (instance.name, attr)
                    )

    @classmethod
    def get_categories(cls) -> dict[str, list[tuple[str, type[FilterBase]]]]:
        cls.discover()
        return dict(cls._by_category)

    @classmethod
    def get_filter(cls, name: str) -> type[FilterBase] | None:
        cls.discover()
        return cls._filters.get(name)

    @classmethod
    def list_names(cls) -> list[str]:
        cls.discover()
        return list(cls._filters.keys())
