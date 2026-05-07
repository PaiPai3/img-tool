import numpy as np
from core.filter_base import FilterBase, ParamDef


class Contrast(FilterBase):
    """Adjust image contrast and brightness."""

    name = "Contrast"
    category = "Color"

    def get_parameters(self) -> list[ParamDef]:
        return [
            ParamDef(
                name="alpha",
                label="Contrast",
                param_type="slider",
                default=1.0,
                min_val=0.0,
                max_val=3.0,
                step=0.01,
            ),
            ParamDef(
                name="beta",
                label="Brightness",
                param_type="slider",
                default=0.0,
                min_val=-100.0,
                max_val=100.0,
                step=1.0,
            ),
        ]

    def apply(self, image: np.ndarray, **params) -> np.ndarray:
        alpha = float(params.get("alpha", 1.0))
        beta = float(params.get("beta", 0.0))
        return np.clip(
            alpha * image.astype(np.float32) + beta, 0, 255
        ).astype(np.uint8)
