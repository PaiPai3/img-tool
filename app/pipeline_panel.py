from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QFormLayout, QSlider, QSpinBox, QCheckBox, QComboBox, QPushButton,
    QGroupBox, QScrollArea, QFrame, QLineEdit, QFileDialog, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from core.filter_base import FilterBase, ParamDef
from core.filter_registry import FilterRegistry
from core.i18n import tr, Translator


class StageRow(QFrame):
    remove_clicked = pyqtSignal(str)
    move_up_clicked = pyqtSignal(str)
    move_down_clicked = pyqtSignal(str)
    enabled_toggled = pyqtSignal(str, bool)
    selected = pyqtSignal(str)

    def __init__(self, stage_id: str, name: str, enabled: bool, parent=None):
        super().__init__(parent)
        self._id = stage_id
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        self._check = QCheckBox()
        self._check.setChecked(enabled)
        self._check.toggled.connect(lambda v: self.enabled_toggled.emit(self._id, v))

        self._label = QLabel(name)
        self._label.setCursor(Qt.PointingHandCursor)

        self._up_btn = QPushButton("↑")
        self._up_btn.setFixedWidth(28)
        self._up_btn.clicked.connect(lambda: self.move_up_clicked.emit(self._id))

        self._down_btn = QPushButton("↓")
        self._down_btn.setFixedWidth(28)
        self._down_btn.clicked.connect(lambda: self.move_down_clicked.emit(self._id))

        self._del_btn = QPushButton("✕")
        self._del_btn.setFixedWidth(28)
        self._del_btn.clicked.connect(lambda: self.remove_clicked.emit(self._id))

        layout.addWidget(self._check, 0)
        layout.addWidget(self._label, 1)
        layout.addWidget(self._up_btn, 0)
        layout.addWidget(self._down_btn, 0)
        layout.addWidget(self._del_btn, 0)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.selected.emit(self._id)

    def set_selected(self, selected: bool):
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def retranslate(self):
        self._label.setText(tr(self._label.text()) if self._label.text() else "")


