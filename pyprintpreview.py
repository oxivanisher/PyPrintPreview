#!/usr/bin/env python3
"""
Photo Print Preview - A tool for previewing and printing photos on 4x6" glossy paper
Supports fill (crop) and fit (border) modes with automatic orientation detection.
"""

import sys
import os
import json
import locale
import logging
import subprocess
from pathlib import Path
from typing import Optional

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                 QHBoxLayout, QPushButton, QLabel, QRadioButton,
                                 QButtonGroup, QComboBox, QMessageBox, QFileDialog,
                                 QCheckBox)
    from PyQt5.QtCore import Qt, QSizeF
    from PyQt5.QtGui import QPixmap, QPainter, QImage, QPageSize
    from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrinterInfo
except ImportError:
    print("Error: PyQt5 is required. Install with: pip install PyQt5")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Logging — writes to /tmp/pyprintpreview.log, appending each run.
# ---------------------------------------------------------------------------
log = logging.getLogger("pyprintpreview")
log.setLevel(logging.DEBUG)
_fh = logging.FileHandler("/tmp/pyprintpreview.log")
_fh.setFormatter(logging.Formatter(
    "%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
log.addHandler(_fh)


class Translations:
    """Manages application translations for multiple languages"""

    LANGUAGES = {
        'en': 'English',
        'de': 'Deutsch'
    }

    STRINGS = {
        'en': {
            'window_title': 'Photo Print Preview',
            'title_label': 'Photo Print Preview - 4x6" Glossy Paper',
            'print_mode': 'Print Mode:',
            'fill_mode': 'Fill (Crop to fit paper)',
            'fill_tooltip': 'Crop image to completely fill the paper with no borders',
            'fit_mode': 'Fit (Scale with borders)',
            'fit_tooltip': 'Scale image to fit within paper, may have white borders',
            'printer': 'Printer:',
            'language': 'Language:',
            'info_text': 'The script automatically rotates landscape images for proper printing.\nPaper orientation: Always portrait (4" width × 6" height)',
            'open_image': 'Open Image...',
            'print': 'Print',
            'close': 'Close',
            'error': 'Error',
            'success': 'Success',
            'no_image': 'No Image',
            'warning': 'Warning',
            'load_error': 'Could not load image:',
            'no_image_loaded': 'Please load an image first.',
            'print_success': 'Print job sent successfully!',
            'print_error': 'Could not generate print image.',
            'select_image': 'Select Image',
            'images': 'Images',
            'print_photo': 'Print Photo',
            'printer_settings': 'Printer Settings',
            'force_portrait': 'Always use portrait orientation (Canon PIXMA)',
            'force_portrait_tooltip': 'Canon PIXMA printers require portrait orientation even for landscape photos',
            'paper_source': 'Paper Source:',
            'paper_source_auto': 'Auto',
            'paper_source_rear': 'Rear Tray',
            'paper_source_front': 'Front Tray',
            'paper_source_top': 'Top Tray',
            'media_type': 'Media Type:',
            'media_type_auto': 'Auto (not set)',
        },
        'de': {
            'window_title': 'Fotodruck-Vorschau',
            'title_label': 'Fotodruck-Vorschau - 4x6" Fotopapier',
            'print_mode': 'Druckmodus:',
            'fill_mode': 'Füllen (Zuschneiden)',
            'fill_tooltip': 'Bild zuschneiden, um das Papier vollständig ohne Rand zu füllen',
            'fit_mode': 'Einpassen (Mit Rand)',
            'fit_tooltip': 'Bild einpassen, kann weiße Ränder haben',
            'printer': 'Drucker:',
            'language': 'Sprache:',
            'info_text': 'Das Skript dreht Querformat-Bilder automatisch für den korrekten Druck.\nPapierausrichtung: Immer Hochformat (4" Breite × 6" Höhe)',
            'open_image': 'Bild öffnen...',
            'print': 'Drucken',
            'close': 'Schließen',
            'error': 'Fehler',
            'success': 'Erfolg',
            'no_image': 'Kein Bild',
            'warning': 'Warnung',
            'load_error': 'Bild konnte nicht geladen werden:',
            'no_image_loaded': 'Bitte laden Sie zuerst ein Bild.',
            'print_success': 'Druckauftrag erfolgreich gesendet!',
            'print_error': 'Druckbild konnte nicht erstellt werden.',
            'select_image': 'Bild auswählen',
            'images': 'Bilder',
            'print_photo': 'Foto drucken',
            'printer_settings': 'Druckereinstellungen',
            'force_portrait': 'Immer Hochformat verwenden (Canon PIXMA)',
            'force_portrait_tooltip': 'Canon PIXMA-Drucker erfordern Hochformat auch für Querformat-Fotos',
            'paper_source': 'Papierquelle:',
            'paper_source_auto': 'Auto',
            'paper_source_rear': 'Hinteres Fach',
            'paper_source_front': 'Vorderes Fach',
            'paper_source_top': 'Oberes Fach',
            'media_type': 'Medientyp:',
            'media_type_auto': 'Auto (nicht gesetzt)',
        }
    }

    def __init__(self):
        self.current_lang = self._detect_system_language()

    def _detect_system_language(self) -> str:
        """Detect system language, default to English"""
        try:
            # Try to get the current locale
            system_locale = locale.getlocale()[0]
            if system_locale:
                lang_code = system_locale.split('_')[0].lower()
                if lang_code in self.LANGUAGES:
                    return lang_code
        except Exception:
            pass
        return 'en'

    def set_language(self, lang_code: str):
        """Set the current language"""
        if lang_code in self.LANGUAGES:
            self.current_lang = lang_code

    def get(self, key: str) -> str:
        """Get a translated string"""
        return self.STRINGS.get(self.current_lang, {}).get(key, key)

    def get_current_language(self) -> str:
        """Get current language code"""
        return self.current_lang


class Config:
    """Manages application configuration for printer settings"""

    def __init__(self):
        self.config_dir = Path.home() / '.config' / 'pyprintpreview'
        self.config_file = self.config_dir / 'settings.json'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.settings = self.load()

    def load(self) -> dict:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config: {e}")

        return {
            'printer_name': '',
            'last_scale_mode': 'fill',
            'paper_size': '4x6',
            'borderless': True,
            'quality': 'high',
            'language': None,  # None means auto-detect
            'force_portrait': True,  # Force portrait orientation for Canon PIXMA compatibility
            'paper_source': 'auto',  # 'auto', 'rear', 'front', 'top', etc.
            'media_type': ''  # '' = don't set (printer decides), otherwise a PPD MediaType value
        }

    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")

    def get(self, key: str, default=None):
        """Get a configuration value"""
        return self.settings.get(key, default)

    def set(self, key: str, value):
        """Set a configuration value"""
        self.settings[key] = value
        self.save()


class PhotoPreview(QLabel):
    """Widget for displaying photo preview with fill/fit modes"""

    def __init__(self, parent=None, translations=None):
        super().__init__(parent)
        self.translations = translations
        self.setMinimumSize(600, 400)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("QLabel { background-color: #2b2b2b; border: 2px solid #555; }")

        self.original_image = None
        self.scale_mode = 'fill'  # 'fill' or 'fit'
        self.paper_orientation = 'portrait'  # Paper is always portrait (4"x6")

        # 4x6 inch paper at 300 DPI
        self.paper_width_px = int(4 * 300)   # 1200 px
        self.paper_height_px = int(6 * 300)  # 1800 px

    def load_image(self, image_path: str) -> bool:
        """Load an image and determine its orientation"""
        try:
            log.info("Loading image: %s", image_path)

            # Load with PIL to get EXIF orientation
            pil_image = Image.open(image_path)
            log.debug("Image opened — size: %dx%d, mode: %s",
                      pil_image.width, pil_image.height, pil_image.mode)

            # Handle EXIF orientation
            try:
                from PIL import ImageOps
                before = (pil_image.width, pil_image.height)
                pil_image = ImageOps.exif_transpose(pil_image)
                after = (pil_image.width, pil_image.height)
                if before != after:
                    log.info("EXIF transpose applied: %dx%d → %dx%d",
                             before[0], before[1], after[0], after[1])
                else:
                    log.debug("EXIF transpose: no rotation needed")
            except Exception:
                log.warning("EXIF transpose failed — using image as-is")

            # Convert PIL to QImage
            pil_image = pil_image.convert('RGB')
            data = pil_image.tobytes('raw', 'RGB')
            qimage = QImage(data, pil_image.width, pil_image.height,
                           pil_image.width * 3, QImage.Format_RGB888)

            self.original_image = QPixmap.fromImage(qimage)
            orientation = "landscape" if pil_image.width > pil_image.height else "portrait"
            log.info("Image loaded — final size: %dx%d (%s)",
                     pil_image.width, pil_image.height, orientation)
            self.update_preview()
            return True

        except Exception as e:
            log.error("Failed to load image: %s", e)
            error_title = self.translations.get('error') if self.translations else "Error"
            error_msg = self.translations.get('load_error') if self.translations else "Could not load image:"
            QMessageBox.critical(self, error_title, f"{error_msg}\n{str(e)}")
            return False

    def set_scale_mode(self, mode: str):
        """Set the scaling mode ('fill' or 'fit')"""
        self.scale_mode = mode
        self.update_preview()

    def update_preview(self):
        """Update the preview based on current settings"""
        if not self.original_image:
            return

        # Determine if image should be rotated
        img_width = self.original_image.width()
        img_height = self.original_image.height()
        img_is_landscape = img_width > img_height

        # Calculate paper aspect ratio (4:6 = 0.667)
        paper_aspect = 4.0 / 6.0

        # Create preview pixmap
        preview_width = self.width() - 20
        preview_height = self.height() - 20

        # Calculate preview paper size maintaining aspect ratio
        if preview_width / paper_aspect < preview_height:
            paper_w = preview_width
            paper_h = int(preview_width / paper_aspect)
        else:
            paper_h = preview_height
            paper_w = int(preview_height * paper_aspect)

        # Create canvas for preview
        preview_pixmap = QPixmap(paper_w, paper_h)
        preview_pixmap.fill(Qt.white)

        painter = QPainter(preview_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Determine if we need to rotate the image for printing
        # Image is landscape and paper is portrait -> rotate image 90�
        working_image = self.original_image
        if img_is_landscape:
            # Rotate for landscape printing
            painter.translate(paper_w / 2, paper_h / 2)
            painter.rotate(90)
            painter.translate(-paper_h / 2, -paper_w / 2)
            # Swap dimensions for calculation
            paper_w, paper_h = paper_h, paper_w

        # Calculate scaling based on mode
        img_aspect = img_width / img_height
        paper_calc_aspect = paper_w / paper_h

        if self.scale_mode == 'fill':
            # Fill mode: crop to fill paper completely
            if img_aspect > paper_calc_aspect:
                # Image is wider - fit to height
                scale = paper_h / img_height
                scaled_w = int(img_width * scale)
                scaled_h = paper_h
                x_offset = (paper_w - scaled_w) // 2
                y_offset = 0
            else:
                # Image is taller - fit to width
                scale = paper_w / img_width
                scaled_w = paper_w
                scaled_h = int(img_height * scale)
                x_offset = 0
                y_offset = (paper_h - scaled_h) // 2

            # Draw scaled image
            painter.drawPixmap(x_offset, y_offset, scaled_w, scaled_h, working_image)

        else:  # fit mode
            # Fit mode: scale to fit with borders
            if img_aspect > paper_calc_aspect:
                # Image is wider - fit to width
                scale = paper_w / img_width
                scaled_w = paper_w
                scaled_h = int(img_height * scale)
                x_offset = 0
                y_offset = (paper_h - scaled_h) // 2
            else:
                # Image is taller - fit to height
                scale = paper_h / img_height
                scaled_w = int(img_width * scale)
                scaled_h = paper_h
                x_offset = (paper_w - scaled_w) // 2
                y_offset = 0

            # Draw scaled image
            painter.drawPixmap(x_offset, y_offset, scaled_w, scaled_h, working_image)

        painter.end()

        # Restore rotation for landscape
        if img_is_landscape:
            transform_obj = preview_pixmap.transformed(
                painter.transform().rotate(-90), Qt.SmoothTransformation
            )
            preview_pixmap = transform_obj

        self.setPixmap(preview_pixmap)

    def resizeEvent(self, event):
        """Handle widget resize"""
        super().resizeEvent(event)
        self.update_preview()

    def get_print_pixmap(self) -> QPixmap:
        """Generate high-resolution pixmap for printing

        Always creates a portrait-oriented canvas (4"x6" = 1200x1800px) for borderless printing.
        For landscape images, the image is rotated 90° to fit within the portrait canvas.
        This ensures proper borderless printing on Canon PIXMA and similar printers that
        require paper inserted in portrait orientation.
        """
        if not self.original_image:
            return None

        img_width = self.original_image.width()
        img_height = self.original_image.height()
        img_is_landscape = img_width > img_height

        # Always create portrait canvas (4"x6" = 1200x1800px)
        # This matches the printer's portrait orientation requirement
        paper_w = self.paper_width_px   # 1200
        paper_h = self.paper_height_px  # 1800

        # Create print pixmap
        print_pixmap = QPixmap(paper_w, paper_h)
        print_pixmap.fill(Qt.white)

        painter = QPainter(print_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # For landscape images, rotate the canvas 90° so we can draw the landscape image
        # Then we'll rotate the final pixmap back to portrait
        working_paper_w = paper_w
        working_paper_h = paper_h

        if img_is_landscape:
            # Rotate canvas to landscape orientation for drawing
            painter.translate(paper_w / 2, paper_h / 2)
            painter.rotate(90)
            painter.translate(-paper_h / 2, -paper_w / 2)
            # Swap dimensions for calculations
            working_paper_w, working_paper_h = paper_h, paper_w

        # Calculate scaling based on mode
        img_aspect = img_width / img_height
        paper_aspect = working_paper_w / working_paper_h

        if self.scale_mode == 'fill':
            # Fill mode: crop to fill paper completely
            if img_aspect > paper_aspect:
                scale = working_paper_h / img_height
                scaled_w = int(img_width * scale)
                scaled_h = working_paper_h
                x_offset = (working_paper_w - scaled_w) // 2
                y_offset = 0
            else:
                scale = working_paper_w / img_width
                scaled_w = working_paper_w
                scaled_h = int(img_height * scale)
                x_offset = 0
                y_offset = (working_paper_h - scaled_h) // 2
        else:  # fit mode
            # Fit mode: scale to fit with borders
            if img_aspect > paper_aspect:
                scale = working_paper_w / img_width
                scaled_w = working_paper_w
                scaled_h = int(img_height * scale)
                x_offset = 0
                y_offset = (working_paper_h - scaled_h) // 2
            else:
                scale = working_paper_h / img_height
                scaled_w = int(img_width * scale)
                scaled_h = working_paper_h
                x_offset = (working_paper_w - scaled_w) // 2
                y_offset = 0

        painter.drawPixmap(x_offset, y_offset, scaled_w, scaled_h, self.original_image)
        painter.end()

        return print_pixmap


class PhotoPrintWindow(QMainWindow):
    """Main application window"""

    def __init__(self, image_path: Optional[str] = None):
        super().__init__()
        self.config = Config()
        self.image_path = image_path

        # Initialize translations
        self.translations = Translations()
        saved_lang = self.config.get('language')
        if saved_lang:
            self.translations.set_language(saved_lang)

        self.setWindowTitle(self.translations.get('window_title'))
        self.setMinimumSize(800, 700)

        self.init_ui()

        if image_path and os.path.exists(image_path):
            self.load_image(image_path)

    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title_label = QLabel(self.translations.get('title_label'))
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Preview widget
        self.preview = PhotoPreview(translations=self.translations)
        self.preview.set_scale_mode(self.config.get('last_scale_mode', 'fill'))
        layout.addWidget(self.preview, stretch=1)

        # Controls section
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setSpacing(15)

        # Scale mode selection
        scale_group = QWidget()
        scale_layout = QHBoxLayout(scale_group)
        scale_layout.setContentsMargins(0, 0, 0, 0)

        scale_label = QLabel(self.translations.get('print_mode'))
        scale_label.setStyleSheet("font-weight: bold;")
        scale_layout.addWidget(scale_label)

        self.scale_button_group = QButtonGroup()

        self.fill_radio = QRadioButton(self.translations.get('fill_mode'))
        self.fill_radio.setToolTip(self.translations.get('fill_tooltip'))
        self.scale_button_group.addButton(self.fill_radio, 0)
        scale_layout.addWidget(self.fill_radio)

        self.fit_radio = QRadioButton(self.translations.get('fit_mode'))
        self.fit_radio.setToolTip(self.translations.get('fit_tooltip'))
        self.scale_button_group.addButton(self.fit_radio, 1)
        scale_layout.addWidget(self.fit_radio)

        scale_layout.addStretch()

        # Set default mode
        if self.config.get('last_scale_mode', 'fill') == 'fill':
            self.fill_radio.setChecked(True)
        else:
            self.fit_radio.setChecked(True)

        self.scale_button_group.buttonClicked.connect(self.on_scale_mode_changed)

        controls_layout.addWidget(scale_group)

        # Language selection
        lang_group = QWidget()
        lang_layout = QHBoxLayout(lang_group)
        lang_layout.setContentsMargins(0, 0, 0, 0)

        lang_label = QLabel(self.translations.get('language'))
        lang_label.setStyleSheet("font-weight: bold;")
        lang_layout.addWidget(lang_label)

        self.language_combo = QComboBox()
        for lang_code, lang_name in Translations.LANGUAGES.items():
            self.language_combo.addItem(lang_name, lang_code)

        # Set current language
        current_lang = self.translations.get_current_language()
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_lang:
                self.language_combo.setCurrentIndex(i)
                break

        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch()

        controls_layout.addWidget(lang_group)

        # Printer selection
        printer_group = QWidget()
        printer_layout = QHBoxLayout(printer_group)
        printer_layout.setContentsMargins(0, 0, 0, 0)

        printer_label = QLabel(self.translations.get('printer'))
        printer_label.setStyleSheet("font-weight: bold;")
        printer_layout.addWidget(printer_label)

        self.printer_combo = QComboBox()
        self.populate_printers()
        printer_layout.addWidget(self.printer_combo, stretch=1)

        controls_layout.addWidget(printer_group)

        # Printer settings group
        settings_group = QWidget()
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setContentsMargins(20, 0, 0, 0)  # Indent settings
        settings_layout.setSpacing(5)

        # Force portrait checkbox
        self.force_portrait_check = QCheckBox(self.translations.get('force_portrait'))
        self.force_portrait_check.setToolTip(self.translations.get('force_portrait_tooltip'))
        self.force_portrait_check.setChecked(self.config.get('force_portrait', True))
        self.force_portrait_check.stateChanged.connect(self.on_force_portrait_changed)
        settings_layout.addWidget(self.force_portrait_check)

        # Paper source selection
        paper_source_widget = QWidget()
        paper_source_layout = QHBoxLayout(paper_source_widget)
        paper_source_layout.setContentsMargins(0, 0, 0, 0)

        paper_source_label = QLabel(self.translations.get('paper_source'))
        paper_source_layout.addWidget(paper_source_label)

        self.paper_source_combo = QComboBox()
        self.paper_source_combo.addItem(self.translations.get('paper_source_auto'), 'auto')
        self.paper_source_combo.addItem(self.translations.get('paper_source_rear'), 'rear')
        self.paper_source_combo.addItem(self.translations.get('paper_source_front'), 'front')
        self.paper_source_combo.addItem(self.translations.get('paper_source_top'), 'top')

        # Set current paper source
        current_source = self.config.get('paper_source', 'auto')
        for i in range(self.paper_source_combo.count()):
            if self.paper_source_combo.itemData(i) == current_source:
                self.paper_source_combo.setCurrentIndex(i)
                break

        self.paper_source_combo.currentIndexChanged.connect(self.on_paper_source_changed)
        paper_source_layout.addWidget(self.paper_source_combo)
        paper_source_layout.addStretch()

        settings_layout.addWidget(paper_source_widget)

        # Media type selection (populated from printer PPD via lpoptions)
        media_type_widget = QWidget()
        media_type_layout = QHBoxLayout(media_type_widget)
        media_type_layout.setContentsMargins(0, 0, 0, 0)

        media_type_label = QLabel(self.translations.get('media_type'))
        media_type_layout.addWidget(media_type_label)

        self.media_type_combo = QComboBox()
        self.media_type_combo.setMinimumWidth(200)
        self.media_type_combo.currentIndexChanged.connect(self.on_media_type_changed)
        media_type_layout.addWidget(self.media_type_combo)
        media_type_layout.addStretch()

        settings_layout.addWidget(media_type_widget)

        controls_layout.addWidget(settings_group)

        # Populate media types for the initially selected printer and wire up
        # the printer combo so it repopulates whenever the selection changes.
        self.printer_combo.currentIndexChanged.connect(self.on_printer_changed)
        self._populate_media_type_combo(self.printer_combo.currentText())

        # Info label
        self.info_label = QLabel(self.translations.get('info_text'))
        self.info_label.setStyleSheet("color: #666; font-size: 11px;")
        self.info_label.setWordWrap(True)
        controls_layout.addWidget(self.info_label)

        layout.addWidget(controls_widget)

        # Button section
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.open_button = QPushButton(self.translations.get('open_image'))
        self.open_button.clicked.connect(self.open_image_dialog)
        button_layout.addWidget(self.open_button)

        button_layout.addStretch()

        self.print_button = QPushButton(self.translations.get('print'))
        self.print_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "padding: 8px 24px; font-weight: bold; font-size: 14px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        self.print_button.clicked.connect(self.print_image)
        self.print_button.setEnabled(False)
        button_layout.addWidget(self.print_button)

        self.close_button = QPushButton(self.translations.get('close'))
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)

        layout.addWidget(button_widget)

    def populate_printers(self):
        """Populate the printer combo box"""
        self.printer_combo.clear()

        # Get available printers
        printers = QPrinterInfo.availablePrinters()

        saved_printer = self.config.get('printer_name', '')
        default_index = 0

        for i, printer_info in enumerate(printers):
            printer_name = printer_info.printerName()
            self.printer_combo.addItem(printer_name)

            if printer_name == saved_printer:
                default_index = i

        if self.printer_combo.count() > 0:
            self.printer_combo.setCurrentIndex(default_index)

    def on_scale_mode_changed(self):
        """Handle scale mode radio button change"""
        if self.fill_radio.isChecked():
            mode = 'fill'
        else:
            mode = 'fit'

        self.preview.set_scale_mode(mode)
        self.config.set('last_scale_mode', mode)

    def on_language_changed(self):
        """Handle language change"""
        lang_code = self.language_combo.currentData()
        if lang_code:
            self.translations.set_language(lang_code)
            self.config.set('language', lang_code)
            self.update_ui_texts()

    def on_force_portrait_changed(self, state):
        """Handle force portrait checkbox change"""
        self.config.set('force_portrait', state == Qt.Checked)

    def on_paper_source_changed(self):
        """Handle paper source combo box change"""
        paper_source = self.paper_source_combo.currentData()
        if paper_source:
            self.config.set('paper_source', paper_source)

    def update_ui_texts(self):
        """Update all UI texts with current language"""
        self.setWindowTitle(self.translations.get('window_title'))

        # Update title label
        title = self.findChild(QLabel)
        if title:
            title.setText(self.translations.get('title_label'))

        # Update buttons
        self.open_button.setText(self.translations.get('open_image'))
        self.print_button.setText(self.translations.get('print'))
        self.close_button.setText(self.translations.get('close'))

        # Update radio buttons
        self.fill_radio.setText(self.translations.get('fill_mode'))
        self.fill_radio.setToolTip(self.translations.get('fill_tooltip'))
        self.fit_radio.setText(self.translations.get('fit_mode'))
        self.fit_radio.setToolTip(self.translations.get('fit_tooltip'))

        # Update printer settings checkbox
        self.force_portrait_check.setText(self.translations.get('force_portrait'))
        self.force_portrait_check.setToolTip(self.translations.get('force_portrait_tooltip'))

        # Update paper source combo box items
        for i in range(self.paper_source_combo.count()):
            source_key = self.paper_source_combo.itemData(i)
            if source_key == 'auto':
                self.paper_source_combo.setItemText(i, self.translations.get('paper_source_auto'))
            elif source_key == 'rear':
                self.paper_source_combo.setItemText(i, self.translations.get('paper_source_rear'))
            elif source_key == 'front':
                self.paper_source_combo.setItemText(i, self.translations.get('paper_source_front'))
            elif source_key == 'top':
                self.paper_source_combo.setItemText(i, self.translations.get('paper_source_top'))

        # Update info label
        self.info_label.setText(self.translations.get('info_text'))

        # Update window title with image name if loaded
        if self.image_path:
            self.setWindowTitle(f"{self.translations.get('window_title')} - {os.path.basename(self.image_path)}")

    def open_image_dialog(self):
        """Open file dialog to select an image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.translations.get('select_image'),
            os.path.expanduser("~"),
            f"{self.translations.get('images')} (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp)"
        )

        if file_path:
            self.load_image(file_path)

    def load_image(self, image_path: str):
        """Load an image into the preview"""
        self.image_path = image_path
        if self.preview.load_image(image_path):
            self.print_button.setEnabled(True)
            self.setWindowTitle(f"{self.translations.get('window_title')} - {os.path.basename(image_path)}")

    def _query_media_types(self, printer_name: str) -> list:
        """Return the list of MediaType values from the printer's PPD via lpoptions."""
        try:
            result = subprocess.run(
                ['lpoptions', '-p', printer_name, '-l'],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if line.startswith('MediaType'):
                    # Format: "MediaType/Media Type: *Auto Plain GlossyPP2 ..."
                    _, values_str = line.split(':', 1)
                    values = [v.lstrip('*') for v in values_str.split()]
                    log.debug("MediaType options for %s: %s", printer_name, values)
                    return values
        except Exception as e:
            log.warning("Could not query media types via lpoptions: %s", e)
        return []

    def _populate_media_type_combo(self, printer_name: str):
        """Populate the media type combo with values from the printer's PPD."""
        self.media_type_combo.blockSignals(True)
        self.media_type_combo.clear()
        self.media_type_combo.addItem(self.translations.get('media_type_auto'), '')

        media_types = self._query_media_types(printer_name)
        for mt in media_types:
            self.media_type_combo.addItem(mt, mt)

        saved = self.config.get('media_type', '')
        matched = False
        if saved:
            for i in range(self.media_type_combo.count()):
                if self.media_type_combo.itemData(i) == saved:
                    self.media_type_combo.setCurrentIndex(i)
                    matched = True
                    break

        if not matched:
            # No saved preference — auto-select the best match for photo paper.
            photo_keywords = ['photographic', 'photo', 'gloss']
            for i in range(self.media_type_combo.count()):
                val = (self.media_type_combo.itemData(i) or '').lower()
                if any(kw in val for kw in photo_keywords):
                    self.media_type_combo.setCurrentIndex(i)
                    log.info("Auto-selected media type: '%s'", self.media_type_combo.itemData(i))
                    break

        self.media_type_combo.blockSignals(False)
        log.info("Media type combo populated for '%s': %d options, selected='%s'",
                 printer_name, self.media_type_combo.count(),
                 self.media_type_combo.currentData())

    def on_printer_changed(self):
        """Repopulate media type combo when the selected printer changes."""
        printer_name = self.printer_combo.currentText()
        log.info("Printer selection changed to: %s", printer_name)
        self._populate_media_type_combo(printer_name)

    def on_media_type_changed(self):
        """Save the selected media type to config."""
        media_type = self.media_type_combo.currentData()
        if media_type is not None:
            self.config.set('media_type', media_type)
            log.info("Media type changed to: '%s'", media_type)

    def _find_4x6_page_size(self, printer_name: str) -> 'QPageSize':
        """Return the printer's native QPageSize for 4x6" paper.

        Queries the printer's PPD via QPrinterInfo.supportedPageSizes() and
        returns the first entry whose physical dimensions match 4x6" within a
        small tolerance.  Falls back to a generic named QPageSize("4x6in") if
        nothing matches (e.g. generic CUPS driver with no PPD size list).
        """
        target_w = 101.6  # mm (4 inches)
        target_h = 152.4  # mm (6 inches)
        tolerance = 3.0   # mm

        log.info("Querying page sizes for printer: %s", printer_name)
        try:
            info = QPrinterInfo.printerInfo(printer_name)
            supported = info.supportedPageSizes()

            if not supported:
                log.warning("Printer reported no supported page sizes (generic driver?)")
            else:
                log.debug("Printer supports %d page size(s):", len(supported))
                for ps in supported:
                    s = ps.size(QPageSize.Millimeter)
                    log.debug("  %-30s  %.1f x %.1f mm  (key: %s)",
                              ps.name(), s.width(), s.height(), ps.key())

            # Two-pass: prefer the borderless variant, accept plain as fallback.
            first_match = None
            for ps in supported:
                size = ps.size(QPageSize.Millimeter)
                w, h = size.width(), size.height()
                if (abs(w - target_w) <= tolerance and abs(h - target_h) <= tolerance) or \
                   (abs(w - target_h) <= tolerance and abs(h - target_w) <= tolerance):
                    if "Borderless" in ps.key():
                        log.info("Matched borderless page size: '%s' (key: %s, %.1f x %.1f mm)",
                                 ps.name(), ps.key(), w, h)
                        return ps
                    if first_match is None:
                        first_match = ps

            if first_match is not None:
                log.warning("No borderless variant found — using non-borderless: '%s' (key: %s)",
                            first_match.name(), first_match.key())
                return first_match

            log.warning("No matching 4x6\" page size found in printer PPD — using fallback")
        except Exception as e:
            log.error("Error querying printer page sizes: %s", e)

        fallback = QPageSize(QSizeF(4.0, 6.0), QPageSize.Inch, "4x6in")
        log.info("Using fallback page size: name='%s', key='%s'",
                 fallback.name(), fallback.key())
        return fallback

    def print_image(self):
        """Print the image with current settings.

        Uses Qt's QPainter/QPrinter for job submission (proven to work with
        CUPS), but sets MediaType and page size as per-user CUPS defaults via
        'lpoptions' beforehand so CUPS includes them in the job Qt submits.
        """
        if not self.preview.original_image:
            QMessageBox.warning(self, self.translations.get('no_image'),
                              self.translations.get('no_image_loaded'))
            return

        printer_name = self.printer_combo.currentText()
        if printer_name:
            self.config.set('printer_name', printer_name)

        # Set MediaType (and page size) as per-user CUPS defaults via lpoptions
        # so Qt's CUPS backend includes them in the job it submits.
        page_size = self._find_4x6_page_size(printer_name)
        lpoptions_opts = [f'media={page_size.key()}']

        media_type = self.media_type_combo.currentData()
        if media_type:
            lpoptions_opts.append(f'MediaType={media_type}')
            log.info("MediaType: %s (will be set via lpoptions)", media_type)
        else:
            log.info("MediaType: not set (left to printer default)")

        try:
            cmd = ['lpoptions', '-p', printer_name]
            for opt in lpoptions_opts:
                cmd += ['-o', opt]
            log.info("Setting CUPS user defaults: %s", ' '.join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                log.warning("lpoptions failed (exit %d): %s", result.returncode, result.stderr.strip())
            else:
                log.info("lpoptions: OK")
        except Exception as e:
            log.warning("lpoptions error: %s", e)

        # Configure QPrinter.
        printer = QPrinter(QPrinter.HighResolution)
        if printer_name:
            printer.setPrinterName(printer_name)
        printer.setPageSize(page_size)
        printer.setFullPage(True)
        printer.setOrientation(QPrinter.Portrait)
        log.info("Orientation: Portrait (image rotation handled in pixmap)")

        paper_source = self.config.get('paper_source', 'auto')
        log.info("Paper source: %s", paper_source)
        if paper_source != 'auto':
            source_map = {'rear': QPrinter.Manual, 'front': QPrinter.Auto, 'top': QPrinter.Upper}
            if paper_source in source_map:
                printer.setPaperSource(source_map[paper_source])

        log.info("Opening print dialog")
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle(self.translations.get('print_photo'))

        dialog_result = dialog.exec_()
        log.info("Print dialog result: %r  (Accepted=%r)", dialog_result, QPrintDialog.Accepted)

        if dialog_result != QPrintDialog.Accepted:
            log.info("Print dialog cancelled by user")
            return

        final_printer = printer.printerName()
        log.info("Print dialog accepted — printer='%s', building JPEG and submitting via lp",
                 final_printer)
        pixmap = self.preview.get_print_pixmap()
        if not pixmap:
            log.error("get_print_pixmap() returned None — print aborted")
            QMessageBox.critical(self, self.translations.get('error'),
                               self.translations.get('print_error'))
            return

        # Save QPixmap → temp PNG → PIL re-reads → JPEG with 300 DPI metadata.
        # JPEG is the format Canon's CUPS driver handles most reliably for photos.
        # DPI metadata in the file tells CUPS the image is 4x6" without needing
        # any extra scaling options.
        import tempfile
        fd_png, tmp_png = tempfile.mkstemp(suffix='.png', prefix='pyprintpreview_')
        fd_jpg, tmp_jpg = tempfile.mkstemp(suffix='.jpg', prefix='pyprintpreview_')
        os.close(fd_png)
        os.close(fd_jpg)
        try:
            if not pixmap.save(tmp_png, "PNG"):
                raise RuntimeError("QPixmap.save() failed")
            pil_img = Image.open(tmp_png)
            pil_img.load()
            pil_img.save(tmp_jpg, "JPEG", quality=95, dpi=(300, 300))
            log.info("Saved JPEG: %s  (%dx%d @ 300 DPI)", tmp_jpg, pil_img.width, pil_img.height)

            cmd = ['lp', '-d', final_printer,
                   '-o', f'media={page_size.key()}']
            if media_type:
                cmd += ['-o', f'MediaType={media_type}']
            cmd.append(tmp_jpg)
            log.info("lp command: %s", ' '.join(cmd))

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                log.info("lp submitted successfully: %s", result.stdout.strip())
                QMessageBox.information(self, self.translations.get('success'),
                                      self.translations.get('print_success'))
            else:
                log.error("lp failed (exit %d): %s", result.returncode, result.stderr.strip())
                QMessageBox.critical(self, self.translations.get('error'),
                                   f"{self.translations.get('print_error')}\n{result.stderr.strip()}")
        except Exception as e:
            log.error("Print error: %s", e, exc_info=True)
            QMessageBox.critical(self, self.translations.get('error'),
                               f"{self.translations.get('print_error')}\n{e}")
        finally:
            for f in (tmp_png, tmp_jpg):
                try:
                    os.unlink(f)
                except Exception:
                    pass


def main():
    """Main entry point"""
    log.info("=" * 60)
    log.info("PyPrintPreview starting  (args: %s)", sys.argv[1:])

    app = QApplication(sys.argv)

    # Get image path from command line if provided
    image_path = None
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        if not os.path.exists(image_path):
            log.error("File not found: %s", image_path)
            print(f"Error: File not found: {image_path}")
            sys.exit(1)

    # Log available printers
    printers = QPrinterInfo.availablePrinters()
    default = QPrinterInfo.defaultPrinter()
    log.info("Available printers (%d):", len(printers))
    for p in printers:
        marker = " [default]" if p.printerName() == default.printerName() else ""
        log.info("  %s%s", p.printerName(), marker)

    window = PhotoPrintWindow(image_path)
    log.info("Language: %s, scale mode: %s, force_portrait: %s, paper_source: %s",
             window.translations.get_current_language(),
             window.config.get('last_scale_mode'),
             window.config.get('force_portrait'),
             window.config.get('paper_source'))
    window.show()

    exit_code = app.exec_()
    log.info("PyPrintPreview exiting (code %d)", exit_code)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
