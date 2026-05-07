import numpy as np
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from utils.image_utils import ndarray_to_qpixmap


class ImageViewer(QGraphicsView):
    pixel_hovered = pyqtSignal(int, int, int, int, int)  # x, y, r, g, b
    zoom_changed = pyqtSignal(int)   # zoom percentage

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self._pixmap_item = None
        self._image: np.ndarray = None
        self._grid_enabled = False
        self._grid_color = QColor(255, 255, 255, 80)

        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.setBackgroundBrush(Qt.darkGray)

    def set_image(self, img: np.ndarray):
        self._image = img
        pixmap = ndarray_to_qpixmap(img)
        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(self._pixmap_item.boundingRect())
        self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)
        self._emit_zoom()

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

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
        self._emit_zoom()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self._image is None:
            return
        scene_pos = self.mapToScene(event.pos())
        x, y = int(scene_pos.x()), int(scene_pos.y())
        h, w = self._image.shape[:2]
        if 0 <= x < w and 0 <= y < h:
            px = self._image[y, x]
            if len(px) >= 3:
                self.pixel_hovered.emit(x, y, int(px[0]), int(px[1]), int(px[2]))

    def clear_image(self):
        self._image = None
        self._scene.clear()
        self._pixmap_item = None

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
