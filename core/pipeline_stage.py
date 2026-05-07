from dataclasses import dataclass, field
from uuid import uuid4
import numpy as np


@dataclass
class PipelineStage:
    filter_instance: "FilterBase"
    params: dict = field(default_factory=dict)
    enabled: bool = True
    id: str = field(default_factory=lambda: uuid4().hex[:8])

    @property
    def name(self) -> str:
        return self.filter_instance.name if self.filter_instance else ""

    def apply(self, image: np.ndarray) -> np.ndarray:
        if not self.enabled or self.filter_instance is None:
            return image
        return self.filter_instance.apply(image, **self.params)
