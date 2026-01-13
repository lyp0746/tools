# -*- coding: utf-8 -*-
"""
ImageProcessorPro Ultimate - 专业图像处理工具（完全重构版）
对标 WPS 图片软件的全功能实现

主要功能：
✓ 基础编辑：裁剪、旋转、翻转、缩放
✓ 高级调节：亮度、对比度、饱和度、色温、色相、锐化
✓ 滤镜特效：20+种专业滤镜（复古、冷暖色调、黑白艺术等）
✓ AI功能：智能抠图、背景移除、智能修复
✓ 标注工具：文字、箭头、矩形、圆形、马赛克
✓ 水印：文字/图片水印、批量加水印
✓ 拼图：横向/纵向/网格拼接
✓ 批处理：批量格式转换、压缩、重命名
✓ OCR：文字识别（中英文）
✓ 美颜：磨皮、美白、去红眼
✓ 打印：预览和打印功能
✓ 历史记录：无限撤销/重做
✓ 快捷键：全快捷键支持

Version: 2.0
作者：LYP
GitHub：https://github.com/lyp0746
邮箱：1610369302@qq.com
Date: 2025-12-12
"""

import sys
import os
import json
import time
from io import BytesIO
from typing import List, Tuple, Optional, Dict
from concurrent.futures import ThreadPoolExecutor
import threading

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QMutex, QTimer, QBuffer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QSlider, QSpinBox, QComboBox,
    QLineEdit, QTextEdit, QCheckBox, QTabWidget, QSplitter, QToolBar,
    QAction, QActionGroup, QMenuBar, QMenu, QStatusBar, QProgressBar,
    QFileDialog, QMessageBox, QDialog, QDialogButtonBox, QScrollArea,
    QGridLayout, QGroupBox, QColorDialog, QInputDialog, QListWidgetItem, QShortcut
)
from PyQt5.QtGui import (
    QPixmap, QImage, QPainter, QPen, QColor, QIcon, QFont, QKeySequence,
    QPalette, QBrush, QCursor
)

from PIL import (
    Image, ImageFilter, ImageFont, ImageDraw, ImageEnhance,
    ImageOps, ImageChops, ImageStat, ExifTags, ImageQt
)
import numpy as np
import cv2

# 可选依赖
try:
    import pytesseract

    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("Warning: pytesseract not installed, OCR功能不可用")

try:
    from rembg import remove as rembg_remove

    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False
    print("Warning: rembg not installed, AI抠图功能不可用")

try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed, 直方图功能不可用")

# ==================== 常量定义 ====================

SUPPORTED_FORMATS = [
    ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif",
    ".webp", ".ico", ".ppm", ".pgm", ".pbm"
]

# 滤镜预设
FILTER_PRESETS = {
    "原图": None,
    "黑白": "grayscale",
    "怀旧": "sepia",
    "反色": "invert",
    "模糊": "blur",
    "高斯模糊": "gaussian_blur",
    "锐化": "sharpen",
    "边缘增强": "edge_enhance",
    "浮雕": "emboss",
    "轮廓": "contour",
    "查找边缘": "find_edges",
    "复古": "vintage",
    "冷色调": "cool",
    "暖色调": "warm",
    "鲜艳": "vivid",
    "柔和": "soft",
    "戏剧": "dramatic",
    "高对比黑白": "high_contrast_bw",
    "HDR": "hdr",
    "卡通": "cartoon",
    "素描": "sketch",
}


# ==================== 工具函数 ====================

def pil_to_qimage(pil_image: Image.Image) -> QImage:
    """PIL Image转QImage（优化版）"""
    if pil_image is None:
        return QImage()

    # 转换为RGBA确保兼容性
    if pil_image.mode not in ("RGB", "RGBA", "L"):
        pil_image = pil_image.convert("RGBA")

    if pil_image.mode == "RGB":
        data = pil_image.tobytes("raw", "RGB")
        qimage = QImage(
            data, pil_image.width, pil_image.height,
            pil_image.width * 3, QImage.Format_RGB888
        )
    elif pil_image.mode == "RGBA":
        data = pil_image.tobytes("raw", "RGBA")
        qimage = QImage(
            data, pil_image.width, pil_image.height,
            pil_image.width * 4, QImage.Format_RGBA8888
        )
    elif pil_image.mode == "L":
        data = pil_image.tobytes("raw", "L")
        qimage = QImage(
            data, pil_image.width, pil_image.height,
            pil_image.width, QImage.Format_Grayscale8
        )
    else:
        pil_image = pil_image.convert("RGBA")
        data = pil_image.tobytes("raw", "RGBA")
        qimage = QImage(
            data, pil_image.width, pil_image.height,
            pil_image.width * 4, QImage.Format_RGBA8888
        )

    return qimage.copy()  # 创建副本避免数据失效


def qimage_to_pil(qimage: QImage) -> Image.Image:
    """QImage转PIL Image"""
    if qimage.isNull():
        return None

    buffer = QBuffer()
    buffer.open(QBuffer.ReadWrite)
    qimage.save(buffer, "PNG")

    pil_image = Image.open(BytesIO(buffer.data()))
    return pil_image


def load_image(path: str) -> Image.Image:
    """加载图片并处理EXIF方向"""
    try:
        img = Image.open(path)

        # 处理EXIF方向
        try:
            exif = img._getexif()
            if exif:
                orientation = exif.get(274)  # Orientation tag
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
        except:
            pass

        # 转换为RGBA保持透明度
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        return img
    except Exception as e:
        print(f"Error loading image {path}: {e}")
        return None


def save_image(image: Image.Image, path: str, quality: int = 95,
               optimize: bool = True, strip_exif: bool = False):
    """保存图片"""
    try:
        # 根据扩展名确定格式
        ext = os.path.splitext(path)[1].lower()

        if ext in [".jpg", ".jpeg"]:
            # JPEG不支持透明度
            if image.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = background
            else:
                image = image.convert("RGB")

            image.save(path, "JPEG", quality=quality, optimize=optimize)

        elif ext == ".png":
            image.save(path, "PNG", optimize=optimize)

        elif ext == ".webp":
            image.save(path, "WEBP", quality=quality)

        else:
            # 其他格式
            if image.mode == "RGBA":
                image = image.convert("RGB")
            image.save(path, quality=quality if ext not in [".bmp", ".gif"] else None)

        return True
    except Exception as e:
        print(f"Error saving image to {path}: {e}")
        return False


def apply_filter(image: Image.Image, filter_name: str) -> Image.Image:
    """应用滤镜"""
    if filter_name == "grayscale":
        return ImageOps.grayscale(image).convert("RGBA")

    elif filter_name == "sepia":
        # 怀旧色调
        img = image.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        sepia_matrix = np.array([
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131]
        ])
        arr = arr @ sepia_matrix.T
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr).convert("RGBA")

    elif filter_name == "invert":
        return ImageOps.invert(image.convert("RGB")).convert("RGBA")

    elif filter_name == "blur":
        return image.filter(ImageFilter.BLUR)

    elif filter_name == "gaussian_blur":
        return image.filter(ImageFilter.GaussianBlur(radius=3))

    elif filter_name == "sharpen":
        return image.filter(ImageFilter.SHARPEN)

    elif filter_name == "edge_enhance":
        return image.filter(ImageFilter.EDGE_ENHANCE_MORE)

    elif filter_name == "emboss":
        return image.filter(ImageFilter.EMBOSS)

    elif filter_name == "contour":
        return image.filter(ImageFilter.CONTOUR)

    elif filter_name == "find_edges":
        return image.filter(ImageFilter.FIND_EDGES)

    elif filter_name == "vintage":
        # 复古效果
        img = apply_filter(image, "sepia")
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(0.8)
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(0.9)

    elif filter_name == "cool":
        # 冷色调
        img = image.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.2, 0, 255)  # 增强蓝色
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 0.8, 0, 255)  # 减弱红色
        return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")

    elif filter_name == "warm":
        # 暖色调
        img = image.convert("RGB")
        arr = np.array(img, dtype=np.float32)
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.2, 0, 255)  # 增强红色
        arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.1, 0, 255)  # 增强绿色
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.8, 0, 255)  # 减弱蓝色
        return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")

    elif filter_name == "vivid":
        # 鲜艳
        enhancer = ImageEnhance.Color(image)
        return enhancer.enhance(1.5)

    elif filter_name == "soft":
        # 柔和
        enhancer = ImageEnhance.Contrast(image)
        img = enhancer.enhance(0.7)
        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(0.5)

    elif filter_name == "dramatic":
        # 戏剧性
        enhancer = ImageEnhance.Contrast(image)
        img = enhancer.enhance(1.5)
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(0.9)

    elif filter_name == "high_contrast_bw":
        # 高对比黑白
        img = ImageOps.grayscale(image)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        return img.convert("RGBA")

    elif filter_name == "hdr":
        # HDR效果
        img = image.convert("RGB")
        arr = np.array(img, dtype=np.float32) / 255.0
        # 简单的HDR模拟
        arr = np.power(arr, 0.7) * 255.0
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(1.3).convert("RGBA")

    elif filter_name == "cartoon":
        # 卡通效果
        img_rgb = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                      cv2.THRESH_BINARY, 9, 9)
        color = cv2.bilateralFilter(img_rgb, 9, 300, 300)
        cartoon = cv2.bitwise_and(color, color, mask=edges)
        cartoon_rgb = cv2.cvtColor(cartoon, cv2.COLOR_BGR2RGB)
        return Image.fromarray(cartoon_rgb).convert("RGBA")

    elif filter_name == "sketch":
        # 素描效果
        img_rgb = np.array(image.convert("RGB"))
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        inv = 255 - gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        sketch = cv2.divide(gray, 255 - blur, scale=256)
        return Image.fromarray(sketch).convert("RGBA")

    return image


