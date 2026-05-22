import cv2
import numpy as np
from core.filter_base import FilterBase, ParamDef
from utils.image_utils import draw_keypoints


class FAST(FilterBase):
    """FAST corner detection."""

    name = "FAST"
    category = "Keypoint"

    def get_parameters(self) -> list[ParamDef]:
        return [
            ParamDef(
                name="threshold", label="Threshold", param_type="int_spin",
                default=25, min_val=1, max_val=100, step=1,
            ),
            ParamDef(
                name="nonmax_suppression", label="Non-max Suppression",
                param_type="checkbox", default=True,
            ),
            ParamDef(
                name="radius", label="Radius", param_type="int_spin",
                default=3, min_val=1, max_val=20, step=1,
            ),
        ]

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        threshold = int(params.get("threshold", 25))
        nonmax = bool(params.get("nonmax_suppression", True))
        radius = int(params.get("radius", 3))

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        fast = cv2.FastFeatureDetector_create(
            threshold=threshold, nonmaxSuppression=nonmax,
        )
        keypoints = fast.detect(gray, None)

        return draw_keypoints(image, keypoints, color=(0, 255, 0), size=radius)
