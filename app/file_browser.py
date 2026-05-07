import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeView, QFileDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, QDir
from PyQt5.QtWidgets import QFileSystemModel
from core.i18n import tr, Translator

IMAGE_EXTENSIONS = ["*.png", "*.jpg", "*.jpeg", "*.bmp",
                    "*.tiff", "*.tif", "*.webp", "*.gif", "*.ico"]


class FileBrowser(QWidget):
    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        btn_layout = QHBoxLayout()
        self._btn_open_folder = QPushButton(tr("Open Folder"))
        self._btn_open_folder.clicked.connect(self.open_folder)
        self._btn_open_file = QPushButton(tr("Open File"))
        self._btn_open_file.clicked.connect(self.open_file)
        btn_layout.addWidget(self._btn_open_folder)
        btn_layout.addWidget(self._btn_open_file)
        layout.addLayout(btn_layout)

        self._model = QFileSystemModel()
        self._model.setNameFilters(IMAGE_EXTENSIONS)
        self._model.setNameFilterDisables(False)
        self._model.setRootPath("")

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setRootIndex(self._model.index(QDir.homePath()))
        self._tree.hideColumn(1)  # size
        self._tree.hideColumn(2)  # type
        self._tree.hideColumn(3)  # date modified
        self._tree.setHeaderHidden(True)
        self._tree.setAnimated(False)
        self._tree.setIndentation(16)
        self._tree.clicked.connect(self._on_clicked)
        layout.addWidget(self._tree)

        Translator.instance().locale_changed.connect(self.retranslate_ui)

    def _on_clicked(self, index):
        path = self._model.filePath(index)
        if os.path.isfile(path):
            self.file_selected.emit(path)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, tr("Open Folder"))
        if folder:
            self._tree.setRootIndex(self._model.index(folder))

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Open Image"),
            filter="Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp *.gif *.ico)"
        )
        if path:
            self.file_selected.emit(path)

    @property
    def root_path(self) -> str:
        return self._model.filePath(self._tree.rootIndex())

    def set_root_path(self, path: str):
        if os.path.isdir(path):
            self._tree.setRootIndex(self._model.index(path))

    def retranslate_ui(self):
        self._btn_open_folder.setText(tr("Open Folder"))
        self._btn_open_file.setText(tr("Open File"))