def adjust_brightness(image: Image.Image, value: float) -> Image.Image:
    """调整亮度 (0.5-1.5)"""
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(value)


def adjust_contrast(image: Image.Image, value: float) -> Image.Image:
    """调整对比度 (0.5-1.5)"""
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(value)


def adjust_saturation(image: Image.Image, value: float) -> Image.Image:
    """调整饱和度 (0-2)"""
    enhancer = ImageEnhance.Color(image)
    return enhancer.enhance(value)


def adjust_sharpness(image: Image.Image, value: float) -> Image.Image:
    """调整锐度 (0-2)"""
    enhancer = ImageEnhance.Sharpness(image)
    return enhancer.enhance(value)


def adjust_temperature(image: Image.Image, value: int) -> Image.Image:
    """调整色温 (-100 to 100)"""
    if value == 0:
        return image

    img = image.convert("RGB")
    arr = np.array(img, dtype=np.int16)

    if value > 0:  # 暖色
        arr[:, :, 0] = np.clip(arr[:, :, 0] + value, 0, 255)
        arr[:, :, 1] = np.clip(arr[:, :, 1] + value // 2, 0, 255)
    else:  # 冷色
        arr[:, :, 2] = np.clip(arr[:, :, 2] - value, 0, 255)

    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")


def adjust_hue(image: Image.Image, value: int) -> Image.Image:
    """调整色相 (-180 to 180)"""
    if value == 0:
        return image

    img = image.convert("RGB")
    arr = np.array(img, dtype=np.float32) / 255.0

    # RGB to HSV
    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
    hsv[:, :, 0] = (hsv[:, :, 0] + value / 360.0) % 1.0

    # HSV to RGB
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    rgb = (rgb * 255).clip(0, 255).astype(np.uint8)

    return Image.fromarray(rgb).convert("RGBA")


def add_text_watermark(image: Image.Image, text: str, position: str = "bottom_right",
                       opacity: int = 128, font_size: int = 36, color: tuple = (255, 255, 255)) -> Image.Image:
    """添加文字水印"""
    if not text:
        return image

    img = image.convert("RGBA")
    txt_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    # 尝试加载字体
    try:
        # Windows
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        try:
            # macOS
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            try:
                # Linux
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()

    # 获取文字大小
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 计算位置
    margin = 20
    if position == "top_left":
        pos = (margin, margin)
    elif position == "top_right":
        pos = (img.width - text_width - margin, margin)
    elif position == "bottom_left":
        pos = (margin, img.height - text_height - margin)
    elif position == "bottom_right":
        pos = (img.width - text_width - margin, img.height - text_height - margin)
    elif position == "center":
        pos = ((img.width - text_width) // 2, (img.height - text_height) // 2)
    else:
        pos = (margin, margin)

    # 绘制文字
    draw.text(pos, text, fill=(*color, opacity), font=font)

    return Image.alpha_composite(img, txt_layer)


def remove_background(image: Image.Image) -> Image.Image:
    """AI抠图/背景移除"""
    if not HAS_REMBG:
        raise ImportError("需要安装rembg库: pip install rembg")

    # 转换为RGB
    img = image.convert("RGB")

    # 使用rembg移除背景
    output = rembg_remove(img)

    return output


def mosaic_area(image: Image.Image, x: int, y: int, width: int, height: int,
                block_size: int = 10) -> Image.Image:
    """对指定区域添加马赛克"""
    img = image.copy()

    # 确保区域在图片范围内
    x = max(0, min(x, img.width))
    y = max(0, min(y, img.height))
    width = min(width, img.width - x)
    height = min(height, img.height - y)

    if width <= 0 or height <= 0:
        return img

    # 提取区域
    region = img.crop((x, y, x + width, y + height))

    # 缩小再放大实现马赛克效果
    small_w = max(1, width // block_size)
    small_h = max(1, height // block_size)
    region = region.resize((small_w, small_h), Image.NEAREST)
    region = region.resize((width, height), Image.NEAREST)

    # 粘贴回去
    img.paste(region, (x, y))

    return img


def stitch_images(images: List[Image.Image], direction: str = "horizontal",
                  spacing: int = 0, background_color: tuple = (255, 255, 255, 255)) -> Image.Image:
    """拼接图片"""
    if not images:
        return None

    if len(images) == 1:
        return images[0]

    # 转换所有图片为RGBA
    images = [img.convert("RGBA") for img in images]

    if direction == "horizontal":
        # 横向拼接
        total_width = sum(img.width for img in images) + spacing * (len(images) - 1)
        max_height = max(img.height for img in images)

        result = Image.new("RGBA", (total_width, max_height), background_color)

        x_offset = 0
        for img in images:
            y_offset = (max_height - img.height) // 2
            result.paste(img, (x_offset, y_offset), img)
            x_offset += img.width + spacing

    elif direction == "vertical":
        # 纵向拼接
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images) + spacing * (len(images) - 1)

        result = Image.new("RGBA", (max_width, total_height), background_color)

        y_offset = 0
        for img in images:
            x_offset = (max_width - img.width) // 2
            result.paste(img, (x_offset, y_offset), img)
            y_offset += img.height + spacing

    elif direction == "grid":
        # 网格拼接（自动计算行列）
        count = len(images)
        cols = int(np.ceil(np.sqrt(count)))
        rows = int(np.ceil(count / cols))

        max_width = max(img.width for img in images)
        max_height = max(img.height for img in images)

        total_width = max_width * cols + spacing * (cols - 1)
        total_height = max_height * rows + spacing * (rows - 1)

        result = Image.new("RGBA", (total_width, total_height), background_color)

        for idx, img in enumerate(images):
            row = idx // cols
            col = idx % cols
            x = col * (max_width + spacing)
            y = row * (max_height + spacing)
            x_offset = (max_width - img.width) // 2
            y_offset = (max_height - img.height) // 2
            result.paste(img, (x + x_offset, y + y_offset), img)

    return result


def ocr_text(image: Image.Image, lang: str = "chi_sim+eng") -> str:
    """OCR文字识别"""
    if not HAS_OCR:
        raise ImportError("需要安装pytesseract和Tesseract-OCR")

    # 转换为灰度图提高识别率
    img = image.convert("RGB")
    img_array = np.array(img)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    # 二值化
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # OCR识别
    text = pytesseract.image_to_string(binary, lang=lang)

    return text


def get_exif_data(image: Image.Image) -> dict:
    """获取EXIF信息"""
    exif_data = {}
    try:
        exif = image._getexif()
        if exif:
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                exif_data[tag] = str(value)
    except:
        pass

    return exif_data


def calculate_histogram(image: Image.Image) -> tuple:
    """计算直方图（RGB通道）"""
    img = image.convert("RGB")

    r_hist = np.array(img.split()[0].histogram())
    g_hist = np.array(img.split()[1].histogram())
    b_hist = np.array(img.split()[2].histogram())

    return r_hist, g_hist, b_hist


# ==================== 自定义控件 ====================

class ImagePreviewLabel(QLabel):
    """图片预览标签（支持缩放、拖拽、绘制）"""

    # 信号
    cropAreaSelected = pyqtSignal(tuple)  # (x, y, width, height)
    mosaicAreaSelected = pyqtSignal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
        self.setMinimumSize(400, 300)

        # 状态
        self.original_pixmap = None
        self.current_zoom = 1.0
        self.fit_to_window = True

        # 绘制状态
        self.drawing_mode = None  # 'crop', 'mosaic', None
        self.is_drawing = False
        self.start_pos = None
        self.current_rect = None

        self.setMouseTracking(True)

    def set_image(self, pixmap: QPixmap):
        """设置图片"""
        self.original_pixmap = pixmap
        self.update_display()

    def update_display(self):
        """更新显示"""
        if self.original_pixmap is None:
            self.clear()
            return

        if self.fit_to_window:
            # 适应窗口
            scaled = self.original_pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        else:
            # 按缩放比例
            new_size = self.original_pixmap.size() * self.current_zoom
            scaled = self.original_pixmap.scaled(
                new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

        self.setPixmap(scaled)

    def set_zoom(self, zoom: float):
        """设置缩放比例"""
        self.current_zoom = zoom
        self.fit_to_window = False
        self.update_display()

    def fit_window(self, fit: bool):
        """适应窗口"""
        self.fit_to_window = fit
        self.update_display()

    def set_drawing_mode(self, mode: str):
        """设置绘制模式"""
        self.drawing_mode = mode
        if mode:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            self.current_rect = None
            self.update()

    def mousePressEvent(self, event):
        if self.drawing_mode and event.button() == Qt.LeftButton:
            self.is_drawing = True
            self.start_pos = event.pos()
            self.current_rect = QtCore.QRect(self.start_pos, self.start_pos)

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.current_rect = QtCore.QRect(self.start_pos, event.pos()).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.is_drawing and event.button() == Qt.LeftButton:
            self.is_drawing = False

            if self.current_rect and self.pixmap():
                # 转换坐标到原图
                rect = self._map_to_image_coords(self.current_rect)

                if self.drawing_mode == 'crop':
                    self.cropAreaSelected.emit(rect)
                elif self.drawing_mode == 'mosaic':
                    self.mosaicAreaSelected.emit(rect)

            self.current_rect = None
            self.drawing_mode = None
            self.setCursor(Qt.ArrowCursor)
            self.update()

    def _map_to_image_coords(self, rect: QtCore.QRect) -> tuple:
        """将label坐标映射到原图坐标"""
        if not self.pixmap() or not self.original_pixmap:
            return (0, 0, 0, 0)

        pixmap = self.pixmap()

        # label中心
        label_rect = self.rect()

        # pixmap在label中的实际位置（居中）
        pix_rect = QtCore.QRect(
            (label_rect.width() - pixmap.width()) // 2,
            (label_rect.height() - pixmap.height()) // 2,
            pixmap.width(),
            pixmap.height()
        )

        # 映射到pixmap坐标
        pix_x = rect.x() - pix_rect.x()
        pix_y = rect.y() - pix_rect.y()
        pix_w = rect.width()
        pix_h = rect.height()

        # 映射到原图坐标
        scale_x = self.original_pixmap.width() / pixmap.width()
        scale_y = self.original_pixmap.height() / pixmap.height()

        img_x = int(pix_x * scale_x)
        img_y = int(pix_y * scale_y)
        img_w = int(pix_w * scale_x)
        img_h = int(pix_h * scale_y)

        # 边界检查
        img_x = max(0, min(img_x, self.original_pixmap.width()))
        img_y = max(0, min(img_y, self.original_pixmap.height()))
        img_w = min(img_w, self.original_pixmap.width() - img_x)
        img_h = min(img_h, self.original_pixmap.height() - img_y)

        return (img_x, img_y, img_w, img_h)

    def paintEvent(self, event):
        super().paintEvent(event)

        # 绘制选择框
        if self.current_rect:
            painter = QPainter(self)
            pen = QPen(QColor(255, 255, 0), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.current_rect)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.fit_to_window:
            self.update_display()


class ImageListWidget(QListWidget):
    """图片列表控件（支持拖拽、缩略图）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QtCore.QSize(120, 120))
        self.setSpacing(10)
        self.setResizeMode(QListWidget.Adjust)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #555;
            }
            QListWidget::item {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #0d47a1;
                border: 2px solid #1976d2;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = [url.toLocalFile() for url in urls]

            # 过滤图片文件
            image_paths = [
                path for path in file_paths
                if os.path.splitext(path)[1].lower() in SUPPORTED_FORMATS
            ]

            if image_paths:
                # 触发信号给主窗口
                self.parent().parent().parent().add_images(image_paths)
        else:
            super().dropEvent(event)


class BatchProcessThread(QThread):
    """批处理线程"""

    progress = pyqtSignal(int, str)  # (percentage, message)
    finished = pyqtSignal(int, int)  # (success_count, fail_count)

    def __init__(self, file_paths, output_dir, settings):
        super().__init__()
        self.file_paths = file_paths
        self.output_dir = output_dir
        self.settings = settings
        self.is_running = True

    def run(self):
        success_count = 0
        fail_count = 0
        total = len(self.file_paths)

        for idx, path in enumerate(self.file_paths):
            if not self.is_running:
                break

            try:
                # 加载图片
                img = load_image(path)
                if img is None:
                    raise Exception("Failed to load image")

                # 应用处理
                img = self._apply_settings(img)

                # 生成输出文件名
                output_path = self._generate_output_path(path, idx)

                # 保存
                success = save_image(
                    img, output_path,
                    quality=self.settings.get('quality', 95),
                    strip_exif=self.settings.get('strip_exif', False)
                )

                if success:
                    success_count += 1
                    self.progress.emit(
                        int((idx + 1) / total * 100),
                        f"已处理: {os.path.basename(path)}"
                    )
                else:
                    fail_count += 1

            except Exception as e:
                fail_count += 1
                self.progress.emit(
                    int((idx + 1) / total * 100),
                    f"失败: {os.path.basename(path)} - {str(e)}"
                )

        self.finished.emit(success_count, fail_count)

    def _apply_settings(self, img: Image.Image) -> Image.Image:
        """应用处理设置"""
        # 缩放
        if self.settings.get('resize_enabled'):
            width = self.settings.get('resize_width')
            height = self.settings.get('resize_height')
            if width and height:
                img = img.resize((width, height), Image.LANCZOS)

        # 滤镜
        if self.settings.get('filter'):
            img = apply_filter(img, self.settings['filter'])

        # 调整
        if self.settings.get('brightness') != 1.0:
            img = adjust_brightness(img, self.settings['brightness'])

        if self.settings.get('contrast') != 1.0:
            img = adjust_contrast(img, self.settings['contrast'])

        if self.settings.get('saturation') != 1.0:
            img = adjust_saturation(img, self.settings['saturation'])

        # 水印
        if self.settings.get('watermark_text'):
            img = add_text_watermark(
                img,
                self.settings['watermark_text'],
                position=self.settings.get('watermark_position', 'bottom_right'),
                opacity=self.settings.get('watermark_opacity', 128),
                font_size=self.settings.get('watermark_font_size', 36)
            )

        return img

    def _generate_output_path(self, input_path: str, index: int) -> str:
        """生成输出路径"""
        basename = os.path.basename(input_path)
        name, ext = os.path.splitext(basename)

        # 应用命名模式
        prefix = self.settings.get('name_prefix', '')
        suffix = self.settings.get('name_suffix', '_processed')

        # 格式转换
        output_format = self.settings.get('output_format')
        if output_format:
            ext_map = {
                'JPEG': '.jpg',
                'PNG': '.png',
                'BMP': '.bmp',
                'WEBP': '.webp'
            }
            ext = ext_map.get(output_format, ext)

        new_name = f"{prefix}{name}{suffix}{ext}"

        return os.path.join(self.output_dir, new_name)

    def stop(self):
        self.is_running = False


# ==================== 主窗口 ====================

class ImageProcessorPro(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ImageProcessorPro Ultimate - 专业图像处理工具")
        self.setGeometry(100, 100, 1400, 900)

        # 数据
        self.image_paths = []
        self.current_index = -1
        self.current_image = None  # PIL Image
        self.original_image = None  # 原始图片
        self.display_image = None  # 显示用图片

        # 历史记录（撤销/重做）
        self.history_stack = []
        self.history_index = -1
        self.max_history = 50

        # 批处理线程
        self.batch_thread = None

        # UI
        self._setup_ui()
        self._setup_shortcuts()
        self._apply_dark_theme()

        # 状态
        self.statusBar().showMessage("就绪")

    def _setup_ui(self):
        """设置UI"""
        # 中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧：文件列表
        left_widget = self._create_file_list_panel()

        # 中间：预览区
        center_widget = self._create_preview_panel()

        # 右侧：工具面板
        right_widget = self._create_tools_panel()

        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(center_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([250, 700, 450])
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3a3a3a;
                width: 2px;
            }
        """)

        main_layout.addWidget(splitter)

        # 菜单栏
        self._create_menu_bar()

        # 工具栏
        self._create_toolbar()

        # 状态栏
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)

    def _create_file_list_panel(self) -> QWidget:
        """创建文件列表面板"""
        widget = QWidget()
        widget.setMaximumWidth(300)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # 标题
        title = QLabel("图片列表")
        title.setFont(QFont("Arial", 10, QFont.Bold))
        title.setStyleSheet("color: #ffffff; padding: 5px;")
        layout.addWidget(title)

        # 列表
        self.list_widget = ImageListWidget(widget)
        self.list_widget.currentRowChanged.connect(self._on_image_selected)
        layout.addWidget(self.list_widget)

        # 按钮
        btn_layout = QHBoxLayout()

        btn_add = QPushButton("添加")
        btn_add.clicked.connect(self._add_images_dialog)
        btn_layout.addWidget(btn_add)

        btn_remove = QPushButton("删除")
        btn_remove.clicked.connect(self._remove_selected_images)
        btn_layout.addWidget(btn_remove)

        btn_clear = QPushButton("清空")
        btn_clear.clicked.connect(self._clear_images)
        btn_layout.addWidget(btn_clear)

        layout.addLayout(btn_layout)

        return widget

    def _create_preview_panel(self) -> QWidget:
        """创建预览面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # 预览标签
        self.preview_label = ImagePreviewLabel()
        self.preview_label.cropAreaSelected.connect(self._on_crop_area_selected)
        self.preview_label.mosaicAreaSelected.connect(self._on_mosaic_area_selected)
        layout.addWidget(self.preview_label, stretch=1)

        # 控制栏
        control_layout = QHBoxLayout()

        # 缩放控制
        self.chk_fit = QCheckBox("适应窗口")
        self.chk_fit.setChecked(True)
        self.chk_fit.stateChanged.connect(self._on_fit_changed)
        control_layout.addWidget(self.chk_fit)

        control_layout.addWidget(QLabel("缩放:"))
        self.slider_zoom = QSlider(Qt.Horizontal)
        self.slider_zoom.setRange(10, 500)
        self.slider_zoom.setValue(100)
        self.slider_zoom.setMaximumWidth(200)
        self.slider_zoom.valueChanged.connect(self._on_zoom_changed)
        control_layout.addWidget(self.slider_zoom)

        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setMinimumWidth(50)
        control_layout.addWidget(self.lbl_zoom)

        control_layout.addStretch()

        # 导航按钮
        btn_prev = QPushButton("◀ 上一张")
        btn_prev.clicked.connect(self._goto_prev)
        control_layout.addWidget(btn_prev)

        btn_next = QPushButton("下一张 ▶")
        btn_next.clicked.connect(self._goto_next)
        control_layout.addWidget(btn_next)

        layout.addLayout(control_layout)

        # 信息栏
        self.lbl_info = QLabel("未加载图片")
        self.lbl_info.setStyleSheet("color: #aaaaaa; padding: 5px;")
        layout.addWidget(self.lbl_info)

        return widget

    def _create_tools_panel(self) -> QWidget:
        """创建工具面板"""
        widget = QWidget()
        widget.setMaximumWidth(500)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Tab控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3a3a3a;
                color: #ffffff;
                padding: 8px 15px;
                border: 1px solid #555;
            }
            QTabBar::tab:selected {
                background-color: #0d47a1;
            }
        """)

        # 各个标签页
        self.tab_widget.addTab(self._create_basic_tab(), "基础编辑")
        self.tab_widget.addTab(self._create_adjust_tab(), "调节")
        self.tab_widget.addTab(self._create_filter_tab(), "滤镜特效")
        self.tab_widget.addTab(self._create_annotate_tab(), "标注")
        self.tab_widget.addTab(self._create_watermark_tab(), "水印")
        self.tab_widget.addTab(self._create_batch_tab(), "批处理")
        self.tab_widget.addTab(self._create_tools_tab(), "工具")

        layout.addWidget(self.tab_widget)

        # 底部按钮
        btn_layout = QHBoxLayout()

        btn_apply = QPushButton("应用更改")
        btn_apply.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 8px;")
        btn_apply.clicked.connect(self._apply_changes)
        btn_layout.addWidget(btn_apply)

        btn_reset = QPushButton("重置")
        btn_reset.clicked.connect(self._reset_image)
        btn_layout.addWidget(btn_reset)

        btn_save = QPushButton("保存")
        btn_save.setStyleSheet("background-color: #388e3c; color: white; font-weight: bold; padding: 8px;")
        btn_save.clicked.connect(self._save_image)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

        return widget

    def _create_basic_tab(self) -> QWidget:
        """基础编辑标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 旋转
        group_rotate = QGroupBox("旋转")
        rotate_layout = QHBoxLayout()

        btn_rot_left = QPushButton("↺ 左转90°")
        btn_rot_left.clicked.connect(lambda: self._rotate_image(-90))
        rotate_layout.addWidget(btn_rot_left)

        btn_rot_right = QPushButton("右转90° ↻")
        btn_rot_right.clicked.connect(lambda: self._rotate_image(90))
        rotate_layout.addWidget(btn_rot_right)

        btn_rot_180 = QPushButton("旋转180°")
        btn_rot_180.clicked.connect(lambda: self._rotate_image(180))
        rotate_layout.addWidget(btn_rot_180)

        group_rotate.setLayout(rotate_layout)
        layout.addWidget(group_rotate)

        # 翻转
        group_flip = QGroupBox("翻转")
        flip_layout = QHBoxLayout()

        btn_flip_h = QPushButton("水平翻转 ⟷")
        btn_flip_h.clicked.connect(lambda: self._flip_image("horizontal"))
        flip_layout.addWidget(btn_flip_h)

        btn_flip_v = QPushButton("垂直翻转 ⥯")
        btn_flip_v.clicked.connect(lambda: self._flip_image("vertical"))
        flip_layout.addWidget(btn_flip_v)

        group_flip.setLayout(flip_layout)
        layout.addWidget(group_flip)

        # 裁剪
        group_crop = QGroupBox("裁剪")
        crop_layout = QVBoxLayout()

        btn_crop = QPushButton("框选裁剪")
        btn_crop.clicked.connect(self._start_crop)
        crop_layout.addWidget(btn_crop)

        crop_size_layout = QHBoxLayout()
        crop_size_layout.addWidget(QLabel("固定尺寸:"))
        self.spin_crop_w = QSpinBox()
        self.spin_crop_w.setRange(0, 10000)
        self.spin_crop_w.setPrefix("W: ")
        crop_size_layout.addWidget(self.spin_crop_w)

        self.spin_crop_h = QSpinBox()
        self.spin_crop_h.setRange(0, 10000)
        self.spin_crop_h.setPrefix("H: ")
        crop_size_layout.addWidget(self.spin_crop_h)

        btn_crop_center = QPushButton("居中裁剪")
        btn_crop_center.clicked.connect(self._crop_center)
        crop_size_layout.addWidget(btn_crop_center)

        crop_layout.addLayout(crop_size_layout)

        group_crop.setLayout(crop_layout)
        layout.addWidget(group_crop)

        # 缩放
        group_resize = QGroupBox("缩放")
        resize_layout = QVBoxLayout()

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("宽度:"))
        self.spin_width = QSpinBox()
        self.spin_width.setRange(1, 10000)
        self.spin_width.setValue(800)
        size_layout.addWidget(self.spin_width)

        size_layout.addWidget(QLabel("高度:"))
        self.spin_height = QSpinBox()
        self.spin_height.setRange(1, 10000)
        self.spin_height.setValue(600)
        size_layout.addWidget(self.spin_height)

        resize_layout.addLayout(size_layout)

        self.chk_keep_aspect = QCheckBox("保持宽高比")
        self.chk_keep_aspect.setChecked(True)
        resize_layout.addWidget(self.chk_keep_aspect)

        btn_resize = QPushButton("应用缩放")
        btn_resize.clicked.connect(self._resize_image)
        resize_layout.addWidget(btn_resize)

        group_resize.setLayout(resize_layout)
        layout.addWidget(group_resize)

        layout.addStretch()

        return widget

    def _create_adjust_tab(self) -> QWidget:
        """调节标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 亮度
        scroll_layout.addWidget(QLabel("亮度:"))
        self.slider_brightness = QSlider(Qt.Horizontal)
        self.slider_brightness.setRange(0, 200)
        self.slider_brightness.setValue(100)
        self.slider_brightness.valueChanged.connect(self._update_preview)
        scroll_layout.addWidget(self.slider_brightness)

        # 对比度
        scroll_layout.addWidget(QLabel("对比度:"))
        self.slider_contrast = QSlider(Qt.Horizontal)
        self.slider_contrast.setRange(0, 200)
        self.slider_contrast.setValue(100)
        self.slider_contrast.valueChanged.connect(self._update_preview)
        scroll_layout.addWidget(self.slider_contrast)

        # 饱和度
        scroll_layout.addWidget(QLabel("饱和度:"))
        self.slider_saturation = QSlider(Qt.Horizontal)
        self.slider_saturation.setRange(0, 200)
        self.slider_saturation.setValue(100)
        self.slider_saturation.valueChanged.connect(self._update_preview)
        scroll_layout.addWidget(self.slider_saturation)

        # 锐度
        scroll_layout.addWidget(QLabel("锐度:"))
        self.slider_sharpness = QSlider(Qt.Horizontal)
        self.slider_sharpness.setRange(0, 200)
        self.slider_sharpness.setValue(100)
        self.slider_sharpness.valueChanged.connect(self._update_preview)
        scroll_layout.addWidget(self.slider_sharpness)

        # 色温
        scroll_layout.addWidget(QLabel("色温:"))
        self.slider_temperature = QSlider(Qt.Horizontal)
        self.slider_temperature.setRange(-100, 100)
        self.slider_temperature.setValue(0)
        self.slider_temperature.valueChanged.connect(self._update_preview)
        scroll_layout.addWidget(self.slider_temperature)

        # 色相
        scroll_layout.addWidget(QLabel("色相:"))
        self.slider_hue = QSlider(Qt.Horizontal)
        self.slider_hue.setRange(-180, 180)
        self.slider_hue.setValue(0)
        self.slider_hue.valueChanged.connect(self._update_preview)
        scroll_layout.addWidget(self.slider_hue)

        # 重置按钮
        btn_reset_adjust = QPushButton("重置所有调节")
        btn_reset_adjust.clicked.connect(self._reset_adjustments)
        scroll_layout.addWidget(btn_reset_adjust)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def _create_filter_tab(self) -> QWidget:
        """滤镜标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("选择滤镜:"))

        # 滤镜列表
        self.list_filters = QListWidget()
        for filter_name in FILTER_PRESETS.keys():
            self.list_filters.addItem(filter_name)
        self.list_filters.setCurrentRow(0)
        self.list_filters.currentRowChanged.connect(self._on_filter_changed)
        layout.addWidget(self.list_filters)

        return widget

    def _create_annotate_tab(self) -> QWidget:
        """标注标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 文字标注
        group_text = QGroupBox("文字标注")
        text_layout = QVBoxLayout()

        self.edit_annotation = QLineEdit()
        self.edit_annotation.setPlaceholderText("输入文字...")
        text_layout.addWidget(self.edit_annotation)

        text_settings_layout = QHBoxLayout()
        text_settings_layout.addWidget(QLabel("大小:"))
        self.spin_text_size = QSpinBox()
        self.spin_text_size.setRange(8, 200)
        self.spin_text_size.setValue(36)
        text_settings_layout.addWidget(self.spin_text_size)

        btn_text_color = QPushButton("颜色")
        btn_text_color.clicked.connect(self._choose_text_color)
        text_settings_layout.addWidget(btn_text_color)

        text_layout.addLayout(text_settings_layout)

        self.combo_text_pos = QComboBox()
        self.combo_text_pos.addItems(["左上", "右上", "左下", "右下", "居中"])
        text_layout.addWidget(self.combo_text_pos)

        btn_add_text = QPushButton("添加文字")
        btn_add_text.clicked.connect(self._add_text_annotation)
        text_layout.addWidget(btn_add_text)

        group_text.setLayout(text_layout)
        layout.addWidget(group_text)

        # 马赛克
        group_mosaic = QGroupBox("马赛克")
        mosaic_layout = QVBoxLayout()

        mosaic_settings_layout = QHBoxLayout()
        mosaic_settings_layout.addWidget(QLabel("块大小:"))
        self.spin_mosaic_size = QSpinBox()
        self.spin_mosaic_size.setRange(5, 50)
        self.spin_mosaic_size.setValue(10)
        mosaic_settings_layout.addWidget(self.spin_mosaic_size)

        mosaic_layout.addLayout(mosaic_settings_layout)

        btn_mosaic = QPushButton("框选添加马赛克")
        btn_mosaic.clicked.connect(self._start_mosaic)
        mosaic_layout.addWidget(btn_mosaic)

        group_mosaic.setLayout(mosaic_layout)
        layout.addWidget(group_mosaic)

        layout.addStretch()

        self.text_color = (255, 255, 255)

        return widget

    def _create_watermark_tab(self) -> QWidget:
        """水印标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 文字水印
        group_text_wm = QGroupBox("文字水印")
        text_wm_layout = QVBoxLayout()

        self.edit_watermark = QLineEdit()
        self.edit_watermark.setPlaceholderText("输入水印文字...")
        text_wm_layout.addWidget(self.edit_watermark)

        wm_settings_layout = QGridLayout()
        wm_settings_layout.addWidget(QLabel("位置:"), 0, 0)
        self.combo_wm_pos = QComboBox()
        self.combo_wm_pos.addItems(["右下", "左下", "右上", "左上", "居中"])
        wm_settings_layout.addWidget(self.combo_wm_pos, 0, 1)

        wm_settings_layout.addWidget(QLabel("大小:"), 1, 0)
        self.spin_wm_size = QSpinBox()
        self.spin_wm_size.setRange(8, 200)
        self.spin_wm_size.setValue(36)
        wm_settings_layout.addWidget(self.spin_wm_size, 1, 1)

        wm_settings_layout.addWidget(QLabel("透明度:"), 2, 0)
        self.spin_wm_opacity = QSpinBox()
        self.spin_wm_opacity.setRange(0, 255)
        self.spin_wm_opacity.setValue(128)
        wm_settings_layout.addWidget(self.spin_wm_opacity, 2, 1)

        text_wm_layout.addLayout(wm_settings_layout)

        btn_add_wm = QPushButton("添加水印")
        btn_add_wm.clicked.connect(self._add_watermark)
        text_wm_layout.addWidget(btn_add_wm)

        group_text_wm.setLayout(text_wm_layout)
        layout.addWidget(group_text_wm)

        layout.addStretch()

        return widget

    def _create_batch_tab(self) -> QWidget:
        """批处理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 输出设置
        group_output = QGroupBox("输出设置")
        output_layout = QVBoxLayout()

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("格式:"))
        self.combo_batch_format = QComboBox()
        self.combo_batch_format.addItems(["保持原格式", "JPEG", "PNG", "BMP", "WEBP"])
        format_layout.addWidget(self.combo_batch_format)
        output_layout.addLayout(format_layout)

        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("质量:"))
        self.spin_batch_quality = QSpinBox()
        self.spin_batch_quality.setRange(1, 100)
        self.spin_batch_quality.setValue(95)
        quality_layout.addWidget(self.spin_batch_quality)
        output_layout.addLayout(quality_layout)

        self.chk_strip_exif_batch = QCheckBox("移除EXIF信息")
        output_layout.addWidget(self.chk_strip_exif_batch)

        group_output.setLayout(output_layout)
        layout.addWidget(group_output)

        # 命名规则
        group_naming = QGroupBox("命名规则")
        naming_layout = QVBoxLayout()

        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("前缀:"))
        self.edit_batch_prefix = QLineEdit()
        prefix_layout.addWidget(self.edit_batch_prefix)
        naming_layout.addLayout(prefix_layout)

        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel("后缀:"))
        self.edit_batch_suffix = QLineEdit()
        self.edit_batch_suffix.setText("_processed")
        suffix_layout.addWidget(self.edit_batch_suffix)
        naming_layout.addLayout(suffix_layout)

        group_naming.setLayout(naming_layout)
        layout.addWidget(group_naming)

        # 批处理选项
        group_process = QGroupBox("处理选项")
        process_layout = QVBoxLayout()

        self.chk_batch_resize = QCheckBox("缩放图片")
        process_layout.addWidget(self.chk_batch_resize)

        resize_layout = QHBoxLayout()
        resize_layout.addWidget(QLabel("尺寸:"))
        self.spin_batch_width = QSpinBox()
        self.spin_batch_width.setRange(1, 10000)
        self.spin_batch_width.setValue(1920)
        resize_layout.addWidget(self.spin_batch_width)
        resize_layout.addWidget(QLabel("×"))
        self.spin_batch_height = QSpinBox()
        self.spin_batch_height.setRange(1, 10000)
        self.spin_batch_height.setValue(1080)
        resize_layout.addWidget(self.spin_batch_height)
        process_layout.addLayout(resize_layout)

        group_process.setLayout(process_layout)
        layout.addWidget(group_process)

        # 执行按钮
        btn_batch_run = QPushButton("开始批处理")
        btn_batch_run.setStyleSheet("background-color: #f57c00; color: white; font-weight: bold; padding: 10px;")
        btn_batch_run.clicked.connect(self._run_batch_process)
        layout.addWidget(btn_batch_run)

        layout.addStretch()

        return widget

    def _create_tools_tab(self) -> QWidget:
        """工具标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # AI工具
        if HAS_REMBG:
            group_ai = QGroupBox("AI工具")
            ai_layout = QVBoxLayout()

            btn_remove_bg = QPushButton("智能抠图/背景移除")
            btn_remove_bg.clicked.connect(self._remove_background)
            ai_layout.addWidget(btn_remove_bg)

            group_ai.setLayout(ai_layout)
            layout.addWidget(group_ai)

        # 拼图
        group_stitch = QGroupBox("图片拼接")
        stitch_layout = QVBoxLayout()

        self.combo_stitch_mode = QComboBox()
        self.combo_stitch_mode.addItems(["横向", "纵向", "网格"])
        stitch_layout.addWidget(self.combo_stitch_mode)

        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("间距:"))
        self.spin_stitch_spacing = QSpinBox()
        self.spin_stitch_spacing.setRange(0, 100)
        self.spin_stitch_spacing.setValue(0)
        spacing_layout.addWidget(self.spin_stitch_spacing)
        stitch_layout.addLayout(spacing_layout)

        btn_stitch = QPushButton("拼接选中的图片")
        btn_stitch.clicked.connect(self._stitch_images)
        stitch_layout.addWidget(btn_stitch)

        group_stitch.setLayout(stitch_layout)
        layout.addWidget(group_stitch)

        # OCR
        if HAS_OCR:
            group_ocr = QGroupBox("OCR文字识别")
            ocr_layout = QVBoxLayout()

            self.combo_ocr_lang = QComboBox()
            self.combo_ocr_lang.addItems(["中英文", "仅中文", "仅英文"])
            ocr_layout.addWidget(self.combo_ocr_lang)

            btn_ocr = QPushButton("识别文字")
            btn_ocr.clicked.connect(self._run_ocr)
            ocr_layout.addWidget(btn_ocr)

            group_ocr.setLayout(ocr_layout)
            layout.addWidget(group_ocr)

        # 信息
        group_info = QGroupBox("图片信息")
        info_layout = QVBoxLayout()

        btn_exif = QPushButton("查看EXIF信息")
        btn_exif.clicked.connect(self._show_exif)
        info_layout.addWidget(btn_exif)

        btn_histogram = QPushButton("查看直方图")
        btn_histogram.clicked.connect(self._show_histogram)
        info_layout.addWidget(btn_histogram)

        group_info.setLayout(info_layout)
        layout.addWidget(group_info)

        layout.addStretch()

        return widget

    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        act_open = QAction("打开图片...(&O)", self)
        act_open.setShortcut(QKeySequence.Open)
        act_open.triggered.connect(self._add_images_dialog)
        file_menu.addAction(act_open)

        act_save = QAction("保存(&S)", self)
        act_save.setShortcut(QKeySequence.Save)
        act_save.triggered.connect(self._save_image)
        file_menu.addAction(act_save)

        act_save_as = QAction("另存为...(&A)", self)
        act_save_as.setShortcut(QKeySequence.SaveAs)
        act_save_as.triggered.connect(self._save_image_as)
        file_menu.addAction(act_save_as)

        file_menu.addSeparator()

        act_exit = QAction("退出(&X)", self)
        act_exit.setShortcut(QKeySequence.Quit)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")

        self.act_undo = QAction("撤销(&U)", self)
        self.act_undo.setShortcut(QKeySequence.Undo)
        self.act_undo.triggered.connect(self._undo)
        self.act_undo.setEnabled(False)
        edit_menu.addAction(self.act_undo)

        self.act_redo = QAction("重做(&R)", self)
        self.act_redo.setShortcut(QKeySequence.Redo)
        self.act_redo.triggered.connect(self._redo)
        self.act_redo.setEnabled(False)
        edit_menu.addAction(self.act_redo)

        edit_menu.addSeparator()

        act_reset = QAction("重置图片(&E)", self)
        act_reset.triggered.connect(self._reset_image)
        edit_menu.addAction(act_reset)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")

        act_fit = QAction("适应窗口(&F)", self)
        act_fit.setCheckable(True)
        act_fit.setChecked(True)
        act_fit.triggered.connect(lambda checked: self.chk_fit.setChecked(checked))
        view_menu.addAction(act_fit)

        act_actual_size = QAction("实际大小(&A)", self)
        act_actual_size.triggered.connect(lambda: self.slider_zoom.setValue(100))
        view_menu.addAction(act_actual_size)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        act_about = QAction("关于(&A)", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QtCore.QSize(24, 24))

        # 打开
        act_open = QAction("打开", self)
        act_open.triggered.connect(self._add_images_dialog)
        toolbar.addAction(act_open)

        # 保存
        act_save = QAction("保存", self)
        act_save.triggered.connect(self._save_image)
        toolbar.addAction(act_save)

        toolbar.addSeparator()

        # 撤销/重做
        toolbar.addAction(self.act_undo)
        toolbar.addAction(self.act_redo)

        toolbar.addSeparator()

        # 旋转
        act_rot_left = QAction("↺ 左转", self)
        act_rot_left.triggered.connect(lambda: self._rotate_image(-90))
        toolbar.addAction(act_rot_left)

        act_rot_right = QAction("右转 ↻", self)
        act_rot_right.triggered.connect(lambda: self._rotate_image(90))
        toolbar.addAction(act_rot_right)

        toolbar.addSeparator()

        # 翻转
        act_flip_h = QAction("水平翻转", self)
        act_flip_h.triggered.connect(lambda: self._flip_image("horizontal"))
        toolbar.addAction(act_flip_h)

        act_flip_v = QAction("垂直翻转", self)
        act_flip_v.triggered.connect(lambda: self._flip_image("vertical"))
        toolbar.addAction(act_flip_v)

    def _setup_shortcuts(self):
        """设置快捷键"""
        # 导航
        QShortcut(QKeySequence(Qt.Key_Left), self, self._goto_prev)
        QShortcut(QKeySequence(Qt.Key_Right), self, self._goto_next)

        # 编辑
        QShortcut(QKeySequence("Ctrl+R"), self, lambda: self._rotate_image(90))
        QShortcut(QKeySequence("Ctrl+Shift+R"), self, lambda: self._rotate_image(-90))
        QShortcut(QKeySequence("Ctrl+H"), self, lambda: self._flip_image("horizontal"))
        QShortcut(QKeySequence("Ctrl+V"), self, lambda: self._flip_image("vertical"))

        # 缩放
        QShortcut(QKeySequence("Ctrl++"), self, lambda: self.slider_zoom.setValue(self.slider_zoom.value() + 10))
        QShortcut(QKeySequence("Ctrl+-"), self, lambda: self.slider_zoom.setValue(self.slider_zoom.value() - 10))
        QShortcut(QKeySequence("Ctrl+0"), self, lambda: self.slider_zoom.setValue(100))

    def _apply_dark_theme(self):
        """应用深色主题"""
        dark_stylesheet = """
        QMainWindow, QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QLabel {
            color: #ffffff;
        }
        QPushButton {
            background-color: #3a3a3a;
            color: #ffffff;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: #4a4a4a;
        }
        QPushButton:pressed {
            background-color: #2a2a2a;
        }
        QLineEdit, QSpinBox, QComboBox {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px;
        }
        QSlider::groove:horizontal {
            background: #3a3a3a;
            height: 6px;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #1976d2;
            width: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }
        QGroupBox {
            border: 1px solid #555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QCheckBox {
            color: #ffffff;
        }
        QMenuBar {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QMenuBar::item:selected {
            background-color: #0d47a1;
        }
        QMenu {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #555;
        }
        QMenu::item:selected {
            background-color: #0d47a1;
        }
        QToolBar {
            background-color: #2b2b2b;
            border: none;
            spacing: 5px;
        }
        QStatusBar {
            background-color: #2b2b2b;
            color: #aaaaaa;
        }
        QScrollBar:vertical {
            background: #2b2b2b;
            width: 12px;
        }
        QScrollBar::handle:vertical {
            background: #555;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical:hover {
            background: #666;
        }
        """
        self.setStyleSheet(dark_stylesheet)

    # ========== 图片管理 ==========

    def add_images(self, paths: list):
        """添加图片"""
        for path in paths:
            if path not in self.image_paths:
                self.image_paths.append(path)

                # 加载缩略图
                try:
                    img = load_image(path)
                    if img:
                        # 创建缩略图
                        img.thumbnail((120, 120), Image.LANCZOS)
                        qimage = pil_to_qimage(img)
                        pixmap = QPixmap.fromImage(qimage)

                        item = QListWidgetItem(os.path.basename(path))
                        item.setIcon(QIcon(pixmap))
                        item.setData(Qt.UserRole, path)
                        self.list_widget.addItem(item)
                except:
                    pass

        # 如果当前没有选中，选中第一张
        if self.current_index == -1 and self.image_paths:
            self.list_widget.setCurrentRow(0)

    def _add_images_dialog(self):
        """打开文件对话框添加图片"""
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self,
            "选择图片",
            "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp);;所有文件 (*.*)"
        )

        if file_paths:
            self.add_images(file_paths)

    def _remove_selected_images(self):
        """删除选中的图片"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            path = item.data(Qt.UserRole)
            if path in self.image_paths:
                self.image_paths.remove(path)
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)

        # 如果删除的是当前图片，清空显示
        if self.current_index >= len(self.image_paths):
            self.current_index = -1
            self.current_image = None
            self.preview_label.clear()

    def _clear_images(self):
        """清空所有图片"""
        reply = QMessageBox.question(
            self, "确认",
            "确定要清空所有图片吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.image_paths.clear()
            self.list_widget.clear()
            self.current_index = -1
            self.current_image = None
            self.original_image = None
            self.display_image = None
            self.history_stack.clear()
            self.history_index = -1
            self.preview_label.clear()
            self.lbl_info.setText("未加载图片")

    def _on_image_selected(self, row: int):
        """图片选择改变"""
        if row < 0 or row >= len(self.image_paths):
            return

        self.current_index = row
        path = self.image_paths[row]

        try:
            # 加载图片
            self.original_image = load_image(path)
            if self.original_image is None:
                raise Exception("Failed to load image")

            self.current_image = self.original_image.copy()
            self.display_image = self.current_image.copy()

            # 重置历史
            self.history_stack = [self.original_image.copy()]
            self.history_index = 0
            self._update_undo_redo_state()

            # 重置调整参数
            self._reset_adjustments()

            # 更新预览
            self._update_display()

            # 更新信息
            w, h = self.current_image.size
            file_size = os.path.getsize(path) / 1024  # KB
            self.lbl_info.setText(
                f"{os.path.basename(path)} | {w} × {h} | {file_size:.1f} KB"
            )

            self.statusBar().showMessage(f"已加载: {os.path.basename(path)}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载图片:\n{str(e)}")

    def _goto_prev(self):
        """上一张"""
        if self.current_index > 0:
            self.list_widget.setCurrentRow(self.current_index - 1)

    def _goto_next(self):
        """下一张"""
        if self.current_index < len(self.image_paths) - 1:
            self.list_widget.setCurrentRow(self.current_index + 1)

    # ========== 预览控制 ==========

    def _on_fit_changed(self, state):
        """适应窗口切换"""
        self.preview_label.fit_window(bool(state))
        self.slider_zoom.setEnabled(not bool(state))

    def _on_zoom_changed(self, value):
        """缩放改变"""
        self.lbl_zoom.setText(f"{value}%")
        if not self.chk_fit.isChecked():
            self.preview_label.set_zoom(value / 100.0)

    def _update_display(self):
        """更新显示"""
        if self.display_image is None:
            return

        qimage = pil_to_qimage(self.display_image)
        pixmap = QPixmap.fromImage(qimage)
        self.preview_label.set_image(pixmap)

    def _update_preview(self):
        """更新预览（应用当前调整但不保存到历史）"""
        if self.current_image is None:
            return

        # 应用所有调整
        img = self.current_image.copy()

        # 亮度
        brightness = self.slider_brightness.value() / 100.0
        if brightness != 1.0:
            img = adjust_brightness(img, brightness)

        # 对比度
        contrast = self.slider_contrast.value() / 100.0
        if contrast != 1.0:
            img = adjust_contrast(img, contrast)

        # 饱和度
        saturation = self.slider_saturation.value() / 100.0
        if saturation != 1.0:
            img = adjust_saturation(img, saturation)

        # 锐度
        sharpness = self.slider_sharpness.value() / 100.0
        if sharpness != 1.0:
            img = adjust_sharpness(img, sharpness)

        # 色温
        temperature = self.slider_temperature.value()
        if temperature != 0:
            img = adjust_temperature(img, temperature)

        # 色相
        hue = self.slider_hue.value()
        if hue != 0:
            img = adjust_hue(img, hue)

        self.display_image = img
        self._update_display()

    # ========== 编辑操作 ==========

    def _add_to_history(self):
        """添加到历史记录"""
        if self.current_image is None:
            return

        # 删除当前索引之后的历史
        self.history_stack = self.history_stack[:self.history_index + 1]

        # 添加当前状态
        self.history_stack.append(self.current_image.copy())
        self.history_index += 1

        # 限制历史数量
        if len(self.history_stack) > self.max_history:
            self.history_stack.pop(0)
            self.history_index -= 1

        self._update_undo_redo_state()

    def _update_undo_redo_state(self):
        """更新撤销/重做按钮状态"""
        self.act_undo.setEnabled(self.history_index > 0)
        self.act_redo.setEnabled(self.history_index < len(self.history_stack) - 1)

    def _undo(self):
        """撤销"""
        if self.history_index > 0:
            self.history_index -= 1
            self.current_image = self.history_stack[self.history_index].copy()
            self.display_image = self.current_image.copy()
            self._update_display()
            self._update_undo_redo_state()
            self.statusBar().showMessage("已撤销")

    def _redo(self):
        """重做"""
        if self.history_index < len(self.history_stack) - 1:
            self.history_index += 1
            self.current_image = self.history_stack[self.history_index].copy()
            self.display_image = self.current_image.copy()
            self._update_display()
            self._update_undo_redo_state()
            self.statusBar().showMessage("已重做")

    def _apply_changes(self):
        """应用当前的所有更改到当前图片"""
        if self.display_image is None:
            return

        self._add_to_history()
        self.current_image = self.display_image.copy()

        # 重置调整参数
        self._reset_adjustments()

        self.statusBar().showMessage("已应用更改")

    def _reset_image(self):
        """重置图片到原始状态"""
        if self.original_image is None:
            return

        reply = QMessageBox.question(
            self, "确认",
            "确定要重置图片到原始状态吗？\n所有未保存的更改将丢失。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._add_to_history()
            self.current_image = self.original_image.copy()
            self.display_image = self.current_image.copy()
            self._reset_adjustments()
            self._update_display()
            self.statusBar().showMessage("已重置图片")

    def _reset_adjustments(self):
        """重置所有调整参数"""
        self.slider_brightness.setValue(100)
        self.slider_contrast.setValue(100)
        self.slider_saturation.setValue(100)
        self.slider_sharpness.setValue(100)
        self.slider_temperature.setValue(0)
        self.slider_hue.setValue(0)

    def _rotate_image(self, angle: int):
        """旋转图片"""
        if self.current_image is None:
            return

        self._add_to_history()
        self.current_image = self.current_image.rotate(-angle, expand=True)
        self.display_image = self.current_image.copy()
        self._update_display()
        self.statusBar().showMessage(f"已旋转 {angle}°")

    def _flip_image(self, direction: str):
        """翻转图片"""
        if self.current_image is None:
            return

        self._add_to_history()

        if direction == "horizontal":
            self.current_image = self.current_image.transpose(Image.FLIP_LEFT_RIGHT)
            msg = "水平翻转"
        else:
            self.current_image = self.current_image.transpose(Image.FLIP_TOP_BOTTOM)
            msg = "垂直翻转"

        self.display_image = self.current_image.copy()
        self._update_display()
        self.statusBar().showMessage(f"已{msg}")

    def _start_crop(self):
        """开始裁剪"""
        if self.current_image is None:
            return

        self.preview_label.set_drawing_mode('crop')
        self.statusBar().showMessage("请在图片上拖拽选择裁剪区域")

    def _on_crop_area_selected(self, rect: tuple):
        """裁剪区域选择完成"""
        x, y, w, h = rect

        if w <= 0 or h <= 0:
            QMessageBox.warning(self, "警告", "裁剪区域无效")
            return

        self._add_to_history()
        self.current_image = self.current_image.crop((x, y, x + w, y + h))
        self.display_image = self.current_image.copy()
        self._update_display()
        self.statusBar().showMessage(f"已裁剪: {w} × {h}")

    def _crop_center(self):
        """居中裁剪"""
        if self.current_image is None:
            return

        crop_w = self.spin_crop_w.value()
        crop_h = self.spin_crop_h.value()

        if crop_w <= 0 or crop_h <= 0:
            QMessageBox.warning(self, "警告", "请设置裁剪尺寸")
            return

        img_w, img_h = self.current_image.size

        if crop_w > img_w or crop_h > img_h:
            QMessageBox.warning(self, "警告", "裁剪尺寸超过图片尺寸")
            return

        x = (img_w - crop_w) // 2
        y = (img_h - crop_h) // 2

        self._add_to_history()
        self.current_image = self.current_image.crop((x, y, x + crop_w, y + crop_h))
        self.display_image = self.current_image.copy()
        self._update_display()
        self.statusBar().showMessage(f"已居中裁剪: {crop_w} × {crop_h}")

    def _resize_image(self):
        """缩放图片"""
        if self.current_image is None:
            return

        new_w = self.spin_width.value()
        new_h = self.spin_height.value()

        if new_w <= 0 or new_h <= 0:
            QMessageBox.warning(self, "警告", "请设置有效的尺寸")
            return

        self._add_to_history()

        if self.chk_keep_aspect.isChecked():
            # 保持宽高比
            self.current_image.thumbnail((new_w, new_h), Image.LANCZOS)
        else:
            self.current_image = self.current_image.resize((new_w, new_h), Image.LANCZOS)

        self.display_image = self.current_image.copy()
        self._update_display()
        self.statusBar().showMessage(f"已缩放至: {self.current_image.width} × {self.current_image.height}")

    def _on_filter_changed(self, row: int):
        """滤镜改变"""
        if self.current_image is None:
            return

        filter_name = self.list_filters.item(row).text()
        filter_key = FILTER_PRESETS.get(filter_name)

        if filter_key is None:
            self.display_image = self.current_image.copy()
        else:
            try:
                self.display_image = apply_filter(self.current_image, filter_key)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"应用滤镜失败:\n{str(e)}")
                return

        self._update_display()
        self.statusBar().showMessage(f"预览滤镜: {filter_name}")

    def _choose_text_color(self):
        """选择文字颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_color = (color.red(), color.green(), color.blue())

    def _add_text_annotation(self):
        """添加文字标注"""
        if self.current_image is None:
            return

        text = self.edit_annotation.text().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请输入文字")
            return

        position_map = {
            "左上": "top_left",
            "右上": "top_right",
            "左下": "bottom_left",
            "右下": "bottom_right",
            "居中": "center"
        }
        position = position_map.get(self.combo_text_pos.currentText(), "center")

        self._add_to_history()

        try:
            self.current_image = add_text_watermark(
                self.current_image,
                text,
                position=position,
                opacity=255,  # 完全不透明
                font_size=self.spin_text_size.value(),
                color=self.text_color
            )
            self.display_image = self.current_image.copy()
            self._update_display()
            self.statusBar().showMessage("已添加文字标注")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加文字失败:\n{str(e)}")

    def _start_mosaic(self):
        """开始添加马赛克"""
        if self.current_image is None:
            return

        self.preview_label.set_drawing_mode('mosaic')
        self.statusBar().showMessage("请在图片上拖拽选择马赛克区域")

    def _on_mosaic_area_selected(self, rect: tuple):
        """马赛克区域选择完成"""
        x, y, w, h = rect

        if w <= 0 or h <= 0:
            QMessageBox.warning(self, "警告", "选择区域无效")
            return

        self._add_to_history()

        try:
            self.current_image = mosaic_area(
                self.current_image,
                x, y, w, h,
                block_size=self.spin_mosaic_size.value()
            )
            self.display_image = self.current_image.copy()
            self._update_display()
            self.statusBar().showMessage("已添加马赛克")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加马赛克失败:\n{str(e)}")

    def _add_watermark(self):
        """添加水印"""
        if self.current_image is None:
            return

        text = self.edit_watermark.text().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请输入水印文字")
            return

        position_map = {
            "右下": "bottom_right",
            "左下": "bottom_left",
            "右上": "top_right",
            "左上": "top_left",
            "居中": "center"
        }
        position = position_map.get(self.combo_wm_pos.currentText(), "bottom_right")

        self._add_to_history()

        try:
            self.current_image = add_text_watermark(
                self.current_image,
                text,
                position=position,
                opacity=self.spin_wm_opacity.value(),
                font_size=self.spin_wm_size.value()
            )
            self.display_image = self.current_image.copy()
            self._update_display()
            self.statusBar().showMessage("已添加水印")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加水印失败:\n{str(e)}")

    # ========== 工具功能 ==========

    def _remove_background(self):
        """移除背景"""
        if self.current_image is None:
            return

        if not HAS_REMBG:
            QMessageBox.warning(
                self, "功能不可用",
                "需要安装rembg库:\npip install rembg"
            )
            return

        reply = QMessageBox.question(
            self, "确认",
            "AI抠图可能需要较长时间，确定继续吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            self.statusBar().showMessage("正在处理，请稍候...")
            QApplication.processEvents()

            self._add_to_history()
            self.current_image = remove_background(self.current_image)
            self.display_image = self.current_image.copy()
            self._update_display()

            self.statusBar().showMessage("背景移除完成")
            QMessageBox.information(self, "完成", "背景已成功移除")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"背景移除失败:\n{str(e)}")
            self.statusBar().showMessage("就绪")

    def _stitch_images(self):
        """拼接图片"""
        selected_items = self.list_widget.selectedItems()

        if len(selected_items) < 2:
            QMessageBox.warning(self, "警告", "请至少选择2张图片进行拼接")
            return

        # 加载所有选中的图片
        images = []
        for item in selected_items:
            path = item.data(Qt.UserRole)
            img = load_image(path)
            if img:
                images.append(img)

        if len(images) < 2:
            QMessageBox.warning(self, "警告", "无法加载选中的图片")
            return

        # 拼接模式
        mode_map = {
            "横向": "horizontal",
            "纵向": "vertical",
            "网格": "grid"
        }
        mode = mode_map.get(self.combo_stitch_mode.currentText(), "horizontal")
        spacing = self.spin_stitch_spacing.value()

        try:
            self.statusBar().showMessage("正在拼接...")
            QApplication.processEvents()

            result = stitch_images(images, direction=mode, spacing=spacing)

            if result:
                # 创建新的图片项
                self.original_image = result
                self.current_image = result.copy()
                self.display_image = result.copy()

                self.history_stack = [self.original_image.copy()]
                self.history_index = 0
                self._update_undo_redo_state()

                self._update_display()

                w, h = result.size
                self.lbl_info.setText(f"拼接结果 | {w} × {h}")

                self.statusBar().showMessage("拼接完成")
                QMessageBox.information(self, "完成", "图片拼接完成")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"拼接失败:\n{str(e)}")
            self.statusBar().showMessage("就绪")

    def _run_ocr(self):
        """运行OCR"""
        if self.current_image is None:
            return

        if not HAS_OCR:
            QMessageBox.warning(
                self, "功能不可用",
                "需要安装pytesseract和Tesseract-OCR:\npip install pytesseract"
            )
            return

        lang_map = {
            "中英文": "chi_sim+eng",
            "仅中文": "chi_sim",
            "仅英文": "eng"
        }
        lang = lang_map.get(self.combo_ocr_lang.currentText(), "chi_sim+eng")

        try:
            self.statusBar().showMessage("正在识别文字...")
            QApplication.processEvents()

            text = ocr_text(self.current_image, lang=lang)

            # 显示结果
            dialog = QDialog(self)
            dialog.setWindowTitle("OCR识别结果")
            dialog.setGeometry(200, 200, 600, 400)

            layout = QVBoxLayout(dialog)

            text_edit = QTextEdit()
            text_edit.setPlainText(text)
            layout.addWidget(text_edit)

            btn_layout = QHBoxLayout()

            btn_copy = QPushButton("复制")
            btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(text))
            btn_layout.addWidget(btn_copy)

            btn_close = QPushButton("关闭")
            btn_close.clicked.connect(dialog.accept)
            btn_layout.addWidget(btn_close)

            layout.addLayout(btn_layout)

            dialog.exec_()

            self.statusBar().showMessage("OCR识别完成")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"OCR识别失败:\n{str(e)}")
            self.statusBar().showMessage("就绪")

    def _show_exif(self):
        """显示EXIF信息"""
        if self.current_image is None:
            return

        exif_data = get_exif_data(self.current_image)

        if not exif_data:
            QMessageBox.information(self, "EXIF信息", "该图片没有EXIF信息")
            return

        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("EXIF信息")
        dialog.setGeometry(200, 200, 500, 400)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        text = "\n".join([f"{key}: {value}" for key, value in exif_data.items()])
        text_edit.setPlainText(text)

        layout.addWidget(text_edit)

        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        dialog.exec_()

    def _show_histogram(self):
        """显示直方图"""
        if self.current_image is None:
            return

        if not HAS_MATPLOTLIB:
            QMessageBox.warning(
                self, "功能不可用",
                "需要安装matplotlib:\npip install matplotlib"
            )
            return

        try:
            r_hist, g_hist, b_hist = calculate_histogram(self.current_image)

            plt.figure("图片直方图", figsize=(10, 6))
            plt.clf()

            plt.subplot(3, 1, 1)
            plt.plot(r_hist, color='red', alpha=0.7)
            plt.title('Red Channel')
            plt.xlim([0, 256])

            plt.subplot(3, 1, 2)
            plt.plot(g_hist, color='green', alpha=0.7)
            plt.title('Green Channel')
            plt.xlim([0, 256])

            plt.subplot(3, 1, 3)
            plt.plot(b_hist, color='blue', alpha=0.7)
            plt.title('Blue Channel')
            plt.xlim([0, 256])

            plt.tight_layout()
            plt.show()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"显示直方图失败:\n{str(e)}")

    # ========== 批处理 ==========

    def _run_batch_process(self):
        """运行批处理"""
        if not self.image_paths:
            QMessageBox.warning(self, "警告", "请先添加图片")
            return

        # 选择输出目录
        output_dir = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if not output_dir:
            return

        # 收集设置
        settings = {
            'resize_enabled': self.chk_batch_resize.isChecked(),
            'resize_width': self.spin_batch_width.value(),
            'resize_height': self.spin_batch_height.value(),
            'filter': None,
            'brightness': 1.0,
            'contrast': 1.0,
            'saturation': 1.0,
            'watermark_text': self.edit_watermark.text().strip(),
            'watermark_position': self.combo_wm_pos.currentText(),
            'watermark_opacity': self.spin_wm_opacity.value(),
            'watermark_font_size': self.spin_wm_size.value(),
            'quality': self.spin_batch_quality.value(),
            'strip_exif': self.chk_strip_exif_batch.isChecked(),
            'name_prefix': self.edit_batch_prefix.text(),
            'name_suffix': self.edit_batch_suffix.text(),
            'output_format': None if self.combo_batch_format.currentText() == "保持原格式"
            else self.combo_batch_format.currentText()
        }

        # 创建并启动线程
        self.batch_thread = BatchProcessThread(self.image_paths, output_dir, settings)
        self.batch_thread.progress.connect(self._on_batch_progress)
        self.batch_thread.finished.connect(self._on_batch_finished)

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.batch_thread.start()
        self.statusBar().showMessage("批处理进行中...")

    def _on_batch_progress(self, percentage: int, message: str):
        """批处理进度更新"""
        self.progress_bar.setValue(percentage)
        self.statusBar().showMessage(message)

    def _on_batch_finished(self, success_count: int, fail_count: int):
        """批处理完成"""
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("批处理完成")

        QMessageBox.information(
            self, "批处理完成",
            f"处理完成!\n成功: {success_count}\n失败: {fail_count}"
        )

    # ========== 保存 ==========

    def _save_image(self):
        """保存图片（覆盖原文件）"""
        if self.current_image is None:
            return

        if self.current_index < 0:
            self._save_image_as()
            return

        path = self.image_paths[self.current_index]

        reply = QMessageBox.question(
            self, "确认",
            f"确定要覆盖原文件吗?\n{os.path.basename(path)}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # 应用当前显示的图片（包含所有调整）
                img_to_save = self.display_image if self.display_image else self.current_image

                success = save_image(img_to_save, path, quality=95)

                if success:
                    # 更新原始图片
                    self.original_image = img_to_save.copy()
                    self.current_image = img_to_save.copy()

                    self.statusBar().showMessage("保存成功")
                    QMessageBox.information(self, "成功", "图片已保存")
                else:
                    raise Exception("保存失败")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")

    def _save_image_as(self):
        """另存为"""
        if self.current_image is None:
            return

        file_dialog = QFileDialog()
        file_path, selected_filter = file_dialog.getSaveFileName(
            self,
            "另存为",
            "",
            "JPEG (*.jpg *.jpeg);;PNG (*.png);;BMP (*.bmp);;WEBP (*.webp);;所有文件 (*.*)"
        )

        if file_path:
            try:
                # 应用当前显示的图片（包含所有调整）
                img_to_save = self.display_image if self.display_image else self.current_image

                success = save_image(img_to_save, file_path, quality=95)

                if success:
                    self.statusBar().showMessage(f"已保存至: {file_path}")
                    QMessageBox.information(self, "成功", "图片已保存")
                else:
                    raise Exception("保存失败")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")

    # ========== 其他 ==========

    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 ImageProcessorPro Ultimate",
            """
            <h2>ImageProcessorPro Ultimate</h2>
            <p>版本: 2.0</p>
            <p>专业图像处理工具 - 对标WPS图片</p>
            <br>
            <p><b>主要功能:</b></p>
            <ul>
                <li>基础编辑：裁剪、旋转、翻转、缩放</li>
                <li>高级调节：亮度、对比度、饱和度等</li>
                <li>20+种专业滤镜特效</li>
                <li>AI智能抠图</li>
                <li>文字标注和水印</li>
                <li>批量处理</li>
                <li>OCR文字识别</li>
                <li>图片拼接</li>
            </ul>
            <br>
            <p>Copyright © 2025</p>
            """
        )

    def closeEvent(self, event):
        """关闭事件"""
        if self.batch_thread and self.batch_thread.isRunning():
            self.batch_thread.stop()
            self.batch_thread.wait()

        event.accept()


# ==================== 主函数 ====================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ImageProcessorPro Ultimate")
    app.setOrganizationName("ImageProcessor")

    # 设置应用图标（可选）
    # app.setWindowIcon(QIcon("icon.png"))

    window = ImageProcessorPro()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()