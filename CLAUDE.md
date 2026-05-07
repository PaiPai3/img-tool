# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```sh
pip install -r requirements.txt   # Install dependencies
python main.py                    # Run the application
```

No tests, linters, or build steps are configured.

## Architecture

A PyQt5 desktop image processing tool with a chained pipeline system. Default language is Chinese (zh), toggleable to English.

### Core (`core/`)

- **`FilterBase`** (`core/filter_base.py`) — Abstract base class for all pipeline operations. Must define `name`, `category`, `get_parameters()` → `list[ParamDef]`, and `apply(image: np.ndarray, **params) -> np.ndarray`. `ParamDef.param_type` values: `"slider"`, `"int_spin"`, `"checkbox"`, `"dropdown"`, `"text"`.
- **`FilterRegistry`** (`core/filter_registry.py`) — Auto-discovers `FilterBase` subclasses in `filters/` via `pkgutil.iter_modules`. No manual registration needed.
- **`PipelineStage`** (`core/pipeline_stage.py`) — Dataclass: `id` (8-char hex), `filter_instance`, `params: dict`, `enabled: bool`. `apply()` passes through if disabled.
- **`Pipeline`** (`core/pipeline.py`) — The model. Holds `_stages: list[PipelineStage]`. `_process()` runs the image through all enabled stages sequentially. Stage CRUD methods. `process_image(img)` is stateless (for batch export). `to_config()`/`load_config()` for serialization. Pixel editing: `set_pixel(x, y, color)`, `draw_crosshair(x, y, color)` modify `_current` and emit `image_changed`.
- **`Translator`** (`core/i18n.py`) — Singleton `QObject` with `tr(text, *args)` global function. English keys mapped to Chinese. Laplacian/Sobel/Canny Edge are intentionally NOT translated (technical terms).
- **`CacheManager`** (`core/cache_manager.py`) — Static methods for `cache/settings.json` and `cache/pipelines/{name}.json`.

### Filters (`filters/`)

All images are RGB `np.ndarray`. Categories: Blur (GaussianBlur), Edge Detection (Laplacian, Sobel, CannyEdge), Color (Invert, Contrast, Grayscale), Filter (Convolution, Sharpen).

### App (`app/`)

- **`MainWindow`** (`app/main_window.py`) — Owns `Pipeline`, creates docks + FloatingToolbar + menus. Wires: FileBrowser → pipeline, Pipeline.image_changed → viewer + status bar, toolbar ↔ viewer. Menus: File (Open, Export current/batch, Exit), View (Fit/Zoom/Grid), Language (中文/English).
- **`PipelinePanel`** (`app/pipeline_panel.py`) — Right dock. Filter library tree (double-click or button to add to pipeline). Stage list with enable/up/down/remove. Parameter editor for selected stage (60ms debounce). Save/Load/Clear pipeline buttons.
- **`ImageViewer`** (`app/image_viewer.py`) — `QGraphicsView` with tool system. Tool enum: NONE, BRUSH, CROSSHAIR, PICKER, RULER. Default NONE = scroll-hand drag + zoom. BRUSH/CROSSHAIR call Pipeline pixel methods. PICKER emits `color_picked(r,g,b)`. RULER draws Manhattan path overlay (QGraphicsRectItems), emits `ruler_distance(str)`, ESC to cancel. Pixel hover emits LAB values in addition to RGB.
- **`FloatingToolbar`** (`app/toolbar.py`) — Semi-transparent widget, child of ImageViewer, positioned at (8,8). Color swatch (click for QColorDialog), exclusive tool buttons (Brush/Crosshair/Picker/Ruler). Emits `tool_selected(Tool)`, `brush_color_changed(r,g,b)`.
- **`FileBrowser`** (`app/file_browser.py`) — `QFileSystemModel`-based tree filtered to image extensions.
- **`StatusBar`** (`app/status_bar.py`) — Position, RGB, LAB, zoom %, image size, ruler distance.

### Utils (`utils/`)

- `imread_unicode(path)` — cv2 image load with Unicode path support.
- `ndarray_to_qpixmap(img)` — Zero-copy RGB ndarray → QPixmap.
