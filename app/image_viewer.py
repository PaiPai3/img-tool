import json
from enum import Enum, auto
import cv2
import numpy as np
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QBrush
from utils.image_utils import ndarray_to_qpixmap


class Tool(Enum):
    NONE = auto()
    BRUSH = auto()
    PICKER = auto()
    ERASER = auto()
    RULER = auto()


class BrushTip(Enum):
    PIXEL = auto()
    CROSS = auto()


class ImageViewer(QGraphicsView):
    pixel_hovered = pyqtSignal(int, int, int, int, int, int, int, int)
    zoom_changed = pyqtSignal(int)
    color_picked = pyqtSignal(int, int, int)
    ruler_distance = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self._pixmap_item = None
        self._image: np.ndarray = None
        self._grid_enabled = False
        self._grid_color = QColor(255, 255, 255, 80)

        # Tool state
        self._tool = Tool.NONE
        self._brush_color = (255, 0, 0)
        self._brush_tip = BrushTip.PIXEL
        self._mouse_pressed = False
        self._ruler_start = None
        self._ruler_current = None
        self._ruler_items = []
        self._pipeline = None

        # Stage edit state (for interactive filters like CropMove)
        self._edit_stage_id: str | None = None
        self._edit_clip_index: int = -1
        self._select_clip_index: int = -1   # clicked-on-overlay selection
        self._edit_phase = ""           # "rect" or "move" (only when editing)
        self._edit_rect_start = None
        self._edit_x1 = self._edit_y1 = self._edit_x2 = self._edit_y2 = 0
        self._edit_dx = self._edit_dy = 0
        self._edit_drag_start = None
        self._edit_drag_dx0 = self._edit_drag_dy0 = 0
        self._overlay_items = []
        self._paint_color = (255, 0, 0)
        self._paint_tip = "circle"
        self._paint_size = 3
        self._paint_mode = "brush"  # "brush", "eraser", "picker"

        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.setBackgroundBrush(Qt.darkGray)

    # --- Tool management ---

    def set_tool(self, tool: Tool):
        prev = self._tool
        self._tool = tool
        if prev == Tool.RULER and tool != Tool.RULER:
            self._clear_ruler()
        if tool != Tool.NONE:
            self._end_stage_edit()
            self.setDragMode(QGraphicsView.NoDrag)
        else:
            self._end_stage_edit()
            self.setDragMode(QGraphicsView.ScrollHandDrag)

    def set_brush_color(self, r: int, g: int, b: int):
        self._brush_color = (r, g, b)

    def set_brush_tip(self, tip: BrushTip):
        self._brush_tip = tip

    def set_pipeline(self, pipeline):
        self._pipeline = pipeline

    # --- Stage edit ---

    def start_stage_edit(self, stage_id: str, clip_index: int = -1):
        if self._pipeline is None or self._image is None:
            return
        stage = next((s for s in self._pipeline.stages if s.id == stage_id), None)
        if stage is None:
            return
        self._end_stage_edit()
        self._edit_stage_id = stage_id
        self._tool = Tool.NONE

        clips_str = stage.params.get("clips", "[]")
        try:
            clips = json.loads(clips_str)
        except (json.JSONDecodeError, TypeError):
            clips = []

        is_paint = stage.filter_instance.name == "Paint"
        is_crop = stage.filter_instance.name == "Crop"
        is_cropmove = stage.filter_instance.name == "Crop Move"

        # Determine if this is a select-only or edit call
        if clip_index >= 0:
            self._edit_clip_index = clip_index
            self._select_clip_index = clip_index
            self.setDragMode(QGraphicsView.NoDrag)

            if is_paint:
                self._edit_phase = "paint"
                self._read_paint_config(stage)
                self._draw_clips_overlay([], -1, -1)  # clear overlay
            elif is_crop:
                # Crop: rect-only editing
                rect_str = stage.params.get("rect", '{"x":0,"y":0,"w":100,"h":100}')
                try:
                    rect = json.loads(rect_str)
                except (json.JSONDecodeError, TypeError):
                    rect = {"x": 0, "y": 0, "w": 100, "h": 100}
                h_img, w_img = self._image.shape[:2]
                self._edit_x1 = max(0, min(int(rect.get("x", 0)), w_img - 1))
                self._edit_y1 = max(0, min(int(rect.get("y", 0)), h_img - 1))
                self._edit_x2 = self._edit_x1 + max(1, int(rect.get("w", 1)))
                self._edit_y2 = self._edit_y1 + max(1, int(rect.get("h", 1)))
                self._edit_dx = self._edit_dy = 0
                self._edit_phase = "rect"
            else:
                cw = ch = 0
                if clip_index < len(clips):
                    clip = clips[clip_index]
                    cw, ch = int(clip.get("w", 0)), int(clip.get("h", 0))
                    h_img, w_img = self._image.shape[:2]
                    self._edit_x1 = max(0, min(int(clip.get("x", 0)), w_img - 1))
                    self._edit_y1 = max(0, min(int(clip.get("y", 0)), h_img - 1))
                    self._edit_x2 = self._edit_x1 + max(1, cw)
                    self._edit_y2 = self._edit_y1 + max(1, ch)
                    self._edit_dx = int(clip.get("dx", 0))
                    self._edit_dy = int(clip.get("dy", 0))
                else:
                    self._edit_x1 = self._edit_y1 = self._edit_x2 = self._edit_y2 = 0
                    self._edit_dx = self._edit_dy = 0

                self._edit_phase = "rect" if (cw <= 0 or ch <= 0) else "move"
        else:
            self._edit_clip_index = -1
            self._edit_phase = ""
            self.setDragMode(QGraphicsView.ScrollHandDrag)

        if is_crop:
            self._draw_crop_overlay()
        else:
            self._draw_clips_overlay(clips, self._edit_clip_index, self._select_clip_index)

    def _end_stage_edit(self):
        self._edit_stage_id = None
        self._edit_clip_index = -1
        self._select_clip_index = -1
        self._edit_phase = ""
        self._edit_rect_start = None
        self._clear_overlay_items()

    def _clear_overlay_items(self):
        for item in self._overlay_items:
            self._scene.removeItem(item)
        self._overlay_items.clear()

    def _get_clips(self):
        if self._edit_stage_id is None or self._pipeline is None:
            return []
        stage = next((s for s in self._pipeline.stages if s.id == self._edit_stage_id), None)
        if stage is None:
            return []
        try:
            return json.loads(stage.params.get("clips", "[]"))
        except (json.JSONDecodeError, TypeError):
            return []

    def _draw_crop_overlay(self, preview=None):
        self._clear_overlay_items()
        color = QColor(0, 255, 0, 60)
        bp = QPen(QColor(0, 255, 0, 200), 0)

        if preview is not None:
            px, py, pw, ph = preview
            r = self._scene.addRect(px, py, pw, ph, bp, QBrush(color))
            self._overlay_items.append(r)
        elif hasattr(self, '_edit_x1'):
            r = self._scene.addRect(self._edit_x1, self._edit_y1,
                                    self._edit_x2 - self._edit_x1,
                                    self._edit_y2 - self._edit_y1, bp, QBrush(color))
            self._overlay_items.append(r)

    def _read_paint_config(self, stage):
        try:
            cfg = json.loads(stage.params.get("paint_config", "{}"))
        except (json.JSONDecodeError, TypeError):
            cfg = {}
        self._paint_color = tuple(cfg.get("color", [255, 0, 0]))
        self._paint_tip = cfg.get("tip", "circle")
        self._paint_size = cfg.get("size", 3)
        self._paint_mode = cfg.get("mode", "brush")

    def _save_paint_stroke(self, x, y):
        if self._paint_mode == "picker":
            if self._image is not None:
                px = self._image[y, x]
                r, g, b = int(px[0]), int(px[1]), int(px[2])
                self._paint_color = (r, g, b)
            cfg = {"color": list(self._paint_color), "tip": self._paint_tip,
                   "size": self._paint_size, "mode": "brush"}
            self._pipeline.set_stage_params(self._edit_stage_id, {"paint_config": json.dumps(cfg)})
            return
        stage = next((s for s in self._pipeline.stages if s.id == self._edit_stage_id), None)
        if stage is None:
            return
        try:
            strokes = json.loads(stage.params.get("strokes", "[]"))
        except (json.JSONDecodeError, TypeError):
            strokes = []
        if self._paint_mode == "eraser":
            # Store pre_brush color at this pixel
            if self._pipeline.pre_brush is not None:
                pb = self._pipeline.pre_brush[y, x]
                strokes.append({"x": x, "y": y, "erase": True,
                               "r": int(pb[0]), "g": int(pb[1]), "b": int(pb[2])})
        else:
            strokes.append({"x": x, "y": y,
                           "r": self._paint_color[0], "g": self._paint_color[1], "b": self._paint_color[2],
                           "tip": self._paint_tip, "size": self._paint_size})
        self._pipeline.set_stage_params(self._edit_stage_id, {"strokes": json.dumps(strokes)})

    def _save_clip_params(self):
        if self._edit_stage_id is None or self._pipeline is None:
            return
        stage = next((s for s in self._pipeline.stages if s.id == self._edit_stage_id), None)
        if stage is None:
            return
        is_crop = stage.filter_instance.name == "Crop"
        if is_crop:
            rect = {"x": self._edit_x1, "y": self._edit_y1,
                    "w": self._edit_x2 - self._edit_x1, "h": self._edit_y2 - self._edit_y1}
            self._pipeline.set_stage_params(self._edit_stage_id, {"rect": json.dumps(rect)})
            return
        if self._edit_clip_index < 0:
            return
        clips = self._get_clips()
        if self._edit_clip_index < len(clips):
            old = clips[self._edit_clip_index]
            clips[self._edit_clip_index] = {
                "x": self._edit_x1, "y": self._edit_y1,
                "w": self._edit_x2 - self._edit_x1, "h": self._edit_y2 - self._edit_y1,
                "dx": self._edit_dx, "dy": self._edit_dy,
                "visible": old.get("visible", True),
            }
            self._pipeline.set_stage_params(self._edit_stage_id, {"clips": json.dumps(clips)})
            self._draw_clips_overlay(clips, self._edit_clip_index, self._select_clip_index)

    def _draw_clips_overlay(self, clips, edit_index=-1, select_index=-1, preview=None):
        self._clear_overlay_items()

        # Opacity levels
        src_dim = QColor(255, 0, 0, 20)
        dst_dim = QColor(0, 255, 0, 20)
        src_norm = QColor(255, 0, 0, 50)
        dst_norm = QColor(0, 255, 0, 50)
        src_active = QColor(255, 0, 0, 90)
        dst_active = QColor(0, 255, 0, 90)
        bp_dim = QPen(QColor(0, 255, 0, 60), 0)
        bp_norm = QPen(QColor(0, 255, 0, 130), 0)
        bp_active = QPen(QColor(0, 255, 0, 255), 0)

        has_selection = (select_index >= 0 or edit_index >= 0)

        for i, clip in enumerate(clips):
            if not clip.get("visible", True):
                continue
            x, y = int(clip.get("x", 0)), int(clip.get("y", 0))
            cw, ch = int(clip.get("w", 0)), int(clip.get("h", 0))
            dx, dy = int(clip.get("dx", 0)), int(clip.get("dy", 0))
            if cw <= 0 or ch <= 0:
                continue

            editing = (i == edit_index)
            selected = editing or (i == select_index)
            if editing:
                sc, dc, bp = src_active, dst_active, bp_active
            elif selected or not has_selection:
                sc, dc, bp = src_norm, dst_norm, bp_norm
            else:
                sc, dc, bp = src_dim, dst_dim, bp_dim

            r = self._scene.addRect(x, y, cw, ch, bp, QBrush(sc))
            self._overlay_items.append(r)

            r2 = self._scene.addRect(x + dx, y + dy, cw, ch, bp, QBrush(dc))
            self._overlay_items.append(r2)

        if preview is not None:
            px, py, pw, ph, pdx, pdy = preview
            if pw > 0 and ph > 0:
                r = self._scene.addRect(px, py, pw, ph, bp_active, QBrush(src_active))
                self._overlay_items.append(r)
                r2 = self._scene.addRect(px + pdx, py + pdy, pw, ph, bp_active, QBrush(dst_active))
                self._overlay_items.append(r2)

    # --- Image display ---

    def set_image(self, img: np.ndarray):
        self._image = img
        self._refresh_pixmap()

    def _refresh_pixmap(self):
        if self._image is None:
            return
        pixmap = ndarray_to_qpixmap(self._image)
        self._scene.clear()
        self._overlay_items.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(self._pixmap_item.boundingRect())
        if self._edit_stage_id is not None:
            stage = next((s for s in self._pipeline.stages if s.id == self._edit_stage_id), None) if self._pipeline else None
            if stage:
                name = stage.filter_instance.name
                if name == "Paint":
                    self._read_paint_config(stage)
                elif name == "Crop":
                    self._draw_crop_overlay()
                elif name == "Crop Move":
                    clips = self._get_clips()
                    self._draw_clips_overlay(clips, self._edit_clip_index, self._select_clip_index)

    def set_grid_enabled(self, enabled: bool):
        self._grid_enabled = enabled
        self.viewport().update()

    def set_grid_color(self, color: QColor):
        self._grid_color = color
        if self._grid_enabled:
            self.viewport().update()

    def drawForeground(self, painter: QPainter, rect):
        super().drawForeground(painter, rect)
        if not self._grid_enabled or self._image is None:
            return

        scale = self.transform().m11()
        interval = max(1, round(1.0 / max(scale, 0.01)))

        h, w = self._image.shape[:2]
        view_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        start_x = max(0, int(view_rect.left()) // interval * interval)
        start_y = max(0, int(view_rect.top()) // interval * interval)
        end_x = min(w, int(view_rect.right()) + interval)
        end_y = min(h, int(view_rect.bottom()) + interval)

        pen = QPen(self._grid_color, 0)
        painter.setPen(pen)

        for x in range(start_x, end_x + 1, interval):
            painter.drawLine(x, start_y, x, end_y)
        for y in range(start_y, end_y + 1, interval):
            painter.drawLine(start_x, y, end_x, y)

    # --- Mouse events ---

    def _scene_xy(self, event) -> tuple[int, int] | None:
        if self._image is None:
            return None
        sp = self.mapToScene(event.pos())
        x, y = int(sp.x()), int(sp.y())
        h, w = self._image.shape[:2]
        if 0 <= x < w and 0 <= y < h:
            return x, y
        return None

    def mousePressEvent(self, event):
        # Stage edit mode when no tool active
        if self._tool == Tool.NONE and self._edit_stage_id is not None:
            xy = self._scene_xy(event)
            if xy is None:
                return
            x, y = xy

            if self._edit_phase == "paint":
                self._mouse_pressed = True
                self._save_paint_stroke(x, y)
                return

            if self._edit_phase == "rect":
                self._edit_rect_start = (x, y)
                self._edit_x1, self._edit_y1 = x, y
                self._edit_x2, self._edit_y2 = x + 1, y + 1
                self._edit_dx = self._edit_dy = 0
                return

            if self._edit_phase == "move":
                rx1, ry1 = self._edit_x1, self._edit_y1
                rw = self._edit_x2 - self._edit_x1
                rh = self._edit_y2 - self._edit_y1
                # Source rect
                in_src = (rx1 <= x < rx1 + rw and ry1 <= y < ry1 + rh)
                # Destination rect
                dst_x1 = rx1 + self._edit_dx
                dst_y1 = ry1 + self._edit_dy
                in_dst = (dst_x1 <= x < dst_x1 + rw and dst_y1 <= y < dst_y1 + rh)
                if in_src or in_dst:
                    self._edit_drag_start = (x, y)
                    self._edit_drag_dx0 = self._edit_dx
                    self._edit_drag_dy0 = self._edit_dy
                return

            # Not editing any clip: click overlay to select, blank to deselect
            clips = self._get_clips()
            found = -1
            for i, clip in enumerate(clips):
                if not clip.get("visible", True):
                    continue
                cx, cy = int(clip.get("x", 0)), int(clip.get("y", 0))
                cw2, ch2 = int(clip.get("w", 0)), int(clip.get("h", 0))
                if cw2 <= 0 or ch2 <= 0:
                    continue
                if (cx <= x < cx + cw2 and cy <= y < cy + ch2) or \
                   (cx + int(clip.get("dx", 0)) <= x < cx + int(clip.get("dx", 0)) + cw2 and \
                    cy + int(clip.get("dy", 0)) <= y < cy + int(clip.get("dy", 0)) + ch2):
                    found = i
                    break
            self._select_clip_index = found
            self._draw_clips_overlay(clips, self._edit_clip_index, self._select_clip_index)
            return

        if self._tool == Tool.NONE:
            super().mousePressEvent(event)
            return

        xy = self._scene_xy(event)
        if xy is None:
            return
        x, y = xy

        if self._tool == Tool.BRUSH:
            self._mouse_pressed = True
            if self._pipeline:
                self._pipeline.push_undo_snapshot()
                if self._brush_tip == BrushTip.CROSS:
                    self._pipeline.draw_crosshair(x, y, self._brush_color)
                else:
                    self._pipeline.set_pixel(x, y, self._brush_color)

        elif self._tool == Tool.ERASER:
            self._mouse_pressed = True
            if self._pipeline and self._pipeline.pre_brush is not None:
                self._pipeline.push_undo_snapshot()
                pb = self._pipeline.pre_brush[y, x]
                self._pipeline.set_pixel(x, y, tuple(int(c) for c in pb))

        elif self._tool == Tool.PICKER:
            if self._image is not None:
                px = self._image[y, x]
                r, g, b = int(px[0]), int(px[1]), int(px[2])
                self.color_picked.emit(r, g, b)

        elif self._tool == Tool.RULER:
            if self._ruler_start is None:
                self._clear_ruler()
                self._ruler_start = (x, y)
                self._ruler_current = (x, y)
                self._draw_ruler()
            else:
                self._ruler_start = None
                self._ruler_current = None

    def mouseMoveEvent(self, event):
        # Always emit pixel hover (with LAB)
        xy = self._scene_xy(event)
        if xy is not None and self._image is not None:
            x, y = xy
            px = self._image[y, x]
            if len(px) >= 3:
                r, g, b = int(px[0]), int(px[1]), int(px[2])
                pixel_bgr = np.uint8([[[b, g, r]]])
                L, A, Bv = cv2.cvtColor(pixel_bgr, cv2.COLOR_BGR2Lab)[0, 0]
                a_signed = int(A) - 128
                b_signed = int(Bv) - 128
                self.pixel_hovered.emit(x, y, r, g, b, int(L), a_signed, b_signed)

        # Stage edit: rect drawing
        if self._tool == Tool.NONE and self._edit_phase == "rect" and self._edit_rect_start is not None:
            if xy is not None:
                x, y = xy
                sx, sy = self._edit_rect_start
                self._edit_x1 = min(sx, x)
                self._edit_y1 = min(sy, y)
                self._edit_x2 = max(sx, x) + 1
                self._edit_y2 = max(sy, y) + 1
                # Check if this is a Crop stage
                stage = next((s for s in self._pipeline.stages if s.id == self._edit_stage_id), None) if self._pipeline else None
                if stage and stage.filter_instance.name == "Crop":
                    self._draw_crop_overlay((self._edit_x1, self._edit_y1,
                                             self._edit_x2 - self._edit_x1, self._edit_y2 - self._edit_y1))
                else:
                    clips = self._get_clips()
                    preview = (self._edit_x1, self._edit_y1,
                              self._edit_x2 - self._edit_x1, self._edit_y2 - self._edit_y1,
                              self._edit_dx, self._edit_dy)
                    self._draw_clips_overlay(clips, self._edit_clip_index, self._select_clip_index, preview)
            return

        # Stage edit: move dragging
        if (self._tool == Tool.NONE and self._edit_phase == "move"
                and self._edit_drag_start is not None and xy is not None):
            x, y = xy
            sx, sy = self._edit_drag_start
            self._edit_dx = self._edit_drag_dx0 + (x - sx)
            self._edit_dy = self._edit_drag_dy0 + (y - sy)
            clips = self._get_clips()
            preview = (self._edit_x1, self._edit_y1,
                      self._edit_x2 - self._edit_x1, self._edit_y2 - self._edit_y1,
                      self._edit_dx, self._edit_dy)
            self._draw_clips_overlay(clips, self._edit_clip_index, self._select_clip_index, preview)
            return

        # Stage edit paint: drag
        if self._tool == Tool.NONE and self._edit_phase == "paint" and self._mouse_pressed:
            if xy is not None:
                self._save_paint_stroke(xy[0], xy[1])
            return

        if self._tool == Tool.NONE:
            super().mouseMoveEvent(event)
            return

        if xy is None:
            return
        x, y = xy

        if self._tool == Tool.BRUSH and self._mouse_pressed:
            if self._pipeline:
                self._pipeline.set_pixel(x, y, self._brush_color)

        elif self._tool == Tool.ERASER and self._mouse_pressed:
            if self._pipeline and self._pipeline.pre_brush is not None:
                pb = self._pipeline.pre_brush[y, x]
                self._pipeline.set_pixel(x, y, tuple(int(c) for c in pb))

        elif self._tool == Tool.RULER and self._ruler_start is not None:
            self._ruler_current = (x, y)
            self._draw_ruler()
            sx, sy = self._ruler_start
            dx = abs(x - sx)
            dy = abs(y - sy)
            total = dx + dy
            self.ruler_distance.emit(f"{total} px  (X:{dx}  Y:{dy})")

    def mouseReleaseEvent(self, event):
        # Stage edit: finish rect
        if self._tool == Tool.NONE and self._edit_phase == "rect" and self._edit_rect_start is not None:
            self._edit_rect_start = None
            self._save_clip_params()
            # Check if Crop (rect-only) → exit edit mode back to select-only
            if self._pipeline:
                stage = next((s for s in self._pipeline.stages if s.id == self._edit_stage_id), None)
                if stage and stage.filter_instance.name == "Crop":
                    self._edit_clip_index = -1
                    self._edit_phase = ""
                    self.setDragMode(QGraphicsView.ScrollHandDrag)
                    self._draw_crop_overlay()
            else:
                self._edit_phase = "move"
            return

        # Stage edit: finish move drag
        if self._tool == Tool.NONE and self._edit_drag_start is not None:
            self._edit_drag_start = None
            self._save_clip_params()
            return

        self._mouse_pressed = False
        if self._tool == Tool.NONE:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self._edit_stage_id is not None:
                self._save_clip_params()
                self._end_stage_edit()
                self.setDragMode(QGraphicsView.ScrollHandDrag)
                return
            self._clear_ruler()
            self.set_tool(Tool.NONE)
        elif event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier:
            if self._pipeline:
                self._pipeline.undo()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
        self._emit_zoom()

    # --- Ruler overlay ---

    def _clear_ruler(self):
        for item in self._ruler_items:
            self._scene.removeItem(item)
        self._ruler_items.clear()
        self._ruler_start = None
        self._ruler_current = None
        self.ruler_distance.emit("")

    def _draw_ruler(self):
        self._redraw_ruler(self._ruler_start, self._ruler_current)

    def _redraw_ruler(self, start, end):
        for item in self._ruler_items:
            self._scene.removeItem(item)
        self._ruler_items.clear()

        sx, sy = start
        ex, ey = end

        path_pixels = []
        dx = 1 if ex >= sx else -1
        for x in range(sx, ex + dx, dx):
            path_pixels.append((x, sy))
        dy = 1 if ey >= sy else -1
        y_start = sy + dy if dy > 0 else sy + dy
        for y in range(y_start, ey + dy, dy):
            path_pixels.append((ex, y))

        overlay = QColor(255, 255, 0, 80)
        brush = QBrush(overlay)
        pen = QPen(Qt.NoPen)

        for px, py in path_pixels:
            rect = self._scene.addRect(px, py, 1, 1, pen, brush)
            self._ruler_items.append(rect)

        start_pen = QPen(QColor(0, 255, 0, 200), 0)
        start_brush = QBrush(QColor(0, 255, 0, 200))
        sr = self._scene.addRect(sx, sy, 1, 1, start_pen, start_brush)
        self._ruler_items.append(sr)

        end_pen = QPen(QColor(255, 0, 0, 200), 0)
        end_brush = QBrush(QColor(255, 0, 0, 200))
        er = self._scene.addRect(ex, ey, 1, 1, end_pen, end_brush)
        self._ruler_items.append(er)

    # --- Other methods ---

    def clear_image(self):
        self._image = None
        self._scene.clear()
        self._pixmap_item = None
        self._ruler_items.clear()
        self._overlay_items.clear()

    def fit_to_window(self):
        if self._pixmap_item:
            self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)
            self._emit_zoom()

    def reset_zoom(self):
        self.fit_to_window()

    def _emit_zoom(self):
        t = self.transform()
        pct = int(t.m11() * 100)
        self.zoom_changed.emit(pct)

    @property
    def image(self) -> np.ndarray | None:
        return self._image