class PipelinePanel(QWidget):
    pipeline_changed = pyqtSignal()

    def __init__(self, pipeline, parent=None):
        super().__init__(parent)
        self._pipeline = pipeline
        self._selected_stage_id: str | None = None
        self._param_widgets: dict[str, object] = {}
        self._current_filter_instance: FilterBase = None

        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # -- Operations library --
        layout.addWidget(QLabel("<b>" + tr("Operations") + "</b>"))

        self._filter_tree = QTreeWidget()
        self._filter_tree.setHeaderHidden(True)
        self._filter_tree.setRootIsDecorated(True)
        layout.addWidget(self._filter_tree)

        self._add_btn = QPushButton(tr("Add to Pipeline"))
        self._add_btn.clicked.connect(self._on_add_stage)
        layout.addWidget(self._add_btn)

        # -- Pipeline stage list --
        layout.addWidget(QLabel("<b>" + tr("Pipeline") + "</b>"))

        self._stage_container = QWidget()
        self._stage_layout = QVBoxLayout(self._stage_container)
        self._stage_layout.setContentsMargins(0, 0, 0, 0)
        self._stage_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._stage_container)
        scroll.setMinimumHeight(80)
        scroll.setMaximumHeight(200)
        layout.addWidget(scroll)

        # -- Stage parameters --
        self._param_group = QGroupBox(tr("Stage Parameters"))
        self._param_layout = QFormLayout()
        self._param_group.setLayout(self._param_layout)
        self._param_group.setVisible(False)
        layout.addWidget(self._param_group)

        self._reset_btn = QPushButton(tr("Reset"))
        self._reset_btn.clicked.connect(self._on_reset_params)
        self._reset_btn.setVisible(False)
        layout.addWidget(self._reset_btn)

        # -- Pipeline management --
        layout.addSpacing(8)

        mgmt_layout = QHBoxLayout()
        self._save_btn = QPushButton(tr("Save Pipeline"))
        self._save_btn.clicked.connect(self._on_save_pipeline)
        self._load_btn = QPushButton(tr("Load Pipeline"))
        self._load_btn.clicked.connect(self._on_load_pipeline)
        mgmt_layout.addWidget(self._save_btn)
        mgmt_layout.addWidget(self._load_btn)
        layout.addLayout(mgmt_layout)

        self._clear_btn = QPushButton(tr("Clear Pipeline"))
        self._clear_btn.clicked.connect(self._pipeline.clear_stages)
        layout.addWidget(self._clear_btn)

        layout.addStretch()

        # -- Debounce timer --
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(60)
        self._debounce.timeout.connect(self._emit_params)

        # -- Populate --
        self._populate_filters()
        self._pipeline.pipeline_changed.connect(self._on_pipeline_changed)
        Translator.instance().locale_changed.connect(self._on_language_changed)

    def _populate_filters(self):
        self._filter_tree.clear()
        categories = FilterRegistry.get_categories()
        for cat, filters in sorted(categories.items()):
            cat_item = QTreeWidgetItem(self._filter_tree, [tr(cat)])
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsSelectable)
            for name, filter_cls in sorted(filters):
                item = QTreeWidgetItem(cat_item, [tr(name)])
                item.setData(0, Qt.UserRole, filter_cls)
        self._filter_tree.expandAll()

    def _on_add_stage(self):
        current = self._filter_tree.currentItem()
        if current is None:
            return
        filter_cls = current.data(0, Qt.UserRole)
        if filter_cls is None:
            return
        self._pipeline.add_stage(filter_cls)

    def _on_pipeline_changed(self):
        selected_id = self._selected_stage_id
        self._stage_layout.takeAt(self._stage_layout.count() - 1)  # remove stretch
        while self._stage_layout.count() > 0:
            item = self._stage_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for stage in self._pipeline.stages:
            row = StageRow(stage.id, tr(stage.name), stage.enabled)
            row.remove_clicked.connect(self._pipeline.remove_stage)
            row.move_up_clicked.connect(lambda sid: self._pipeline.move_stage(sid, -1))
            row.move_down_clicked.connect(lambda sid: self._pipeline.move_stage(sid, 1))
            row.enabled_toggled.connect(self._pipeline.set_stage_enabled)
            row.selected.connect(self._select_stage)
            if stage.id == selected_id:
                row.set_selected(True)
            self._stage_layout.addWidget(row)

        self._stage_layout.addStretch()

        # Restore selection if possible
        current_ids = {s.id for s in self._pipeline.stages}
        if selected_id not in current_ids:
            self._select_stage(None)

    def _select_stage(self, stage_id: str | None):
        self._selected_stage_id = stage_id
        self._clear_params()

        if stage_id is None:
            self._param_group.setVisible(False)
            self._reset_btn.setVisible(False)
            self._current_filter_instance = None
            return

        stage = next((s for s in self._pipeline.stages if s.id == stage_id), None)
        if stage is None:
            return

        self._current_filter_instance = stage.filter_instance
        self._build_param_widgets(stage.params)
        self._param_group.setVisible(True)
        self._reset_btn.setVisible(True)

        # Update visual selection
        for i in range(self._stage_layout.count()):
            w = self._stage_layout.itemAt(i).widget()
            if isinstance(w, StageRow):
                w.set_selected(w._id == stage_id)

    def _build_param_widgets(self, params: dict):
        if self._current_filter_instance is None:
            return
        for param in self._current_filter_instance.get_parameters():
            current_val = params.get(param.name, param.default)
            if param.param_type == "slider":
                w = self._create_slider(param, current_val)
            elif param.param_type == "int_spin":
                w = self._create_int_spin(param, current_val)
            elif param.param_type == "checkbox":
                w = self._create_checkbox(param, current_val)
            elif param.param_type == "dropdown":
                w = self._create_dropdown(param, current_val)
            elif param.param_type == "text":
                w = self._create_text_input(param, current_val)
            else:
                continue
            self._param_widgets[param.name] = w
            self._param_layout.addRow(tr(param.label) + ":", w)

    def _create_slider(self, param: ParamDef, value):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(int(param.min_val / param.step), int(param.max_val / param.step))
        slider.setValue(int(value / param.step))
        slider.setTickPosition(QSlider.TicksBelow)

        label = QLabel(f"{value:.2f}".rstrip("0").rstrip("."))
        label.setAlignment(Qt.AlignRight)

        def on_change(v, l=label, s=param.step):
            l.setText(f"{v * s:.2f}".rstrip("0").rstrip("."))
            self._debounce.start()

        slider.valueChanged.connect(on_change)
        slider.valueChanged.connect(lambda: self._debounce.start())

        layout.addWidget(slider)
        layout.addWidget(label)
        return container

    def _create_int_spin(self, param: ParamDef, value):
        spin = QSpinBox()
        spin.setRange(int(param.min_val), int(param.max_val))
        spin.setValue(int(value))
        spin.setSingleStep(int(param.step))
        spin.valueChanged.connect(lambda: self._debounce.start())
        return spin

    def _create_checkbox(self, param: ParamDef, value):
        cb = QCheckBox()
        cb.setChecked(bool(value))
        cb.toggled.connect(lambda: self._debounce.start())
        return cb

    def _create_dropdown(self, param: ParamDef, value):
        combo = QComboBox()
        combo.addItems(param.options)
        combo.setCurrentText(str(value))
        combo.currentTextChanged.connect(lambda: self._debounce.start())
        return combo

    def _create_text_input(self, param: ParamDef, value):
        edit = QLineEdit(str(value))
        edit.textChanged.connect(lambda: self._debounce.start())
        return edit

    def _read_params(self) -> dict:
        params = {}
        if self._current_filter_instance is None:
            return params
        for param in self._current_filter_instance.get_parameters():
            w = self._param_widgets.get(param.name)
            if w is None:
                continue
            if param.param_type == "slider":
                slider = w.findChild(QSlider)
                params[param.name] = slider.value() * param.step
            elif param.param_type == "int_spin":
                params[param.name] = w.value()
            elif param.param_type == "checkbox":
                params[param.name] = w.isChecked()
            elif param.param_type == "dropdown":
                params[param.name] = w.currentText()
            elif param.param_type == "text":
                params[param.name] = w.text()
        return params

    def _emit_params(self):
        if self._current_filter_instance is None or self._selected_stage_id is None:
            return
        params = self._read_params()
        self._pipeline.set_stage_params(self._selected_stage_id, params)

    def _clear_params(self):
        self._debounce.stop()
        while self._param_layout.rowCount() > 0:
            self._param_layout.removeRow(0)
        self._param_widgets.clear()

    def _on_reset_params(self):
        if self._current_filter_instance is None or self._selected_stage_id is None:
            return
        defaults = {p.name: p.default for p in self._current_filter_instance.get_parameters()}
        self._pipeline.set_stage_params(self._selected_stage_id, defaults)
        self._clear_params()
        self._build_param_widgets(defaults)
        self._param_group.setVisible(True)

    def _on_save_pipeline(self):
        from core.cache_manager import CacheManager
        name, ok = QFileDialog.getSaveFileName(self, tr("Save Pipeline As"),
                                                CacheManager.PIPELINES_DIR,
                                                "JSON (*.json)")
        if not ok or not name:
            return
        import os
        basename = os.path.splitext(os.path.basename(name))[0]
        config = self._pipeline.to_config()
        if not config:
            return
        CacheManager.save_pipeline(basename, config)
        QMessageBox.information(self, tr("Pipeline saved"), tr("Pipeline saved"))

    def _on_load_pipeline(self):
        from core.cache_manager import CacheManager
        pipelines = CacheManager.list_pipelines()
        if not pipelines:
            return
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getItem(self, tr("Load Pipeline"), tr("Import Pipeline"),
                                         pipelines, 0, False)
        if not ok or not name:
            return
        config = CacheManager.load_pipeline(name)
        if config is not None:
            self._pipeline.load_config(config)

    def _on_language_changed(self, _locale):
        self._populate_filters()
        for i in range(self._stage_layout.count()):
            w = self._stage_layout.itemAt(i).widget()
            if isinstance(w, StageRow):
                w.retranslate()
        # Rebuild param section if a stage is selected
        if self._selected_stage_id is not None:
            stage = next((s for s in self._pipeline.stages if s.id == self._selected_stage_id), None)
            if stage:
                self._clear_params()
                self._build_param_widgets(stage.params)
        # Translate static labels
        for item in self.findChildren(QLabel):
            if item.text() and "<b>" in item.text():
                inner = item.text().replace("<b>", "").replace("</b>", "")
                item.setText("<b>" + tr(inner) + "</b>")
        self._add_btn.setText(tr("Add to Pipeline"))
        self._param_group.setTitle(tr("Stage Parameters"))
        self._reset_btn.setText(tr("Reset"))
        self._save_btn.setText(tr("Save Pipeline"))
        self._load_btn.setText(tr("Load Pipeline"))
        self._clear_btn.setText(tr("Clear Pipeline"))
