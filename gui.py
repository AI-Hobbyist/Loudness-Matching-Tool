import sys
import json
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QMessageBox, QProgressBar, QDialog, QComboBox
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from audio_processor import process_audio

__version__ = "1.1"


class Worker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, input_dir, output_dir, target_loudness, loudness_type):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.target_loudness = target_loudness
        self.loudness_type = loudness_type

    def run(self):
        process_audio(self.input_dir, self.output_dir,
                      self.target_loudness, self.loudness_type, self.update_progress)
        self.finished.emit()

    def update_progress(self, value):
        self.progress.emit(value)


class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("输出设置")
        self.config = self.load_config()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.export_format_label = QLabel("音频输出格式:")
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["wav", "flac", "mp3"])
        self.export_format_combo.setCurrentText(self.config["export_format"])

        self.bitrate_label = QLabel("输出MP3比特率(kbps):")
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["128", "192", "256", "320"])
        self.bitrate_combo.setCurrentText(str(self.config["mp3_bitrate"]))

        self.ffmpeg_sample_rate_label = QLabel("输出音频采样率:")
        self.ffmpeg_sample_rate_combo = QComboBox()
        self.ffmpeg_sample_rate_combo.addItems(["32000", "44100", "48000"])
        self.ffmpeg_sample_rate_combo.setCurrentText(
            str(self.config["ffmpeg_sample_rate"]))

        self.ffmpeg_bit_depth_label = QLabel("输出音频位深度:")
        self.ffmpeg_bit_depth_combo = QComboBox()
        self.ffmpeg_bit_depth_combo.addItems(["16", "24", "32"])
        self.ffmpeg_bit_depth_combo.setCurrentText(
            str(self.config["ffmpeg_bit_depth"]))

        self.setting_description_label = QLabel(
            "<b>说明:</b><br>选择wav格式导出时, 若原始音频格式为wav, 则会保持原始采样率和位深度进行导出")
        self.setting_description_label.setWordWrap(True)

        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_settings)

        layout.addWidget(self.export_format_label)
        layout.addWidget(self.export_format_combo)
        layout.addWidget(self.bitrate_label)
        layout.addWidget(self.bitrate_combo)
        layout.addWidget(self.ffmpeg_sample_rate_label)
        layout.addWidget(self.ffmpeg_sample_rate_combo)
        layout.addWidget(self.ffmpeg_bit_depth_label)
        layout.addWidget(self.ffmpeg_bit_depth_combo)
        layout.addWidget(self.setting_description_label)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

        self.setFixedWidth(200)
        self.setFixedHeight(300)

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "export_format": "mp3",
                "mp3_bitrate": 192,
                "ffmpeg_sample_rate": 44100,
                "ffmpeg_bit_depth": 24
            }

    def save_settings(self):
        self.config["export_format"] = self.export_format_combo.currentText()
        self.config["mp3_bitrate"] = int(self.bitrate_combo.currentText())
        self.config["ffmpeg_sample_rate"] = int(
            self.ffmpeg_sample_rate_combo.currentText())
        self.config["ffmpeg_bit_depth"] = int(
            self.ffmpeg_bit_depth_combo.currentText())
        with open("config.json", "w") as f:
            json.dump(self.config, f)
        self.accept()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("响度匹配小工具"+" v"+__version__)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.input_dir_label = QLabel("选择音频输入文件夹:")
        self.input_dir_lineEdit = QLineEdit()
        self.input_dir_button = QPushButton("浏览")
        self.input_dir_button.clicked.connect(self.browse_input_dir)

        self.output_dir_label = QLabel("选择音频输出文件夹:")
        self.output_dir_lineEdit = QLineEdit()
        self.output_dir_button = QPushButton("浏览")
        self.output_dir_button.clicked.connect(self.browse_output_dir)

        self.loudness_type_label = QLabel("选择匹配方式:")
        self.loudness_type_combo = QComboBox()
        self.loudness_type_combo.addItem("ITU-R BS.1770 (LUFS)")
        self.loudness_type_combo.addItem("平均响度 (dBFS)")
        self.loudness_type_combo.addItem("最大峰值 (dBFS)")
        self.loudness_type_combo.addItem("总计 RMS (dB)")

        self.target_loudness_label = QLabel("目标响度数值:")
        self.target_loudness_lineEdit = QLineEdit()
        self.target_loudness_lineEdit.setValidator(QDoubleValidator())
        self.target_loudness_lineEdit.setText("-23")

        self.process_button = QPushButton("开始处理")
        self.process_button.clicked.connect(self.process)

        self.settings_button = QPushButton("输出设置")
        self.settings_button.clicked.connect(self.open_settings)

        self.progress_bar = QProgressBar()

        layout.addWidget(self.input_dir_label)
        layout.addWidget(self.input_dir_lineEdit)
        layout.addWidget(self.input_dir_button)
        layout.addWidget(self.output_dir_label)
        layout.addWidget(self.output_dir_lineEdit)
        layout.addWidget(self.output_dir_button)
        layout.addWidget(self.loudness_type_label)
        layout.addWidget(self.loudness_type_combo)
        layout.addWidget(self.target_loudness_label)
        layout.addWidget(self.target_loudness_lineEdit)
        layout.addWidget(self.process_button)
        layout.addWidget(self.settings_button)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        self.setFixedWidth(300)
        self.setFixedHeight(350)

    def browse_input_dir(self):
        input_dir = QFileDialog.getExistingDirectory(
            self, "Select Input Directory")
        if input_dir:
            self.input_dir_lineEdit.setText(input_dir)

    def browse_output_dir(self):
        output_dir = QFileDialog.getExistingDirectory(
            self, "Select Output Directory")
        if output_dir:
            self.output_dir_lineEdit.setText(output_dir)

    def process(self):
        input_dir = self.input_dir_lineEdit.text()
        output_dir = self.output_dir_lineEdit.text()
        if not input_dir or not output_dir:
            QMessageBox.critical(self, "错误", "请选择文件夹目录!")
            return
        if not os.path.exists(input_dir) or not os.path.exists(output_dir):
            QMessageBox.critical(self, "错误", "请选择正确的文件夹目录!")
            return
        if self.target_loudness_lineEdit.text() == "":
            QMessageBox.critical(self, "错误", "请输入目标响度!")
            return
        target_loudness = float(self.target_loudness_lineEdit.text())
        if target_loudness > 0 or target_loudness < -48:
            QMessageBox.critical(self, "错误", "响度数值输入错误! 范围: -48~0")
            return
        loudness_type = self.loudness_type_combo.currentText()

        self.worker = Worker(input_dir, output_dir,
                             target_loudness, loudness_type)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(
            lambda: QMessageBox.information(self, "完成", "处理完成！"))
        self.worker.start()

    def open_settings(self):
        settings_window = SettingsWindow(self)
        settings_window.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
