# PyPrintPreview Installation Files

This directory contains files for installing PyPrintPreview to `/opt/PyPrintPreview` on Linux systems.

## Files

### install.sh
Automated installation script that:
- Installs system dependencies (Python, PyQt5, Pillow)
- Copies application files to `/opt/PyPrintPreview`
- Sets up desktop integration system-wide
- Creates Nemo file manager context menu entry
- Creates symlink in `/usr/local/bin` for command-line access

**Usage:**
```bash
sudo ./install.sh
```

### pyprintpreview.desktop
Desktop entry file for system integration. Allows the application to:
- Appear in application menus
- Be set as default application for image files
- Be used via "Open With" context menu

**Manual installation:**
```bash
# System-wide
sudo cp pyprintpreview.desktop /usr/share/applications/
sudo update-desktop-database /usr/share/applications/

# Per-user
cp pyprintpreview.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

### print-photo.nemo_action
Nemo file manager action file. Adds "Print Photo (4x6")" to the right-click context menu for image files.

**Manual installation:**
```bash
# System-wide
sudo cp print-photo.nemo_action /usr/share/nemo/actions/

# Per-user
mkdir -p ~/.local/share/nemo/actions
cp print-photo.nemo_action ~/.local/share/nemo/actions/

# Restart Nemo
nemo -q
```

## Customization

All files are configured for installation to `/opt/PyPrintPreview`. If you need to install to a different location:

1. Edit the paths in each file:
   - `pyprintpreview.desktop`: Change `Exec=/opt/PyPrintPreview/pyprintpreview.py`
   - `print-photo.nemo_action`: Change `Exec=/opt/PyPrintPreview/pyprintpreview.py`
   - `install.sh`: Change `INSTALL_DIR="/opt/PyPrintPreview"`

2. Run the modified install script or manually copy the files to your chosen location.

## Uninstallation

To remove PyPrintPreview installed via the automated installer:

```bash
sudo rm -rf /opt/PyPrintPreview
sudo rm /usr/share/applications/pyprintpreview.desktop
sudo rm /usr/share/nemo/actions/print-photo.nemo_action
sudo rm /usr/local/bin/pyprintpreview
sudo update-desktop-database /usr/share/applications/
```

For per-user installations, remove from your home directory instead:
```bash
rm ~/.local/share/applications/pyprintpreview.desktop
rm ~/.local/share/nemo/actions/print-photo.nemo_action
update-desktop-database ~/.local/share/applications/
```
