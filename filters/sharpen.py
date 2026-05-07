import cv2
import numpy as np
from core.filter_base import FilterBase, ParamDef


class Sharpen(FilterBase):
    """Sharpen the image using a weighted Laplacian kernel."""

    name = "Sharpen"
    category = "Filter"

    def get_parameters(self) -> list[ParamDef]:
        return [
            ParamDef(
                name="strength",
                label="Strength",
                param_type="slider",
                default=1.0,
                min_val=0.01,
                max_val=5.0,
                step=0.01,
            ),
        ]

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        s = float(params.get("strength", 1.0))
        kernel = np.array([
            [0, -s, 0],
            [-s, 1 + 4 * s, -s],
            [0, -s, 0],
        ], dtype=np.float32)
        return cv2.filter2D(image, -1, kernel)
