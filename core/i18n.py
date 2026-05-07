from PyQt5.QtCore import QObject, pyqtSignal

_TRANSLATIONS = {
    "Image Tool": "图像工具",
    "&File": "文件(&F)",
    "Open Folder...": "打开文件夹...",
    "Open File...": "打开文件...",
    "Save As...": "另存为...",
    "Export": "导出",
    "Export Current...": "导出当前...",
    "Batch Export...": "批量导出...",
    "Exit": "退出",
    "&View": "视图(&V)",
    "Fit to Window": "适应窗口",
    "Zoom In": "放大",
    "Zoom Out": "缩小",
    "Show Grid": "显示网格",
    "&Language": "语言(&L)",
    "中文": "中文",
    "English": "English",
    "Open Folder": "打开文件夹",
    "Open File": "打开文件",
    "Open Image": "打开图像",
    "Pos: {}": "位置: {}",
    "RGB: {}": "RGB: {}",
    "Size: {}": "尺寸: {}",
    "Zoom: {}": "缩放: {}",
    "Files": "文件",
    "Tools": "工具",
    "Operations": "操作库",
    "Pipeline": "处理管线",
    "Add to Pipeline": "添加到管线",
    "Remove": "移除",
    "Move Up": "上移",
    "Move Down": "下移",
    "Stage Parameters": "阶段参数",
    "Save Pipeline": "保存管线",
    "Load Pipeline": "加载管线",
    "Save Pipeline As": "管线另存为",
    "Pipeline saved": "管线已保存",
    "Clear Pipeline": "清空管线",
    "None (Original)": "无 (原图)",
    "Invert": "反相",
    "Contrast": "对比度",
    "Convolution": "卷积",
    "Gaussian Blur": "高斯模糊",
    "Laplacian": "拉普拉斯",
    "Sobel": "索贝尔",
    "Canny Edge": "Canny边缘检测",
    "Blur": "模糊",
    "Edge Detection": "边缘检测",
    "Color": "色彩调整",
    "Filter": "滤波器",
    "Kernel Size": "核大小",
    "Sigma": "西格玛",
    "Derivative X": "X方向导数",
    "Derivative Y": "Y方向导数",
    "Scale": "缩放",
    "Low Threshold": "低阈值",
    "High Threshold": "高阈值",
    "Aperture Size": "孔径大小",
    "Brightness": "亮度",
    "Kernel Values": "卷积核",
    "Enable All": "全部启用",
    "Disable All": "全部禁用",
    "Error": "错误",
    "Failed to load image:\n{}": "无法加载图像:\n{}",
    "Images": "图像",
    "Select Input Folder": "选择输入文件夹",
    "Select Output Folder": "选择输出文件夹",
    "Processing...": "处理中...",
    "Cancel": "取消",
    "Processing: {}": "处理中: {}",
    "Save Image": "保存图像",
    "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)": "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)",
    "Overwrite?": "覆盖确认",
    "Pipeline already exists. Overwrite?": "管线已存在，是否覆盖？",
    "Import Pipeline": "导入管线",
    "Default": "默认",
    "Reset": "重置",
    "No image loaded.": "未加载图像。",
    "Batch export complete. {} files processed.": "批量导出完成。已处理 {} 个文件。",
    "No images found in folder.": "文件夹中未找到图像。",
    "No pipeline stages to export with.": "管线中没有阶段，将导出原图。",
}


class Translator(QObject):
    locale_changed = pyqtSignal(str)

    _instance = None

    def __init__(self):
        if Translator._instance is not None:
            raise RuntimeError("Use Translator.instance()")
        super().__init__()
        self._locale = "zh"
        Translator._instance = self

    @classmethod
    def instance(cls) -> "Translator":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def locale(self) -> str:
        return self._locale

    def set_locale(self, locale: str):
        if locale != self._locale:
            self._locale = locale
            self.locale_changed.emit(locale)


def tr(text: str, *args) -> str:
    translator = Translator.instance()
    if translator.locale == "zh":
        text = _TRANSLATIONS.get(text, text)
    if args:
        text = text.format(*args)
    return text
