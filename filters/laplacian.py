import cv2
import numpy as np
from core.filter_base import FilterBase, ParamDef


class Laplacian(FilterBase):
    """Detect edges using the Laplacian operator (2nd derivative)."""

    name = "Laplacian"
    category = "Edge Detection"

    def get_parameters(self) -> list[ParamDef]:
        return [
            ParamDef(
                name="ksize",
                label="Kernel Size",
                param_type="int_spin",
                default=3,
                min_val=1,
                max_val=31,
                step=2,
            ),
            ParamDef(
                name="scale",
                label="Scale",
                param_type="slider",
                default=1.0,
                min_val=0.1,
                max_val=5.0,
                step=0.1,
            ),
            ParamDef(
                name="invert",
                label="Invert",
                param_type="checkbox",
                default=False,
            ),
        ]

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        ksize = int(params.get("ksize", 3))
        if ksize % 2 == 0:
            ksize += 1
        scale = float(params.get("scale", 1.0))
        invert = bool(params.get("invert", False))

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        lap = cv2.Laplacian(gray, cv2.CV_64F, ksize=ksize, scale=scale)
        lap = np.uint8(np.absolute(lap))
        if invert:
            lap = 255 - lap
        return cv2.cvtColor(lap, cv2.COLOR_GRAY2RGB)
