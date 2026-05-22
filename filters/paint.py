import json
import numpy as np
from core.filter_base import FilterBase, ParamDef


class Paint(FilterBase):
    """Paint strokes on the image interactively."""

    name = "Paint"
    category = "Draw"
    interactive = True

    def get_parameters(self) -> list[ParamDef]:
        return [
            ParamDef(name="strokes", label="Strokes", param_type="text", default="[]"),
        ]

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        h, w = image.shape[:2]
        strokes_str = params.get("strokes", "[]")
        try:
            strokes = json.loads(strokes_str)
        except (json.JSONDecodeError, TypeError):
            strokes = []

        result = image.copy()
        for s in strokes:
            x, y = int(s.get("x", 0)), int(s.get("y", 0))
            if not (0 <= x < w and 0 <= y < h):
                continue

            if s.get("erase"):
                r, g, b = int(s.get("r", 0)), int(s.get("g", 0)), int(s.get("b", 0))
                # Eraser: restore single pixel
                result[y, x] = (r, g, b)
                continue

            r, g, b = int(s.get("r", 255)), int(s.get("g", 0)), int(s.get("b", 0))
            size = int(s.get("size", 3))
            tip = s.get("tip", "circle")

            if tip == "cross":
                sz = size
                x1, x2 = max(0, x - sz), min(w - 1, x + sz)
                y1, y2 = max(0, y - sz), min(h - 1, y + sz)
                result[y, x1:x2 + 1] = (r, g, b)
                result[y1:y2 + 1, x] = (r, g, b)
            elif tip == "square":
                half = size // 2
                x1, x2 = max(0, x - half), min(w, x + half + 1)
                y1, y2 = max(0, y - half), min(h, y + half + 1)
                result[y1:y2, x1:x2] = (r, g, b)
            else:  # circle
                rr = max(1, size // 2)
                y1, y2 = max(0, y - rr), min(h, y + rr + 1)
                x1, x2 = max(0, x - rr), min(w, x + rr + 1)
                for dy_ in range(y1, y2):
                    for dx_ in range(x1, x2):
                        if (dx_ - x) ** 2 + (dy_ - y) ** 2 <= rr ** 2:
                            result[dy_, dx_] = (r, g, b)
        return result
