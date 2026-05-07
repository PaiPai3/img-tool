import cv2
import numpy as np
from core.filter_base import FilterBase, ParamDef
from utils.image_utils import draw_keypoints


class ORB(FilterBase):
    """ORB keypoint detection."""

    name = "ORB"
    category = "Keypoint"

    def get_parameters(self) -> list[ParamDef]:
        return [
            ParamDef(
                name="nfeatures", label="N Features", param_type="int_spin",
                default=500, min_val=10, max_val=5000, step=10,
            ),
            ParamDef(
                name="scale_factor", label="Scale Factor", param_type="slider",
                default=1.2, min_val=1.1, max_val=2.0, step=0.1,
            ),
        ]

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        nfeatures = int(params.get("nfeatures", 500))
        scale_factor = float(params.get("scale_factor", 1.2))

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        orb = cv2.ORB_create(nfeatures=nfeatures, scaleFactor=scale_factor)
        keypoints = orb.detect(gray, None)

        return draw_keypoints(image, keypoints, color=(0, 255, 0), size=3)
