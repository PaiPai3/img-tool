import cv2
import numpy as np
from core.filter_base import FilterBase, ParamDef


class Sobel(FilterBase):
    """Detect edges using the Sobel operator (1st derivative)."""

    name = "Sobel"
    category = "Edge Detection"

    def get_parameters(self) -> list[ParamDef]:
        return [
            ParamDef(
                name="dx",
                label="Derivative X",
                param_type="int_spin",
                default=0,
                min_val=0,
                max_val=2,
                step=1,
            ),
            ParamDef(
                name="dy",
                label="Derivative Y",
                param_type="int_spin",
                default=1,
                min_val=0,
                max_val=2,
                step=1,
            ),
            ParamDef(
                name="ksize",
                label="Kernel Size",
                param_type="dropdown",
                default="3",
                options=["1", "3", "5", "7"],
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
        dx = int(params.get("dx", 0))
        dy = int(params.get("dy", 1))
        if dx == 0 and dy == 0:
            dx = 1
        ksize = int(params.get("ksize", 3))
        scale = float(params.get("scale", 1.0))
        invert = bool(params.get("invert", False))

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        sobel = cv2.Sobel(gray, cv2.CV_64F, dx, dy, ksize=ksize, scale=scale)
        sobel = np.uint8(np.absolute(sobel))
        if invert:
            sobel = 255 - sobel
        return cv2.cvtColor(sobel, cv2.COLOR_GRAY2RGB)
