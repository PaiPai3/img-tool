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
- **`Pipeline`** (`core/pipeline.py`) — The model. Holds `_stages: list[PipelineStage]`. `_process()` runs the image through all enabled stages sequentially (output of stage N → input of stage N+1). Emits `image_changed` (for viewer) and `pipeline_changed` (for UI refresh). Stage CRUD: `add_stage`, `remove_stage`, `move_stage`, `set_stage_enabled`, `set_stage_params`, `clear_stages`. `process_image(img)` is stateless (for batch export). Serialization via `to_config()`/`load_config()`.
- **`Translator`** (`core/i18n.py`) — Singleton `QObject` with `tr(text, *args)` global function. English keys mapped to Chinese. Emits `locale_changed` signal; all UI components connect to it for live language switching.
- **`CacheManager`** (`core/cache_manager.py`) — Static methods for `cache/settings.json` (last folder, window state, language, grid) and `cache/pipelines/{name}.json`.

### Filters (`filters/`)

Each file = one `FilterBase` subclass. All images are RGB `np.ndarray` (BGR→RGB converted on load). Gray→RGB conversion for edge-detection outputs.

Categories: Blur (GaussianBlur), Edge Detection (Laplacian, Sobel, CannyEdge), Color (Invert, Contrast), Filter (Convolution).

### App (`app/`)

- **`MainWindow`** (`app/main_window.py`) — Owns `Pipeline`, creates docks + menus. Signal wiring: FileBrowser → pipeline load, Pipeline.image_changed → viewer + status bar. Menus: File (Open, Export current/batch, Exit), View (Fit/Zoom/Grid), Language (中文/English). Saves/restores settings via `CacheManager` on close/open.
- **`PipelinePanel`** (`app/pipeline_panel.py`) — Right dock. Top: filter library tree (from `FilterRegistry`). Middle: pipeline stage list (check/enable, name, up/down/remove buttons). Bottom: parameter editor for selected stage (60ms debounce). Save/Load/Clear pipeline buttons.
- **`ImageViewer`** (`app/image_viewer.py`) — `QGraphicsView`. Scroll-hand drag, mouse-wheel zoom, pixel-hover RGB readout. Adaptive pixel grid in `drawForeground()`: interval = `max(1, round(1/scale))`, so at ≥100% zoom each pixel has borders.
- **`FileBrowser`** (`app/file_browser.py`) — `QFileSystemModel`-based tree filtered to image extensions.
- **`StatusBar`** (`app/status_bar.py`) — Position, RGB, zoom %, image size. All labels use `tr()`.

### Utils (`utils/`)

- `imread_unicode(path)` — cv2 image load with Unicode path support.
- `ndarray_to_qpixmap(img)` — Zero-copy RGB ndarray → QPixmap.
