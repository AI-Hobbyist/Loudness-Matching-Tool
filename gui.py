import sys
import json
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QMessageBox, QProgressBar, QDialog, QComboBox, QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from audio_processor import process_audio

import json

__version__ = "1.3"


class LanguageManager:
    def __init__(self):
        self.current_language = "zh_HANS"
        self.languages = {
            "en": "English",
            "zh_HANS": "简体中文",
            "zh_HANT": "繁體中文"
        }
        self.translations = {}
        self.load_all_languages()
    
    def load_all_languages(self):
        """Load all language files"""
        for lang_code in self.languages.keys():
            try:
                with open(f"lang/{lang_code}.json", "r", encoding="utf-8") as f:
                    self.translations[lang_code] = json.load(f)
            except FileNotFoundError:
                print(f"Warning: Language file {lang_code}.json not found")
                self.translations[lang_code] = {}
    
    def set_language(self, lang_code):
        """Set the current language"""
        if lang_code in self.languages:
            self.current_language = lang_code
            return True
        return False
    
    def get_text(self, key, default=None):
        """Get translated text for the given key"""
        if default is None:
            default = key
        return self.translations.get(self.current_language, {}).get(key, default)
    
    def get_language_name(self, lang_code):
        """Get the display name for a language code"""
        return self.languages.get(lang_code, lang_code)


