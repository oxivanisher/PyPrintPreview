#!/usr/bin/env python3
"""
Photo Print Preview - A tool for previewing and printing photos on 4x6" glossy paper
Supports fill (crop) and fit (border) modes with automatic orientation detection.
"""

import sys
import os
import json
import locale
from pathlib import Path
from typing import Optional

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                 QHBoxLayout, QPushButton, QLabel, QRadioButton,
                                 QButtonGroup, QComboBox, QMessageBox, QFileDialog,
                                 QCheckBox)
    from PyQt5.QtCore import Qt, QSizeF
    from PyQt5.QtGui import QPixmap, QPainter, QImage
    from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrinterInfo
except ImportError:
    print("Error: PyQt5 is required. Install with: pip install PyQt5")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)


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
            'paper_source': 'auto'  # 'auto', 'rear', 'front', 'top', etc.
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
            # Load with PIL to get EXIF orientation
            pil_image = Image.open(image_path)

            # Handle EXIF orientation
            try:
                from PIL import ImageOps
                pil_image = ImageOps.exif_transpose(pil_image)
            except Exception:
                pass

            # Convert PIL to QImage
            pil_image = pil_image.convert('RGB')
            data = pil_image.tobytes('raw', 'RGB')
            qimage = QImage(data, pil_image.width, pil_image.height,
                           pil_image.width * 3, QImage.Format_RGB888)

            self.original_image = QPixmap.fromImage(qimage)
            self.update_preview()
            return True

        except Exception as e:
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

        controls_layout.addWidget(settings_group)

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

    def print_image(self):
        """Print the image with current settings"""
        if not self.preview.original_image:
            QMessageBox.warning(self, self.translations.get('no_image'),
                              self.translations.get('no_image_loaded'))
            return

        # Save printer selection
        printer_name = self.printer_combo.currentText()
        if printer_name:
            self.config.set('printer_name', printer_name)

        # Create printer object
        printer = QPrinter(QPrinter.HighResolution)

        # Set printer by name
        if printer_name:
            printer.setPrinterName(printer_name)

        # Configure for 4x6" photo paper
        printer.setPageSize(QPrinter.Custom)
        printer.setPageSizeMM(QSizeF(101.6, 152.4))  # 4x6 inches in mm
        printer.setFullPage(True)  # Borderless

        # Set orientation
        # Canon PIXMA printers REQUIRE portrait orientation as paper is inserted portrait in rear tray
        # The image rotation is handled in get_print_pixmap(), not by printer orientation
        if self.config.get('force_portrait', True):
            # Always portrait for Canon PIXMA compatibility
            printer.setOrientation(QPrinter.Portrait)
        else:
            # Legacy behavior: set orientation based on image
            img_width = self.preview.original_image.width()
            img_height = self.preview.original_image.height()
            if img_width > img_height:
                printer.setOrientation(QPrinter.Landscape)
            else:
                printer.setOrientation(QPrinter.Portrait)

        # Set paper source if specified (for rear tray on Canon PIXMA)
        paper_source = self.config.get('paper_source', 'auto')
        if paper_source != 'auto':
            # Try to set paper source via CUPS options
            # Note: This may not work on all printer drivers
            try:
                from PyQt5.QtPrintSupport import QPrinterInfo
                if hasattr(printer, 'setPaperSource'):
                    # Map source names to QPrinter constants
                    source_map = {
                        'rear': QPrinter.Manual,
                        'front': QPrinter.Auto,
                        'top': QPrinter.Upper,
                    }
                    if paper_source in source_map:
                        printer.setPaperSource(source_map[paper_source])
            except Exception:
                pass  # Silently fail if not supported

        # Show print dialog
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle(self.translations.get('print_photo'))

        if dialog.exec_() == QPrintDialog.Accepted:
            # Get print-ready pixmap
            pixmap = self.preview.get_print_pixmap()

            if pixmap:
                painter = QPainter(printer)

                # Get printer page rect
                page_rect = printer.pageRect(QPrinter.DevicePixel)

                # Draw the pixmap to fill the page
                painter.drawPixmap(page_rect.toRect(), pixmap)
                painter.end()

                QMessageBox.information(self, self.translations.get('success'),
                                      self.translations.get('print_success'))
            else:
                QMessageBox.critical(self, self.translations.get('error'),
                                   self.translations.get('print_error'))


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Get image path from command line if provided
    image_path = None
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        if not os.path.exists(image_path):
            print(f"Error: File not found: {image_path}")
            sys.exit(1)

    window = PhotoPrintWindow(image_path)
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
