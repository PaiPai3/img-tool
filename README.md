# Image Tool

基于 PyQt5 和 OpenCV 的桌面图像处理工具，支持多种滤镜实时预览。

## 快速开始

```sh
pip install -r requirements.txt
python main.py
```

## 功能

- **文件浏览** — 左侧文件树浏览和打开图片，支持常见格式（PNG、JPG、BMP、TIFF、WebP、GIF）
- **滤镜处理** — 右侧滤镜面板按类别组织，选择滤镜后实时预览效果
- **参数调节** — 每个滤镜提供可调节参数（滑块、数值框、复选框、下拉菜单）
- **像素拾取** — 鼠标悬停时状态栏显示坐标和 RGB 值
- **缩放与网格** — 滚轮缩放、拖拽平移、Ctrl+G 切换像素网格

## 内置滤镜

| 滤镜 | 类别 | 说明 |
|------|------|------|
| Gaussian Blur | Blur | 高斯模糊，可调核大小和 Sigma |
| Laplacian | Edge Detection | 拉普拉斯算子边缘检测 |
| Sobel | Edge Detection | Sobel 算子边缘检测，可分别设置 X/Y 方向导数 |
| Canny Edge | Edge Detection | Canny 边缘检测，支持双阈值和反转 |

## 项目结构

```
core/          # 核心抽象：FilterBase、FilterRegistry 自动发现、Pipeline
filters/       # 滤镜实现，放入新文件即自动注册
app/           # PyQt5 界面：主窗口、图像查看器、滤镜面板、文件浏览器、状态栏
utils/         # 工具函数：Unicode 路径图片读取、numpy 转 QPixmap
```

## 扩展滤镜

在 `filters/` 目录下新建 Python 文件，继承 `FilterBase` 并实现 `name`、`category`、`get_parameters()` 和 `apply()` 方法即可，无需手动注册。