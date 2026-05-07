from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QColorDialog, QComboBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from app.image_viewer import Tool, BrushTip
from core.i18n import tr, Translator

_TOOL_LIST = [Tool.BRUSH, Tool.ERASER, Tool.PICKER, Tool.RULER]


class FloatingToolbar(QWidget):
    tool_selected = pyqtSignal(Tool)
    brush_color_changed = pyqtSignal(int, int, int)
    brush_tip_changed = pyqtSignal(BrushTip)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._brush_color_rgb = (255, 0, 0)
        self._active_tool = Tool.NONE

        self.setFixedHeight(36)
        self.setStyleSheet(
            "FloatingToolbar { background: rgba(50, 50, 50, 220); border-radius: 6px; }"
            " QPushButton { background: rgba(80, 80, 80, 200); color: #ccc; border: none; "
            "border-radius: 4px; padding: 2px 6px; min-width: 24px; font-size: 11px; }"
            " QPushButton:checked { background: #4a90d9; color: #fff; }"
            " QPushButton:hover { background: rgba(120, 120, 120, 200); }"
            " QComboBox { background: rgba(80,80,80,200); color: #ccc; border: none; "
            "border-radius: 3px; padding: 1px 3px; font-size: 11px; max-width: 60px; }"
            " QComboBox:hover { background: rgba(120,120,120,200); }"
            " QComboBox QAbstractItemView { background: #444; color: #ccc; selection-background-color: #4a90d9; }"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(3)

        # Color swatch
        self._color_swatch = QLabel()
        self._color_swatch.setFixedSize(22, 22)
        self._color_swatch.setCursor(Qt.PointingHandCursor)
        self._color_swatch.setStyleSheet(
            "background: rgb(255,0,0); border: 1px solid #888; border-radius: 3px;"
        )
        self._color_swatch.mousePressEvent = lambda e: self._pick_color()
        layout.addWidget(self._color_swatch)

        # Brush button
        self._btn_brush = QPushButton(tr("Brush"))
        self._btn_brush.setCheckable(True)
        self._btn_brush.clicked.connect(lambda: self._select(Tool.BRUSH))

        # Brush tip combo
        self._tip_combo = QComboBox()
        self._tip_combo.addItem(tr("Pixel"), BrushTip.PIXEL)
        self._tip_combo.addItem(tr("Cross"), BrushTip.CROSS)
        self._tip_combo.currentIndexChanged.connect(self._on_tip_changed)

        # Eraser button
        self._btn_eraser = QPushButton(tr("Eraser"))
        self._btn_eraser.setCheckable(True)
        self._btn_eraser.clicked.connect(lambda: self._select(Tool.ERASER))

        # Picker button
        self._btn_picker = QPushButton(tr("Picker"))
        self._btn_picker.setCheckable(True)
        self._btn_picker.clicked.connect(lambda: self._select(Tool.PICKER))

        # Ruler button
        self._btn_ruler = QPushButton(tr("Ruler"))
        self._btn_ruler.setCheckable(True)
        self._btn_ruler.clicked.connect(lambda: self._select(Tool.RULER))

        self._buttons = [self._btn_brush, self._btn_eraser, self._btn_picker, self._btn_ruler]

        layout.addWidget(self._btn_brush)
        layout.addWidget(self._tip_combo)
        layout.addWidget(self._btn_eraser)
        layout.addWidget(self._btn_picker)
        layout.addWidget(self._btn_ruler)

        Translator.instance().locale_changed.connect(self.retranslate_ui)

    def _select(self, tool: Tool):
        if self._active_tool == tool:
            # Toggle off: return to NONE
            for btn in self._buttons:
                btn.setChecked(False)
            self._active_tool = Tool.NONE
            self.tool_selected.emit(Tool.NONE)
            return

        self._active_tool = tool
        for btn in self._buttons:
            btn.setChecked(False)
        idx = _TOOL_LIST.index(tool)
        self._buttons[idx].setChecked(True)
        self.tool_selected.emit(tool)

    def _on_tip_changed(self, _index):
        tip = self._tip_combo.currentData()
        if tip is not None:
            self.brush_tip_changed.emit(tip)

    def set_color(self, r: int, g: int, b: int):
        self._brush_color_rgb = (r, g, b)
        self._color_swatch.setStyleSheet(
            f"background: rgb({r},{g},{b}); border: 1px solid #888; border-radius: 3px;"
        )
        self.brush_color_changed.emit(r, g, b)

    def _pick_color(self):
        qc = QColor(*self._brush_color_rgb)
        color = QColorDialog.getColor(qc, self, "Select Brush Color")
        if color.isValid():
            r, g, b = color.red(), color.green(), color.blue()
            self.set_color(r, g, b)
            self.brush_color_changed.emit(r, g, b)

    def retranslate_ui(self):
        self._btn_brush.setText(tr("Brush"))
        self._btn_eraser.setText(tr("Eraser"))
        self._btn_picker.setText(tr("Picker"))
        self._btn_ruler.setText(tr("Ruler"))
        self._tip_combo.setItemText(0, tr("Pixel"))
        self._tip_combo.setItemText(1, tr("Cross"))
