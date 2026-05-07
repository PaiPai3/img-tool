from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import numpy as np


@dataclass
class ParamDef:
    name: str
    label: str
    param_type: str = "slider"        # "slider", "int_spin", "checkbox", "dropdown"
    default: float = 0.0
    min_val: float = 0.0
    max_val: float = 100.0
    step: float = 1.0
    options: list = field(default_factory=list)   # for "dropdown"


class FilterBase(ABC):
    name: str = ""
    category: str = ""

    @abstractmethod
    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        ...

    @abstractmethod
    def get_parameters(self) -> list[ParamDef]:
        ...

    @property
    def description(self) -> str:
        return self.__doc__ or ""
