import numpy as np
from core.filter_base import FilterBase, ParamDef


class Invert(FilterBase):
    """Invert image colors (negative effect)."""

    name = "Invert"
    category = "Color"

    def get_parameters(self) -> list[ParamDef]:
        return []

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        return np.uint8(255 - image.astype(np.int16))
