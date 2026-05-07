import cv2
import numpy as np
from core.filter_base import FilterBase, ParamDef


class CannyEdge(FilterBase):
    """Detect edges using the Canny algorithm with hysteresis thresholds."""

    name = "Canny Edge"
    category = "Edge Detection"

    def get_parameters(self) -> list[ParamDef]:
        return [
            ParamDef(
                name="threshold1",
                label="Low Threshold",
                param_type="slider",
                default=50,
                min_val=0,
                max_val=255,
                step=1,
            ),
            ParamDef(
                name="threshold2",
                label="High Threshold",
                param_type="slider",
                default=150,
                min_val=0,
                max_val=255,
                step=1,
            ),
            ParamDef(
                name="aperture",
                label="Aperture Size",
                param_type="dropdown",
                default="3",
                options=["3", "5", "7"],
            ),
            ParamDef(
                name="invert",
                label="Invert",
                param_type="checkbox",
                default=False,
            ),
        ]

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        t1 = float(params.get("threshold1", 50))
        t2 = float(params.get("threshold2", 150))
        aperture = int(params.get("aperture", 3))
        invert = bool(params.get("invert", False))

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, t1, t2, apertureSize=aperture)
        if invert:
            edges = 255 - edges
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
