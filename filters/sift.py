import cv2
import numpy as np
from core.filter_base import FilterBase, ParamDef
from utils.image_utils import draw_keypoints


class SIFT(FilterBase):
    """SIFT keypoint detection."""

    name = "SIFT"
    category = "Keypoint"

    def get_parameters(self) -> list[ParamDef]:
        return [
            ParamDef(
                name="nfeatures", label="N Features", param_type="int_spin",
                default=500, min_val=10, max_val=5000, step=10,
            ),
            ParamDef(
                name="edge_threshold", label="Edge Threshold", param_type="slider",
                default=10.0, min_val=1.0, max_val=50.0, step=1.0,
            ),
            ParamDef(
                name="contrast_threshold", label="Contrast Threshold", param_type="slider",
                default=0.04, min_val=0.01, max_val=0.2, step=0.01,
            ),
        ]

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        nfeatures = int(params.get("nfeatures", 500))
        edge_threshold = float(params.get("edge_threshold", 10.0))
        contrast_threshold = float(params.get("contrast_threshold", 0.04))

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        sift = cv2.SIFT_create(
            nfeatures=nfeatures,
            edgeThreshold=edge_threshold,
            contrastThreshold=contrast_threshold,
        )
        keypoints = sift.detect(gray, None)

        return draw_keypoints(image, keypoints, color=(0, 255, 0), size=3)
