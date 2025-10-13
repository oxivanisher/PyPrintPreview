# Photo Print Preview

A Python GUI application for previewing and printing photos on 4x6" glossy paper with proper formatting and orientation handling.

## Features

- **GUI Preview**: See exactly how your photo will print before printing
- **Smart Orientation**: Automatically detects and handles landscape/portrait images
- **Two Scaling Modes**:
  - **Fill Mode**: Crops image to completely fill the 4x6" paper (no borders)
  - **Fit Mode**: Scales image to fit within paper (may have white borders)
- **EXIF Support**: Automatically rotates images based on EXIF orientation data
- **Saved Preferences**: Remembers your printer selection and preferred scaling mode
- **Borderless Printing**: Configured for 4x6" borderless photo printing
- **Canon Inkjet Support**: Works with Canon photo printers and other compatible printers

## Installation on Linux Mint 22.2

### 1. Install Dependencies

```bash
# Install Python and pip if not already installed
sudo apt update
sudo apt install python3 python3-pip python3-pyqt5 python3-pil

# Or install via pip (recommended for latest versions)
pip3 install -r requirements.txt
```

### 2. Make the Script Executable

```bash
chmod +x pyprintpreview.py
```

### 3. Test the Script

```bash
python3 pyprintpreview.py /path/to/your/photo.jpg
```

## Integration with Nemo File Browser

### Method 1: Add to Context Menu (Right-Click Menu)

1. Create the Nemo actions directory if it doesn't exist:
```bash
mkdir -p ~/.local/share/nemo/actions
```

2. Create a new action file:
```bash
nano ~/.local/share/nemo/actions/print-photo.nemo_action
```

3. Add the following content (adjust the path to your script):
```ini
[Nemo Action]
Name=Print Photo (4x6")
Comment=Preview and print photo on 4x6" glossy paper
Exec=python3 /home/YOUR_USERNAME/Documents/dev/PycharmProjects/PyPrintPreview/pyprintpreview.py %F
Icon-Name=printer
Selection=s
Extensions=jpg;jpeg;png;bmp;gif;tiff;webp;
```

4. Replace `/home/YOUR_USERNAME/` with your actual home directory path:
```bash
sed -i "s|/home/YOUR_USERNAME/|$HOME/|g" ~/.local/share/nemo/actions/print-photo.nemo_action
```

5. Restart Nemo:
```bash
nemo -q
```

Now when you right-click on any image file in Nemo, you'll see "Print Photo (4x6")" in the context menu.

### Method 2: Set as Default Application for Images

1. Create a desktop entry:
```bash
mkdir -p ~/.local/share/applications
nano ~/.local/share/applications/pyprintpreview.desktop
```

2. Add the following content:
```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Photo Print Preview
Comment=Preview and print photos on 4x6" glossy paper
Exec=python3 /home/YOUR_USERNAME/Documents/dev/PycharmProjects/PyPrintPreview/pyprintpreview.py %f
Icon=printer
Terminal=false
Categories=Graphics;Photography;Printing;
MimeType=image/jpeg;image/png;image/bmp;image/gif;image/tiff;image/webp;
```

3. Replace the path with your actual path:
```bash
sed -i "s|/home/YOUR_USERNAME/|$HOME/|g" ~/.local/share/applications/pyprintpreview.desktop
```

4. Update desktop database:
```bash
update-desktop-database ~/.local/share/applications
```

5. Now you can right-click any image → "Open With" → "Photo Print Preview"

To set it as the default application for images:
```bash
xdg-mime default pyprintpreview.desktop image/jpeg
xdg-mime default pyprintpreview.desktop image/png
```

## Usage

### From Command Line
```bash
# Open with a specific image
python3 pyprintpreview.py /path/to/photo.jpg

# Or just open the GUI
python3 pyprintpreview.py
```

### From Nemo
1. Right-click on any image file
2. Select "Print Photo (4x6")" from the context menu
3. Choose your scaling mode (Fill or Fit)
4. Select your printer
5. Click "Print"

## Configuration

The application saves your preferences in:
```
~/.config/pyprintpreview/settings.json
```

This includes:
- Last selected printer
- Preferred scaling mode (fill/fit)
- Paper size settings

## Scaling Modes Explained

### Fill Mode (Recommended for most photos)
- Crops the image to exactly fill the 4x6" paper
- No white borders
- Some parts of the image may be cropped
- Best for modern smartphone photos (16:9, 9:16 aspect ratios)

### Fit Mode
- Scales the entire image to fit on the paper
- May have white borders on top/bottom or sides
- No cropping - entire image is visible
- Best for photos already in 2:3 aspect ratio

## Printer Setup Tips for Canon Inkjet

When the print dialog opens:
1. Select your Canon printer
2. Look for "Properties" or "Preferences"
3. Set these options:
   - **Media Type**: Photo Paper Pro Platinum (or Glossy Photo Paper)
   - **Paper Size**: 4x6" (101.6 x 152.4 mm) or "4x6 Borderless"
   - **Quality**: High or Best
   - **Borderless**: Enable if available

These settings should be remembered by the system for future prints.

## Troubleshooting

### Script doesn't run
- Make sure it's executable: `chmod +x pyprintpreview.py`
- Check Python version: `python3 --version` (should be 3.6+)
- Verify dependencies: `pip3 list | grep -E "PyQt5|Pillow"`

### Image appears rotated incorrectly
- The script reads EXIF orientation data automatically
- If still incorrect, try opening the image in an image editor and saving it again

### Print is too small/large
- Make sure your printer is set to 4x6" paper size
- Check "Fit to page" is NOT selected in printer dialog
- Use "Actual Size" or "100%" scaling in printer settings

### Context menu doesn't appear
- Make sure the .nemo_action file is in the correct directory
- Restart Nemo: `nemo -q`
- Check file has correct permissions: `ls -l ~/.local/share/nemo/actions/`

### PyQt5 import errors
- Try installing system package: `sudo apt install python3-pyqt5`
- Or use pip: `pip3 install PyQt5`

## License

This script is provided as-is for personal use.

## Requirements

- Python 3.6+
- PyQt5 5.15+
- Pillow 9.0+
- Linux (tested on Linux Mint 22.2)
