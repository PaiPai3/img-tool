import cv2
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from utils.image_utils import imread_unicode
from core.filter_base import FilterBase
from core.pipeline_stage import PipelineStage
from core.filter_registry import FilterRegistry


class Pipeline(QObject):
    image_changed = pyqtSignal(np.ndarray)
    pipeline_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._original: np.ndarray = None
        self._current: np.ndarray = None
        self._pre_brush: np.ndarray = None
        self._stages: list[PipelineStage] = []
        self._undo_stack: list[np.ndarray] = []

    def load_image(self, path: str):
        img = imread_unicode(path)
        if img is None:
            raise ValueError(f"Cannot open image: {path}")
        self._original = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self._current = self._original
        self._process()

    def set_image(self, img: np.ndarray):
        self._original = img
        self._current = self._original
        self._process()

    def _process(self):
        if self._original is None:
            return
        img = self._original.copy()
        for stage in self._stages:
            img = stage.apply(img)
        self._pre_brush = img
        self._current = img.copy()
        self._undo_stack.clear()
        self.image_changed.emit(self._current)

    def process_image(self, img: np.ndarray) -> np.ndarray:
        result = img.copy()
        for stage in self._stages:
            result = stage.apply(result)
        return result

    # --- Stage management ---

    def add_stage(self, filter_cls: type[FilterBase], params: dict = None) -> str:
        instance = filter_cls()
        if params is None:
            params = {p.name: p.default for p in instance.get_parameters()}
        stage = PipelineStage(filter_instance=instance, params=params)
        self._stages.append(stage)
        self._process()
        self.pipeline_changed.emit()
        return stage.id

    def remove_stage(self, stage_id: str):
        self._stages = [s for s in self._stages if s.id != stage_id]
        self._process()
        self.pipeline_changed.emit()

    def move_stage(self, stage_id: str, direction: int):
        for i, s in enumerate(self._stages):
            if s.id == stage_id:
                target = i + direction
                if 0 <= target < len(self._stages):
                    self._stages.insert(target, self._stages.pop(i))
                    self._process()
                    self.pipeline_changed.emit()
                return

    def set_stage_enabled(self, stage_id: str, enabled: bool):
        for s in self._stages:
            if s.id == stage_id:
                s.enabled = enabled
                self._process()
                self.pipeline_changed.emit()
                return

    def set_stage_params(self, stage_id: str, params: dict):
        for s in self._stages:
            if s.id == stage_id:
                s.params = dict(params)
                self._process()
                return

    def clear_stages(self):
        self._stages.clear()
        self._process()
        self.pipeline_changed.emit()

    def reset(self):
        if self._original is not None:
            self._current = self._original
            self.image_changed.emit(self._current)

    # --- Serialization ---

    def to_config(self) -> list[dict]:
        return [
            {"name": s.filter_instance.name, "params": s.params, "enabled": s.enabled}
            for s in self._stages
        ]

    def load_config(self, config: list[dict]):
        self._stages.clear()
        for entry in config:
            filter_cls = FilterRegistry.get_filter(entry["name"])
            if filter_cls is None:
                continue
            instance = filter_cls()
            stage = PipelineStage(
                filter_instance=instance,
                params=entry.get("params", {}),
                enabled=entry.get("enabled", True),
            )
            self._stages.append(stage)
        self._process()
        self.pipeline_changed.emit()

    # --- Pixel editing ---

    def push_undo_snapshot(self):
        if self._current is not None:
            self._undo_stack.append(self._current.copy())
            if len(self._undo_stack) > 100:
                self._undo_stack.pop(0)

    def undo(self):
        if self._undo_stack:
            self._current = self._undo_stack.pop()
            self.image_changed.emit(self._current)

    def set_pixel(self, x: int, y: int, color: tuple):
        if self._current is None:
            return
        h, w = self._current.shape[:2]
        if 0 <= x < w and 0 <= y < h:
            self._current[y, x] = color
            self.image_changed.emit(self._current)

    def draw_crosshair(self, x: int, y: int, color: tuple, length: int = 5):
        if self._current is None:
            return
        h, w = self._current.shape[:2]
        x1, x2 = max(0, x - length), min(w - 1, x + length)
        y1, y2 = max(0, y - length), min(h - 1, y + length)
        self._current[y, x1:x2 + 1] = color
        self._current[y1:y2 + 1, x] = color
        self.image_changed.emit(self._current)

    # --- Properties ---

    @property
    def stages(self) -> list[PipelineStage]:
        return list(self._stages)

    @property
    def original(self) -> np.ndarray | None:
        return self._original

    @property
    def current(self) -> np.ndarray | None:
        return self._current

    @property
    def pre_brush(self) -> np.ndarray | None:
        return self._pre_brush
