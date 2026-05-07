from PyQt5.QtWidgets import QStatusBar, QLabel
from core.i18n import tr, Translator


class ImageStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pos_label = QLabel(tr("Pos: {}").format("—, —"))
        self._rgb_label = QLabel(tr("RGB: {}").format("—, —, —"))
        self._lab_label = QLabel(tr("LAB: {}").format("—, —, —"))
        self._zoom_label = QLabel(tr("Zoom: {}").format("100%"))
        self._size_label = QLabel("")
        self._ruler_label = QLabel("")

        self._pos_label.setMinimumWidth(180)
        self._rgb_label.setMinimumWidth(200)
        self._lab_label.setMinimumWidth(200)
        self._zoom_label.setMinimumWidth(80)
        self._size_label.setMinimumWidth(150)
        self._ruler_label.setMinimumWidth(100)

        self.addPermanentWidget(self._pos_label)
        self.addPermanentWidget(self._rgb_label)
        self.addPermanentWidget(self._lab_label)
        self.addPermanentWidget(self._zoom_label)
        self.addPermanentWidget(self._size_label)
        self.addPermanentWidget(self._ruler_label)

        Translator.instance().locale_changed.connect(self.retranslate_ui)

    def set_pixel(self, x: int, y: int, r: int, g: int, b: int, L: int, A: int, B: int):
        self._pos_label.setText(tr("Pos: {}").format(f"{x}, {y}"))
        self._rgb_label.setText(tr("RGB: {}").format(f"{r}, {g}, {b}"))
        self._lab_label.setText(tr("LAB: {}").format(f"{L}, {A:+d}, {B:+d}"))

    def clear_pixel(self):
        self._pos_label.setText(tr("Pos: {}").format("—, —"))
        self._rgb_label.setText(tr("RGB: {}").format("—, —, —"))
        self._lab_label.setText(tr("LAB: {}").format("—, —, —"))

    def set_zoom(self, percent: int):
        self._zoom_label.setText(tr("Zoom: {}").format(f"{percent}%"))

    def set_image_size(self, w: int, h: int):
        self._size_label.setText(tr("Size: {}").format(f"{w} x {h}"))

    def set_ruler_distance(self, text: str):
        if text:
            self._ruler_label.setText(tr("Dist: {}").format(text))
        else:
            self._ruler_label.setText("")

    def retranslate_ui(self):
        self._pos_label.setText(tr("Pos: {}").format("—, —"))
        self._rgb_label.setText(tr("RGB: {}").format("—, —, —"))
        self._lab_label.setText(tr("LAB: {}").format("—, —, —"))
        self._zoom_label.setText(tr("Zoom: {}").format("100%"))
