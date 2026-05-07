import os
import numpy as np
import cv2
from PyQt5.QtGui import QImage, QPixmap


def imread_unicode(path: str) -> np.ndarray | None:
    """Load an image from a path that may contain Unicode characters."""
    with open(path, "rb") as f:
        data = np.frombuffer(f.read(), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def ndarray_to_qpixmap(img: np.ndarray) -> QPixmap:
    img = np.ascontiguousarray(img)
    h, w, ch = img.shape
    bytes_per_line = ch * w
    qimg = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg)
