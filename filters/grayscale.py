import cv2
import numpy as np
from core.filter_base import FilterBase, ParamDef


class Grayscale(FilterBase):
    """Convert the image to grayscale."""

    name = "Grayscale"
    category = "Color"

    def get_parameters(self) -> list[ParamDef]:
        return []

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
