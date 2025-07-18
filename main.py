import sys
import os
import glob
import yaml
import time
import cv2
import numpy as np

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QGraphicsScene, QGraphicsPixmapItem
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.uic import loadUi


class ImageShrinkerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("ui/image_shrinker.ui", self)

        # QAction 연결
        self.actionViewMain.triggered.connect(
            lambda: self.stackedWidget.setCurrentWidget(self.page_3))
        self.actionViewPreferences.triggered.connect(
            lambda: self.stackedWidget.setCurrentWidget(self.page_4))

        # 버튼 연결
        self.loadImage.clicked.connect(self.load_images)
        self.convertImage.clicked.connect(self.convert_images)
        self.browseOriginalDir.clicked.connect(self.select_input_dir)
        self.browseResultDir.clicked.connect(self.select_output_dir)
        self.saveSetting.clicked.connect(self.save_settings)

        # 상태 초기화
        self.image_paths = []
        self.progressBar.setFormat("0/0 (0%)")
        self.progressBar.setValue(0)

        # 설정 불러오기
        self.load_settings()

    def select_input_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "원본 이미지 폴더 선택", "./")
        if folder:
            self.dirOriginal.setText(folder)

    def select_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "결과 이미지 폴더 선택", "./")
        if folder:
            self.dirResult.setText(folder)

    def load_images(self):
        folder = self.dirOriginal.text()
        if not os.path.isdir(folder):
            self.logBrowser.append("경로가 유효하지 않습니다.")
            return

        exts = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif']
        self.image_paths = [img for ext in exts for img in glob.glob(os.path.join(folder, ext))]
        total = len(self.image_paths)
        self.progressBar.setMaximum(total if total > 0 else 1)
        self.progressBar.setValue(0)
        self.progressBar.setFormat(f"0/{total} (%p%)")
        self.logBrowser.append(
            f"총 {total}개의 이미지가 발견되었습니다." if total > 0 else "이미지가 없습니다.")

    def convert_images(self):
        width = int(self.imageWidth.text()) if self.imageWidth.text().isdigit() else 256
        height = int(self.imageHeight.text()) if self.imageHeight.text().isdigit() else 256
        output_dir = self.dirResult.text()
        os.makedirs(output_dir, exist_ok=True)

        total = len(self.image_paths)
        for i, path in enumerate(self.image_paths):
            img = cv2.imread(path)
            h, w = img.shape[:2]

            method = self.get_resize_method()

            if method == "padding_white":
                padded = self.add_padding(img, [255, 255, 255])
            elif method == "padding_bg":
                padded = self.add_color_padding(img)
            elif method == "crop":
                padded = self.crop_center(img)
            else:  # resize
                padded = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)

            resized = cv2.resize(padded, (width, height), interpolation=cv2.INTER_AREA)
            filename = os.path.basename(path)
            result_path = os.path.join(output_dir, filename)
            cv2.imwrite(result_path, resized)

            self.update_progress(
                i + 1, total, filename, self.cv2_to_qimage(img), self.cv2_to_qimage(resized))

            if self.checkBox.isChecked():
                QApplication.processEvents()
                time.sleep(3)

        self.logBrowser.append("모든 이미지 변환이 완료되었습니다.")

    def add_padding(self, img, color):
        h, w = img.shape[:2]
        size = max(h, w)
        delta_w = size - w
        delta_h = size - h
        top, bottom = delta_h // 2, delta_h - delta_h // 2
        left, right = delta_w // 2, delta_w - delta_w // 2
        return cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)

    def add_color_padding(self, img):
        h, w = img.shape[:2]
        corners = [
            img[0:10, 0:10],
            img[0:10, -10:],
            img[-10:, 0:10],
            img[-10:, -10:]
        ]
        avgs = [np.mean(corner, axis=(0, 1)) for corner in corners]
        max_diff = np.max([np.abs(avgs[0] - avg).max() for avg in avgs[1:]])
        color = [255, 255, 255] if max_diff > 10 else [int(c) for c in np.mean(avgs, axis=0)]
        return self.add_padding(img, color)

    def crop_center(self, img):
        h, w = img.shape[:2]
        size = min(h, w)
        y1 = (h - size) // 2
        x1 = (w - size) // 2
        return img[y1:y1 + size, x1:x1 + size]

    def get_resize_method(self):
        if self.radioButtonPaddingWhite.isChecked():
            return "padding_white"
        elif self.radioButtonPaddingBg.isChecked():
            return "padding_bg"
        elif self.radioButtonCrop.isChecked():
            return "crop"
        else:
            return "resize"

    def update_progress(self, current, total, filename, original_qimage, result_qimage):
        self.progressBar.setMaximum(total)
        self.progressBar.setValue(current)
        self.progressBar.setFormat(f"{current}/{total} (%p%)")

        if self.checkBox.isChecked():
            scene_original = QGraphicsScene()
            scene_result = QGraphicsScene()
            pixmap_original = QPixmap.fromImage(original_qimage).scaled(
                self.graphicsViewOriginal.size(), Qt.AspectRatioMode.KeepAspectRatio)
            pixmap_result = QPixmap.fromImage(result_qimage).scaled(
                self.graphicsViewResult.size(), Qt.AspectRatioMode.KeepAspectRatio)
            scene_original.addItem(QGraphicsPixmapItem(pixmap_original))
            scene_result.addItem(QGraphicsPixmapItem(pixmap_result))
            self.graphicsViewOriginal.setScene(scene_original)
            self.graphicsViewResult.setScene(scene_result)

        self.logBrowser.append(f"[{current}/{total}] 변환 완료: {filename}")

    def cv2_to_qimage(self, img):
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        return QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)

    def save_settings(self):
        data = {
            "input_dir": self.dirOriginal.text(),
            "output_dir": self.dirResult.text(),
            "width": self.imageWidth.text(),
            "height": self.imageHeight.text(),
            "show_process": self.checkBox.isChecked(),
            "resize_method": self.get_resize_method()
        }
        os.makedirs("params", exist_ok=True)
        with open("params/setting.yaml", "w") as f:
            yaml.dump(data, f, allow_unicode=True)
        QMessageBox.information(self, "저장", "설정이 저장되었습니다.")
        self.load_settings()

    def load_settings(self):
        if not os.path.exists("params/setting.yaml"):
            self.logBrowser.append("설정 파일이 존재하지 않습니다.")
            return
        with open("params/setting.yaml", "r") as f:
            data = yaml.safe_load(f)

        self.dirOriginal.setText(data.get("input_dir", ""))
        self.dirResult.setText(data.get("output_dir", ""))
        self.imageWidth.setText(str(data.get("width", "")))
        self.imageHeight.setText(str(data.get("height", "")))
        self.checkBox.setChecked(data.get("show_process", False))

        method = data.get("resize_method", "resize")
        method_map = {
            "padding_white": "여백 채우기(흰색)",
            "padding_bg": "여백 채우기(배경색)",
            "crop": "중앙에 맞춰 자르기",
            "resize": "보정 없음(찌그러질 수 있음)"
        }
        getattr(self, {
            "padding_white": "radioButtonPaddingWhite",
            "padding_bg": "radioButtonPaddingBg",
            "crop": "radioButtonCrop",
            "resize": "radioButtonResize"
        }[method]).setChecked(True)

        # 상세 로그 출력
        self.logBrowser.append("설정 파일 로드 완료:")
        self.logBrowser.append(f"  원본 이미지 경로: {data.get('input_dir', '')}")
        self.logBrowser.append(f"  결과 이미지 경로: {data.get('output_dir', '')}")
        self.logBrowser.append(f"  결과 크기: {data.get('width', '')} x {data.get('height', '')}")
        self.logBrowser.append(
            f"  과정 시각화: {'예' if data.get('show_process', False) else '아니오'}")
        self.logBrowser.append(f"  정사각형 보정 방식: {method_map.get(method, '알 수 없음')}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageShrinkerUI()
    window.show()
    sys.exit(app.exec())
