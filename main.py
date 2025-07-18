import sys
import os
import glob
import yaml
import time
import cv2
import numpy as np

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QGraphicsScene, QGraphicsPixmapItem
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.uic import loadUi


class ImageShrinkerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("ui/image_shrinker.ui", self)

        # QAction 연결 (View → Main / Preferences)
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

        # 설정 불러오기
        self.load_settings()

        # 초기 상태
        self.progressBar.setFormat("0/0 (0%)")
        self.progressBar.setValue(0)
        self.image_paths = []

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
            self.progressBar.setMaximum(1)
            self.progressBar.setValue(0)
            self.progressBar.setFormat("0/0 (0%)")
            return

        exts = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif']
        self.image_paths = []
        for ext in exts:
            self.image_paths.extend(glob.glob(os.path.join(folder, ext)))

        total = len(self.image_paths)
        if total == 0:
            self.progressBar.setMaximum(1)
            self.progressBar.setValue(0)
            self.progressBar.setFormat("0/0 (0%)")
            return

        self.progressBar.setMaximum(total)
        self.progressBar.setFormat(f"0/{total} (%p%)")
        self.logBrowser.append(f"총 {total} 개의 이미지가 발견되었습니다.")

    def convert_images(self):
        width = int(self.imageWidth.text()) if self.imageWidth.text().isdigit() else 256
        height = int(self.imageHeight.text()) if self.imageHeight.text().isdigit() else 256
        output_dir = self.dirResult.text()
        os.makedirs(output_dir, exist_ok=True)

        total = len(self.image_paths)
        for i, path in enumerate(self.image_paths):
            img = cv2.imread(path)
            h, w = img.shape[:2]

            # 정사각형 만들기 위해 패딩
            size = max(w, h)
            delta_w = size - w
            delta_h = size - h
            top, bottom = delta_h // 2, delta_h - delta_h // 2
            left, right = delta_w // 2, delta_w - delta_w // 2
            color = [255, 255, 255]
            squared = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)

            resized = cv2.resize(squared, (width, height), interpolation=cv2.INTER_AREA)

            # 저장
            filename = os.path.basename(path)
            result_path = os.path.join(output_dir, filename)
            cv2.imwrite(result_path, resized)

            # QImage 변환
            original_qimage = self.cv2_to_qimage(img)
            result_qimage = self.cv2_to_qimage(resized)

            self.update_progress(i + 1, total, filename, original_qimage, result_qimage)

            if self.checkBox.isChecked():
                QApplication.processEvents()
                time.sleep(3)

        self.logBrowser.append("모든 이미지 변환이 완료되었습니다.")

    def update_progress(self, current, total, filename, original_qimage, result_qimage):
        self.progressBar.setMaximum(total)
        self.progressBar.setValue(current)
        self.progressBar.setFormat(f"{current}/{total} (%p%)")

        if self.checkBox.isChecked():
            # 원본 이미지 표시
            scene_original = QGraphicsScene()
            pixmap_original = QPixmap.fromImage(original_qimage).scaled(
                self.graphicsViewOriginal.size(), Qt.AspectRatioMode.KeepAspectRatio)
            scene_original.addItem(QGraphicsPixmapItem(pixmap_original))
            self.graphicsViewOriginal.setScene(scene_original)

            # 결과 이미지 표시
            scene_result = QGraphicsScene()
            pixmap_result = QPixmap.fromImage(result_qimage).scaled(
                self.graphicsViewResult.size(), Qt.AspectRatioMode.KeepAspectRatio)
            scene_result.addItem(QGraphicsPixmapItem(pixmap_result))
            self.graphicsViewResult.setScene(scene_result)

        self.logBrowser.append(f"[{current}/{total}] 변환 완료: {filename}")

    def cv2_to_qimage(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        return QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

    def save_settings(self):
        data = {
            "input_dir": self.dirOriginal.text(),
            "output_dir": self.dirResult.text(),
            "width": self.imageWidth.text(),
            "height": self.imageHeight.text(),
            "show_process": self.checkBox.isChecked()
        }
        os.makedirs("params", exist_ok=True)
        with open("params/setting.yaml", "w") as f:
            yaml.dump(data, f, allow_unicode=True)

        QMessageBox.information(self, "저장", "설정이 저장되었습니다.")

    def load_settings(self):
        if not os.path.exists("params/setting.yaml"):
            return
        with open("params/setting.yaml", "r") as f:
            data = yaml.safe_load(f)

        self.dirOriginal.setText(data.get("input_dir", ""))
        self.dirResult.setText(data.get("output_dir", ""))
        self.imageWidth.setText(str(data.get("width", "")))
        self.imageHeight.setText(str(data.get("height", "")))
        self.checkBox.setChecked(data.get("show_process", False))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageShrinkerUI()
    window.show()
    sys.exit(app.exec())
