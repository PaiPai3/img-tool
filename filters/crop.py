import json
import numpy as np
from core.filter_base import FilterBase, ParamDef


class Crop(FilterBase):
    """Crop the image, keeping only the selected rectangle."""

    name = "Crop"
    category = "Transform"
    interactive = True

    def get_parameters(self) -> list[ParamDef]:
        return [
            ParamDef(name="rect", label="Rect", param_type="text", default='{"x":0,"y":0,"w":100,"h":100}'),
        ]

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        h, w = image.shape[:2]
        rect_str = params.get("rect", '{"x":0,"y":0,"w":100,"h":100}')
        try:
            rect = json.loads(rect_str)
        except (json.JSONDecodeError, TypeError):
            rect = {"x": 0, "y": 0, "w": 100, "h": 100}

        x = max(0, min(int(rect.get("x", 0)), w - 1))
        y = max(0, min(int(rect.get("y", 0)), h - 1))
        cw = max(1, min(int(rect.get("w", 1)), w - x))
        ch = max(1, min(int(rect.get("h", 1)), h - y))
        return image[y:y + ch, x:x + cw].copy()
