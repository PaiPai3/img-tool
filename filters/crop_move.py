import json
import numpy as np
from core.filter_base import FilterBase, ParamDef


class CropMove(FilterBase):
    """Select regions and move them. One stage can contain multiple clips."""

    name = "Crop Move"
    category = "Transform"
    interactive = True

    def get_parameters(self) -> list[ParamDef]:
        return [
            ParamDef(name="clips", label="Clips", param_type="text", default="[]"),
        ]

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        h, w = image.shape[:2]
        clips_str = params.get("clips", "[]")
        try:
            clips = json.loads(clips_str)
        except (json.JSONDecodeError, TypeError):
            clips = []

        result = image.copy()
        for clip in clips:
            if not clip.get("visible", True):
                continue
            x = max(0, min(int(clip.get("x", 0)), w - 1))
            y = max(0, min(int(clip.get("y", 0)), h - 1))
            cw = max(1, min(int(clip.get("w", 1)), w - x))
            ch = max(1, min(int(clip.get("h", 1)), h - y))
            dx = int(clip.get("dx", 0))
            dy = int(clip.get("dy", 0))

            src = result[y:y + ch, x:x + cw].copy()
            result[y:y + ch, x:x + cw] = 0

            # Visible source region (clipped by image bounds)
            sy1 = max(0, -(y + dy))
            sy2 = min(ch, h - (y + dy))
            sx1 = max(0, -(x + dx))
            sx2 = min(cw, w - (x + dx))

            # Visible destination region
            dy1 = max(0, y + dy)
            dy2 = min(h, y + ch + dy)
            dx1 = max(0, x + dx)
            dx2 = min(w, x + cw + dx)

            if sy2 > sy1 and sx2 > sx1:
                result[dy1:dy2, dx1:dx2] = src[sy1:sy2, sx1:sx2]
        return result