# Global language manager instance
lang_manager = LanguageManager()


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
        self.config = self.load_config()
        self.initUI()
        self.update_language()

    def initUI(self):
        layout = QVBoxLayout()

        self.export_format_label = QLabel("Audio Output Format:")
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["wav", "flac", "mp3"])
        self.export_format_combo.setCurrentText(self.config["export_format"])

        self.bitrate_label = QLabel("Output MP3 Bitrate (kbps):")
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["128", "192", "256", "320"])
        self.bitrate_combo.setCurrentText(str(self.config["mp3_bitrate"]))

        self.ffmpeg_sample_rate_label = QLabel("Output Audio Sample Rate:")
        self.ffmpeg_sample_rate_combo = QComboBox()
        self.ffmpeg_sample_rate_combo.addItems(["32000", "44100", "48000"])
        self.ffmpeg_sample_rate_combo.setCurrentText(
            str(self.config["ffmpeg_sample_rate"]))

        self.ffmpeg_bit_depth_label = QLabel("Output Audio Bit Depth:")
        self.ffmpeg_bit_depth_combo = QComboBox()
        self.ffmpeg_bit_depth_combo.addItems(["16", "24", "32"])
        self.ffmpeg_bit_depth_combo.setCurrentText(
            str(self.config["ffmpeg_bit_depth"]))

        self.setting_description_label = QLabel(
            "<b>Note:</b><br>When exporting in wav format, if the original audio format is wav, the original sample rate and bit depth will be maintained during export")
        self.setting_description_label.setWordWrap(True)

        self.save_button = QPushButton("Save")
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
        self.setFixedWidth(250)
        self.setFixedHeight(300)

    def update_language(self):
        """Update all text elements with current language"""
        self.setWindowTitle(lang_manager.get_text("output_settings_window_title"))
        self.export_format_label.setText(lang_manager.get_text("output_format_label"))
        self.bitrate_label.setText(lang_manager.get_text("bitrate_label"))
        self.ffmpeg_sample_rate_label.setText(lang_manager.get_text("ffmpeg_sample_rate_label"))
        self.ffmpeg_bit_depth_label.setText(lang_manager.get_text("ffmpeg_bit_depth_label"))
        self.setting_description_label.setText(lang_manager.get_text("setting_description_label"))
        self.save_button.setText(lang_manager.get_text("save_button"))

    def load_config(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                # Set language from config if available
                if "language" in config:
                    lang_manager.set_language(config["language"])
                return config
        except FileNotFoundError:
            return {
                "export_format": "mp3",
                "mp3_bitrate": 192,
                "ffmpeg_sample_rate": 44100,
                "ffmpeg_bit_depth": 24,
                "language": "en"
            }

    def save_settings(self):
        self.config["export_format"] = self.export_format_combo.currentText()
        self.config["mp3_bitrate"] = int(self.bitrate_combo.currentText())
        self.config["ffmpeg_sample_rate"] = int(
            self.ffmpeg_sample_rate_combo.currentText())
        self.config["ffmpeg_bit_depth"] = int(
            self.ffmpeg_bit_depth_combo.currentText())
        self.config["language"] = lang_manager.current_language
        with open("config.json", "w") as f:
            json.dump(self.config, f)
        self.accept()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.update_language()

    def initUI(self):
        layout = QVBoxLayout()

        # Language selection
        lang_layout = QHBoxLayout()
        self.language_label = QLabel("Language:")
        self.language_combo = QComboBox()
        for lang_code, lang_name in lang_manager.languages.items():
            self.language_combo.addItem(lang_name, lang_code)
        # Set current language
        current_index = self.language_combo.findData(lang_manager.current_language)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.language_label)
        lang_layout.addWidget(self.language_combo)
        layout.addLayout(lang_layout)

        self.input_dir_label = QLabel("Select Audio Input Folder:")
        self.input_dir_lineEdit = QLineEdit()
        self.input_dir_button = QPushButton("Browse")
        self.input_dir_button.clicked.connect(self.browse_input_dir)

        self.output_dir_label = QLabel("Select Audio Output Folder:")
        self.output_dir_lineEdit = QLineEdit()
        self.output_dir_button = QPushButton("Browse")
        self.output_dir_button.clicked.connect(self.browse_output_dir)

        self.loudness_type_label = QLabel("Select Matching Method:")
        self.loudness_type_combo = QComboBox()
        self.loudness_type_combo.addItem("ITU-R BS.1770 (LUFS)")
        self.loudness_type_combo.addItem("Average Loudness (dBFS)")
        self.loudness_type_combo.addItem("Maximum Peak (dBFS)")
        self.loudness_type_combo.addItem("Total RMS (dB)")

        self.target_loudness_label = QLabel("Target Loudness Value:")
        self.target_loudness_lineEdit = QLineEdit()
        self.target_loudness_lineEdit.setValidator(QDoubleValidator())
        self.target_loudness_lineEdit.setText("-23")

        self.process_button = QPushButton("Start Processing")
        self.process_button.clicked.connect(self.process)

        self.settings_button = QPushButton("Output Settings")
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
        self.setFixedHeight(380)

    def update_language(self):
        """Update all text elements with current language"""
        self.setWindowTitle(lang_manager.get_text("main_window_title") + " v" + __version__)
        self.language_label.setText(lang_manager.get_text("language_label"))
        self.input_dir_label.setText(lang_manager.get_text("input_dir_label"))
        self.output_dir_label.setText(lang_manager.get_text("output_dir_label"))
        self.input_dir_button.setText(lang_manager.get_text("browse_button"))
        self.output_dir_button.setText(lang_manager.get_text("browse_button"))
        self.loudness_type_label.setText(lang_manager.get_text("loudness_type_label"))
        self.target_loudness_label.setText(lang_manager.get_text("target_loudness_label"))
        self.process_button.setText(lang_manager.get_text("process_button"))
        self.settings_button.setText(lang_manager.get_text("settings_button"))
        
        # Update combo box items
        self.loudness_type_combo.clear()
        self.loudness_type_combo.addItem(lang_manager.get_text("loudness_type_combo_item_1"))
        self.loudness_type_combo.addItem(lang_manager.get_text("loudness_type_combo_item_2"))
        self.loudness_type_combo.addItem(lang_manager.get_text("loudness_type_combo_item_3"))
        self.loudness_type_combo.addItem(lang_manager.get_text("loudness_type_combo_item_4"))

    def on_language_changed(self):
        """Handle language change"""
        current_index = self.language_combo.currentIndex()
        if current_index >= 0:
            lang_code = self.language_combo.itemData(current_index)
            if lang_code and lang_manager.set_language(lang_code):
                self.update_language()

    def browse_input_dir(self):
        input_dir = QFileDialog.getExistingDirectory(
            self, lang_manager.get_text("select_input_dir"))
        if input_dir:
            self.input_dir_lineEdit.setText(input_dir)

    def browse_output_dir(self):
        output_dir = QFileDialog.getExistingDirectory(
            self, lang_manager.get_text("select_output_dir"))
        if output_dir:
            self.output_dir_lineEdit.setText(output_dir)

    def process(self):
        input_dir = self.input_dir_lineEdit.text()
        output_dir = self.output_dir_lineEdit.text()
        if not input_dir or not output_dir:
            QMessageBox.critical(self, lang_manager.get_text("error"), lang_manager.get_text("error_message_1"))
            return
        if not os.path.exists(input_dir) or not os.path.exists(output_dir):
            QMessageBox.critical(self, lang_manager.get_text("error"), lang_manager.get_text("error_message_2"))
            return
        if self.target_loudness_lineEdit.text() == "":
            QMessageBox.critical(self, lang_manager.get_text("error"), lang_manager.get_text("error_message_3"))
            return
        target_loudness = float(self.target_loudness_lineEdit.text())
        if target_loudness > 0 or target_loudness < -48:
            QMessageBox.critical(self, lang_manager.get_text("error"), lang_manager.get_text("error_message_4"))
            return
        loudness_type = self.loudness_type_combo.currentText()

        self.worker = Worker(input_dir, output_dir,
                             target_loudness, loudness_type)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(
            lambda: QMessageBox.information(self, "Complete", lang_manager.get_text("processing_completed")))
        self.worker.start()

    def open_settings(self):
        settings_window = SettingsWindow(self)
        settings_window.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
