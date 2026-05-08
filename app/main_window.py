import os
import numpy as np
import cv2
from PyQt5.QtWidgets import (
    QMainWindow, QDockWidget, QFileDialog, QMessageBox, QAction,
    QActionGroup, QMenu, QProgressDialog, QApplication,
)
from PyQt5.QtCore import Qt
from app.file_browser import FileBrowser
from app.image_viewer import ImageViewer
from app.pipeline_panel import PipelinePanel
from app.status_bar import ImageStatusBar
from app.toolbar import FloatingToolbar
from core.pipeline import Pipeline
from core.cache_manager import CacheManager
from core.i18n import tr, Translator
from utils.image_utils import imread_unicode

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp", ".gif", ".ico")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("Image Tool"))
        self.resize(1400, 900)

        self._pipeline = Pipeline()

        # -- Central widget --
        self._viewer = ImageViewer()
        self.setCentralWidget(self._viewer)

        # -- Left dock: File Browser --
        self._file_browser = FileBrowser()
        self._left_dock = QDockWidget(tr("Files"), self)
        self._left_dock.setWidget(self._file_browser)
        self._left_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._left_dock)

        # -- Right dock: Pipeline Panel --
        self._pipeline_panel = PipelinePanel(self._pipeline)
        self._right_dock = QDockWidget(tr("Tools"), self)
        self._right_dock.setWidget(self._pipeline_panel)
        self._right_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.RightDockWidgetArea, self._right_dock)

        # -- Status bar --
        self._status_bar = ImageStatusBar()
        self.setStatusBar(self._status_bar)

        # -- Floating toolbar (child of viewer) --
        self._toolbar = FloatingToolbar(self._viewer)
        self._toolbar.move(8, 8)

        # -- Menu bar --
        self._build_menus()

        # -- Connect signals --
        self._pipeline.image_changed.connect(self._viewer.set_image)
        self._pipeline.image_changed.connect(self._on_image_updated)
        self._file_browser.file_selected.connect(self._load_image)
        self._viewer.pixel_hovered.connect(self._status_bar.set_pixel)
        self._viewer.zoom_changed.connect(self._status_bar.set_zoom)
        self._viewer.ruler_distance.connect(self._status_bar.set_ruler_distance)
        self._viewer.color_picked.connect(self._toolbar.set_color)
        self._toolbar.tool_selected.connect(self._viewer.set_tool)
        self._toolbar.brush_color_changed.connect(self._viewer.set_brush_color)
        self._toolbar.brush_tip_changed.connect(self._viewer.set_brush_tip)
        self._viewer.set_pipeline(self._pipeline)
        self._pipeline_panel.stage_edit_requested.connect(self._viewer.start_stage_edit)
        Translator.instance().locale_changed.connect(self._on_language_changed)

        # -- Restore settings --
        self._restore_settings()

    def _build_menus(self):
        file_menu = self.menuBar().addMenu(tr("&File"))

        act_open_folder = QAction(tr("Open Folder..."), self)
        act_open_folder.triggered.connect(self._file_browser.open_folder)
        file_menu.addAction(act_open_folder)

        act_open_file = QAction(tr("Open File..."), self)
        act_open_file.setShortcut("Ctrl+O")
        act_open_file.triggered.connect(self._file_browser.open_file)
        file_menu.addAction(act_open_file)

        file_menu.addSeparator()

        export_menu = QMenu(tr("Export"), self)

        act_export_current = QAction(tr("Export Current..."), self)
        act_export_current.setShortcut("Ctrl+S")
        act_export_current.triggered.connect(self._export_current)
        export_menu.addAction(act_export_current)

        act_batch_export = QAction(tr("Batch Export..."), self)
        act_batch_export.setShortcut("Ctrl+Shift+S")
        act_batch_export.triggered.connect(self._batch_export)
        export_menu.addAction(act_batch_export)

        file_menu.addMenu(export_menu)

        file_menu.addSeparator()

        act_exit = QAction(tr("Exit"), self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        view_menu = self.menuBar().addMenu(tr("&View"))

        act_fit = QAction(tr("Fit to Window"), self)
        act_fit.setShortcut("Ctrl+0")
        act_fit.triggered.connect(self._viewer.fit_to_window)
        view_menu.addAction(act_fit)

        act_zoom_in = QAction(tr("Zoom In"), self)
        act_zoom_in.setShortcut("Ctrl++")
        act_zoom_in.triggered.connect(lambda: self._viewer.scale(1.25, 1.25))
        view_menu.addAction(act_zoom_in)

        act_zoom_out = QAction(tr("Zoom Out"), self)
        act_zoom_out.setShortcut("Ctrl+-")
        act_zoom_out.triggered.connect(lambda: self._viewer.scale(0.8, 0.8))
        view_menu.addAction(act_zoom_out)

        view_menu.addSeparator()

        self._act_grid = QAction(tr("Show Grid"), self)
        self._act_grid.setCheckable(True)
        self._act_grid.setShortcut("Ctrl+G")
        self._act_grid.toggled.connect(self._viewer.set_grid_enabled)
        view_menu.addAction(self._act_grid)

        lang_menu = self.menuBar().addMenu(tr("&Language"))

        act_zh = QAction(tr("中文"), self)
        act_zh.setCheckable(True)
        act_zh.triggered.connect(lambda: Translator.instance().set_locale("zh"))

        act_en = QAction(tr("English"), self)
        act_en.setCheckable(True)
        act_en.triggered.connect(lambda: Translator.instance().set_locale("en"))

        self._lang_group = QActionGroup(self)
        self._lang_group.setExclusive(True)
        self._lang_group.addAction(act_zh)
        self._lang_group.addAction(act_en)

        # Check the current locale
        if Translator.instance().locale == "zh":
            act_zh.setChecked(True)
        else:
            act_en.setChecked(True)

        lang_menu.addAction(act_zh)
        lang_menu.addAction(act_en)

    def _load_image(self, path: str):
        try:
            self._pipeline.load_image(path)
        except Exception as e:
            QMessageBox.warning(self, tr("Error"), tr("Failed to load image:\n{}").format(str(e)))

    def _on_image_updated(self, img: np.ndarray):
        h, w = img.shape[:2]
        self._status_bar.set_image_size(w, h)

    def _export_current(self):
        if self._pipeline.current is None:
            return
        include_strokes = self._ask_include_strokes()
        if include_strokes is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Save Image"),
            filter="PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)"
        )
        if not path:
            return
        source = self._pipeline.current if include_strokes else self._pipeline.pre_brush
        if source is None:
            source = self._pipeline.current
        bgr = cv2.cvtColor(source, cv2.COLOR_RGB2BGR)
        cv2.imwrite(path, bgr)

    def _ask_include_strokes(self):
        """Returns True/False or None if cancelled."""
        from PyQt5.QtWidgets import QCheckBox, QDialog, QVBoxLayout, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("Export"))
        layout = QVBoxLayout(dlg)
        cb = QCheckBox(tr("Include brush strokes"))
        cb.setChecked(False)
        layout.addWidget(cb)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        if not dlg.exec_():
            return None
        return cb.isChecked()

    def _batch_export(self):
        include_strokes = self._ask_include_strokes()
        if include_strokes is None:
            return
        input_dir = QFileDialog.getExistingDirectory(self, tr("Select Input Folder"))
        if not input_dir:
            return
        output_dir = QFileDialog.getExistingDirectory(self, tr("Select Output Folder"))
        if not output_dir:
            return

        files = sorted(
            f for f in os.listdir(input_dir)
            if f.lower().endswith(IMAGE_EXTENSIONS)
        )
        if not files:
            QMessageBox.information(self, tr("Export"), tr("No images found in folder."))
            return

        progress = QProgressDialog(tr("Processing..."), tr("Cancel"), 0, len(files), self)
        progress.setWindowModality(Qt.WindowModal)

        for i, filename in enumerate(files):
            if progress.wasCanceled():
                break
            progress.setValue(i)
            progress.setLabelText(tr("Processing: {}").format(filename))
            QApplication.processEvents()

            input_path = os.path.join(input_dir, filename)
            img = imread_unicode(input_path)
            if img is None:
                continue
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            result = self._pipeline.process_image(img_rgb)
            result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
            cv2.imwrite(os.path.join(output_dir, filename), result_bgr)

        progress.setValue(len(files))
        QMessageBox.information(
            self, tr("Export"),
            tr("Batch export complete. {} files processed.").format(i + 1)
        )

    def _restore_settings(self):
        settings = CacheManager.load_settings()
        if not settings:
            return
        if settings.get("window_geometry"):
            from PyQt5.QtCore import QByteArray
            self.restoreGeometry(QByteArray.fromBase64(settings["window_geometry"].encode()))
        if settings.get("window_state"):
            from PyQt5.QtCore import QByteArray
            self.restoreState(QByteArray.fromBase64(settings["window_state"].encode()))
        if settings.get("last_folder"):
            self._file_browser.set_root_path(settings["last_folder"])
        if settings.get("grid_enabled"):
            self._act_grid.setChecked(True)
        if settings.get("pipeline_config"):
            self._pipeline.load_config(settings["pipeline_config"])

    def closeEvent(self, event):
        settings = {
            "last_folder": self._file_browser.root_path,
            "window_geometry": self.saveGeometry().toBase64().data().decode(),
            "window_state": self.saveState().toBase64().data().decode(),
            "language": Translator.instance().locale,
            "grid_enabled": self._act_grid.isChecked(),
            "pipeline_config": self._pipeline.to_config(),
        }
        CacheManager.save_settings(settings)
        super().closeEvent(event)

    def _on_language_changed(self, _locale):
        self.setWindowTitle(tr("Image Tool"))
        self._left_dock.setWindowTitle(tr("Files"))
        self._right_dock.setWindowTitle(tr("Tools"))
        self.menuBar().clear()
        self._build_menus()
