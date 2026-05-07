import cv2
import numpy as np
from core.filter_base import FilterBase, ParamDef
from utils.image_utils import draw_keypoints


class Harris(FilterBase):
    """Harris corner detection."""

    name = "Harris"
    category = "Keypoint"

    def get_parameters(self) -> list[ParamDef]:
        return [
            ParamDef(
                name="block_size", label="Block Size", param_type="int_spin",
                default=2, min_val=2, max_val=10, step=1,
            ),
            ParamDef(
                name="ksize", label="Kernel Size", param_type="int_spin",
                default=3, min_val=1, max_val=31, step=2,
            ),
            ParamDef(
                name="k", label="K Value", param_type="slider",
                default=0.04, min_val=0.01, max_val=0.2, step=0.01,
            ),
            ParamDef(
                name="threshold", label="Threshold", param_type="slider",
                default=0.01, min_val=0.001, max_val=0.1, step=0.001,
            ),
        ]

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        block_size = int(params.get("block_size", 2))
        ksize = int(params.get("ksize", 3))
        if ksize % 2 == 0:
            ksize += 1
        k = float(params.get("k", 0.04))
        threshold = float(params.get("threshold", 0.01))

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        gray_f32 = np.float32(gray)
        harris = cv2.cornerHarris(gray_f32, block_size, ksize, k)
        harris = cv2.dilate(harris, None)
        ys, xs = np.where(harris > threshold * harris.max())
        keypoints = [cv2.KeyPoint(float(x), float(y), 1) for x, y in zip(xs, ys)]

        return draw_keypoints(image, keypoints, color=(0, 255, 0), size=3)
