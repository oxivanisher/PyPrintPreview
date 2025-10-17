#!/bin/bash
# Installation script for PyPrintPreview
# Installs to /opt/PyPrintPreview by default

set -e

INSTALL_DIR="/opt/PyPrintPreview"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "PyPrintPreview Installation Script"
echo "==================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script requires root privileges to install to /opt"
    echo "Please run with sudo:"
    echo "  sudo ./install.sh"
    exit 1
fi

# Install system dependencies
echo "Installing system dependencies..."
apt update
apt install -y python3 python3-pip python3-pyqt5 python3-pil

# Create installation directory
echo ""
echo "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Copy application files
echo "Copying application files..."
cp "$PROJECT_DIR/pyprintpreview.py" "$INSTALL_DIR/"
cp "$PROJECT_DIR/requirements.txt" "$INSTALL_DIR/"
cp "$PROJECT_DIR/README.md" "$INSTALL_DIR/"

# Make script executable
chmod +x "$INSTALL_DIR/pyprintpreview.py"

# Install desktop entry (system-wide)
echo ""
echo "Installing desktop entry..."
cp "$SCRIPT_DIR/pyprintpreview.desktop" /usr/share/applications/
update-desktop-database /usr/share/applications/ 2>/dev/null || true

# Install Nemo action (for all users)
echo "Installing Nemo action (right-click menu)..."
mkdir -p /usr/share/nemo/actions
cp "$SCRIPT_DIR/print-photo.nemo_action" /usr/share/nemo/actions/

# Create symlink in /usr/local/bin for easy command-line access
echo ""
echo "Creating symlink in /usr/local/bin..."
ln -sf "$INSTALL_DIR/pyprintpreview.py" /usr/local/bin/pyprintpreview

echo ""
echo "Installation complete!"
echo ""
echo "You can now:"
echo "  - Run from command line: pyprintpreview /path/to/image.jpg"
echo "  - Right-click any image in Nemo and select 'Print Photo (4x6\")'"
echo "  - Set as default application for images via 'Open With' menu"
echo ""
echo "To uninstall, run:"
echo "  sudo rm -rf $INSTALL_DIR"
echo "  sudo rm /usr/share/applications/pyprintpreview.desktop"
echo "  sudo rm /usr/share/nemo/actions/print-photo.nemo_action"
echo "  sudo rm /usr/local/bin/pyprintpreview"
echo ""
