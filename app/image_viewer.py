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
    CROSSHAIR = auto()
    PICKER = auto()
    RULER = auto()


class ImageViewer(QGraphicsView):
    pixel_hovered = pyqtSignal(int, int, int, int, int, int, int, int)  # x,y,r,g,b,L,A,B
    zoom_changed = pyqtSignal(int)
    color_picked = pyqtSignal(int, int, int)            # r, g, b
    ruler_distance = pyqtSignal(str)                     # distance text

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
        self._mouse_pressed = False
        self._ruler_start = None       # (x, y) or None
        self._ruler_current = None     # (x, y) or None
        self._ruler_items = []
        self._finished_ruler = None    # (start, end) — finalized ruler, cleared on new ruler start
        self._pipeline = None

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
        if tool == Tool.NONE:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        else:
            self.setDragMode(QGraphicsView.NoDrag)

    def set_brush_color(self, r: int, g: int, b: int):
        self._brush_color = (r, g, b)

    def set_pipeline(self, pipeline):
        self._pipeline = pipeline

    # --- Image display ---

    def set_image(self, img: np.ndarray):
        self._image = img
        self._refresh_pixmap()

    def _refresh_pixmap(self):
        if self._image is None:
            return
        pixmap = ndarray_to_qpixmap(self._image)
        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(self._pixmap_item.boundingRect())

    def _restore_ruler_after_refresh(self):
        """Re-draw ruler overlay after scene is cleared by set_image."""
        if self._ruler_start is not None and self._ruler_current is not None:
            self._redraw_ruler(self._ruler_start, self._ruler_current)

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
                self._pipeline.set_pixel(x, y, self._brush_color)

        elif self._tool == Tool.CROSSHAIR:
            if self._pipeline:
                self._pipeline.draw_crosshair(x, y, self._brush_color)

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
                # Second click: finalize
                self._finished_ruler = (self._ruler_start, self._ruler_current)
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

        if self._tool == Tool.NONE:
            super().mouseMoveEvent(event)
            return

        if xy is None:
            return
        x, y = xy

        if self._tool == Tool.BRUSH and self._mouse_pressed:
            if self._pipeline:
                self._pipeline.set_pixel(x, y, self._brush_color)

        elif self._tool == Tool.RULER and self._ruler_start is not None:
            self._ruler_current = (x, y)
            self._draw_ruler()
            sx, sy = self._ruler_start
            manhattan = abs(x - sx) + abs(y - sy)
            self.ruler_distance.emit(f"{manhattan} px")

    def mouseReleaseEvent(self, event):
        self._mouse_pressed = False
        if self._tool == Tool.NONE:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._clear_ruler()
            self.set_tool(Tool.NONE)
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
        self._finished_ruler = None
        self.ruler_distance.emit("")

    def _draw_ruler(self):
        self._redraw_ruler(self._ruler_start, self._ruler_current)

    def _redraw_ruler(self, start, end):
        for item in self._ruler_items:
            self._scene.removeItem(item)
        self._ruler_items.clear()

        sx, sy = start
        ex, ey = end

        # Manhattan path: horizontal first, then vertical
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

        # Start marker: green
        start_pen = QPen(QColor(0, 255, 0, 200), 0)
        start_brush = QBrush(QColor(0, 255, 0, 200))
        sr = self._scene.addRect(sx, sy, 1, 1, start_pen, start_brush)
        self._ruler_items.append(sr)

        # End marker: red
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
