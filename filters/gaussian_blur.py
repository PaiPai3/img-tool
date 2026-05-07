import cv2
import numpy as np
from core.filter_base import FilterBase, ParamDef


class GaussianBlur(FilterBase):
    """Apply Gaussian blur to smooth the image and reduce noise."""

    name = "Gaussian Blur"
    category = "Blur"

    def get_parameters(self) -> list[ParamDef]:
        return [
            ParamDef(
                name="kernel_size",
                label="Kernel Size",
                param_type="int_spin",
                default=5,
                min_val=1,
                max_val=31,
                step=2,
            ),
            ParamDef(
                name="sigma",
                label="Sigma",
                param_type="slider",
                default=1.0,
                min_val=0.1,
                max_val=10.0,
                step=0.1,
            ),
        ]

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        ksize = int(params.get("kernel_size", 5))
        if ksize % 2 == 0:
            ksize += 1
        sigma = float(params.get("sigma", 1.0))
        return cv2.GaussianBlur(image, (ksize, ksize), sigmaX=sigma)
