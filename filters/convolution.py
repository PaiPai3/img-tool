import cv2
import numpy as np
from core.filter_base import FilterBase, ParamDef


class Convolution(FilterBase):
    """Apply custom convolution kernel to the image."""

    name = "Convolution"
    category = "Filter"

    def get_parameters(self) -> list[ParamDef]:
        return [
            ParamDef(
                name="kernel",
                label="Kernel Values",
                param_type="text",
                default="-1,-1,-1,-1,8,-1,-1,-1,-1",
            ),
        ]

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        kernel_str = str(params.get("kernel", ""))
        try:
            values = [float(v.strip()) for v in kernel_str.split(",") if v.strip()]
            n = int(len(values) ** 0.5)
            if n * n != len(values) or n < 1:
                return image
            kernel = np.array(values, dtype=np.float32).reshape(n, n)
            return cv2.filter2D(image, -1, kernel)
        except (ValueError, IndexError):
            return image
