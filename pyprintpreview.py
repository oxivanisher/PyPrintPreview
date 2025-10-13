#!/usr/bin/env python3
"""
Photo Print Preview - A tool for previewing and printing photos on 4x6" glossy paper
Supports fill (crop) and fit (border) modes with automatic orientation detection.
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                 QHBoxLayout, QPushButton, QLabel, QRadioButton,
                                 QButtonGroup, QComboBox, QMessageBox, QFileDialog)
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
            'quality': 'high'
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

    def __init__(self, parent=None):
        super().__init__(parent)
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
            QMessageBox.critical(self, "Error", f"Could not load image:\n{str(e)}")
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
        """Generate high-resolution pixmap for printing"""
        if not self.original_image:
            return None

        img_width = self.original_image.width()
        img_height = self.original_image.height()
        img_is_landscape = img_width > img_height

        # Determine paper dimensions for printing
        if img_is_landscape:
            # Landscape: rotate paper orientation
            paper_w = self.paper_height_px
            paper_h = self.paper_width_px
        else:
            # Portrait
            paper_w = self.paper_width_px
            paper_h = self.paper_height_px

        # Create print pixmap
        print_pixmap = QPixmap(paper_w, paper_h)
        print_pixmap.fill(Qt.white)

        painter = QPainter(print_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Calculate scaling based on mode
        img_aspect = img_width / img_height
        paper_aspect = paper_w / paper_h

        if self.scale_mode == 'fill':
            # Fill mode: crop to fill paper completely
            if img_aspect > paper_aspect:
                scale = paper_h / img_height
                scaled_w = int(img_width * scale)
                scaled_h = paper_h
                x_offset = (paper_w - scaled_w) // 2
                y_offset = 0
            else:
                scale = paper_w / img_width
                scaled_w = paper_w
                scaled_h = int(img_height * scale)
                x_offset = 0
                y_offset = (paper_h - scaled_h) // 2
        else:  # fit mode
            # Fit mode: scale to fit with borders
            if img_aspect > paper_aspect:
                scale = paper_w / img_width
                scaled_w = paper_w
                scaled_h = int(img_height * scale)
                x_offset = 0
                y_offset = (paper_h - scaled_h) // 2
            else:
                scale = paper_h / img_height
                scaled_w = int(img_width * scale)
                scaled_h = paper_h
                x_offset = (paper_w - scaled_w) // 2
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

        self.setWindowTitle("Photo Print Preview")
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
        title_label = QLabel("Photo Print Preview - 4x6\" Glossy Paper")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Preview widget
        self.preview = PhotoPreview()
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

        scale_label = QLabel("Print Mode:")
        scale_label.setStyleSheet("font-weight: bold;")
        scale_layout.addWidget(scale_label)

        self.scale_button_group = QButtonGroup()

        self.fill_radio = QRadioButton("Fill (Crop to fit paper)")
        self.fill_radio.setToolTip("Crop image to completely fill the paper with no borders")
        self.scale_button_group.addButton(self.fill_radio, 0)
        scale_layout.addWidget(self.fill_radio)

        self.fit_radio = QRadioButton("Fit (Scale with borders)")
        self.fit_radio.setToolTip("Scale image to fit within paper, may have white borders")
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

        # Printer selection
        printer_group = QWidget()
        printer_layout = QHBoxLayout(printer_group)
        printer_layout.setContentsMargins(0, 0, 0, 0)

        printer_label = QLabel("Printer:")
        printer_label.setStyleSheet("font-weight: bold;")
        printer_layout.addWidget(printer_label)

        self.printer_combo = QComboBox()
        self.populate_printers()
        printer_layout.addWidget(self.printer_combo, stretch=1)

        controls_layout.addWidget(printer_group)

        # Info label
        info_label = QLabel(
            "The script automatically rotates landscape images for proper printing.\n"
            "Paper orientation: Always portrait (4\" width � 6\" height)"
        )
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        info_label.setWordWrap(True)
        controls_layout.addWidget(info_label)

        layout.addWidget(controls_widget)

        # Button section
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.open_button = QPushButton("Open Image...")
        self.open_button.clicked.connect(self.open_image_dialog)
        button_layout.addWidget(self.open_button)

        button_layout.addStretch()

        self.print_button = QPushButton("Print")
        self.print_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "padding: 8px 24px; font-weight: bold; font-size: 14px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        self.print_button.clicked.connect(self.print_image)
        self.print_button.setEnabled(False)
        button_layout.addWidget(self.print_button)

        self.close_button = QPushButton("Close")
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

    def open_image_dialog(self):
        """Open file dialog to select an image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            os.path.expanduser("~"),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp)"
        )

        if file_path:
            self.load_image(file_path)

    def load_image(self, image_path: str):
        """Load an image into the preview"""
        self.image_path = image_path
        if self.preview.load_image(image_path):
            self.print_button.setEnabled(True)
            self.setWindowTitle(f"Photo Print Preview - {os.path.basename(image_path)}")

    def print_image(self):
        """Print the image with current settings"""
        if not self.preview.original_image:
            QMessageBox.warning(self, "No Image", "Please load an image first.")
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

        # Set orientation based on image
        img_width = self.preview.original_image.width()
        img_height = self.preview.original_image.height()
        if img_width > img_height:
            printer.setOrientation(QPrinter.Landscape)
        else:
            printer.setOrientation(QPrinter.Portrait)

        # Show print dialog
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Print Photo")

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

                QMessageBox.information(self, "Success", "Print job sent successfully!")
            else:
                QMessageBox.critical(self, "Error", "Could not generate print image.")


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
