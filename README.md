# Photo Print Preview

A Python GUI application for previewing and printing photos on 4x6" glossy paper with proper formatting and orientation handling.

## Features

- **GUI Preview**: See exactly how your photo will print before printing
- **Smart Orientation**: Automatically detects and handles landscape/portrait images
- **Two Scaling Modes**:
  - **Fill Mode**: Crops image to completely fill the 4x6" paper (no borders)
  - **Fit Mode**: Scales image to fit within paper (may have white borders)
- **EXIF Support**: Automatically rotates images based on EXIF orientation data
- **Saved Preferences**: Remembers your printer selection, scaling mode, and printer settings
- **Canon PIXMA Support**: Special handling for Canon PIXMA printers with configurable orientation and paper source
- **Borderless Printing**: Configured for 4x6" borderless photo printing
- **Multilingual**: English and German interface with automatic language detection

## Installation on Linux Mint 22.2

### Quick Install (Recommended)

The easiest way to install PyPrintPreview is to use the automated installer, which will:
- Install all dependencies
- Copy files to `/opt/PyPrintPreview`
- Set up desktop integration and Nemo context menu
- Create a symlink for command-line access

```bash
cd /path/to/PyPrintPreview
sudo ./dist/install.sh
```

After installation, you can run:
```bash
pyprintpreview /path/to/your/photo.jpg
```

### Manual Installation

If you prefer to run from the source directory:

1. **Install Dependencies**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-pyqt5 python3-pil
```

2. **Make the Script Executable**
```bash
chmod +x pyprintpreview.py
```

3. **Test the Script**
```bash
python3 pyprintpreview.py /path/to/your/photo.jpg
```

## Integration with Nemo File Browser

**Note:** If you used the automated installer (`dist/install.sh`), desktop integration is already set up system-wide and you can skip this section.

### Manual Integration

For manual installations or per-user configuration:

#### Context Menu (Right-Click Menu)

Copy the Nemo action file to your user directory:
```bash
mkdir -p ~/.local/share/nemo/actions
cp dist/print-photo.nemo_action ~/.local/share/nemo/actions/
```

If running from a custom location (not `/opt/PyPrintPreview`), edit the file to update the path:
```bash
nano ~/.local/share/nemo/actions/print-photo.nemo_action
# Change the Exec= line to point to your pyprintpreview.py location
```

Restart Nemo:
```bash
nemo -q
```

#### Desktop Entry (Open With / Default Application)

Copy the desktop entry file:
```bash
mkdir -p ~/.local/share/applications
cp dist/pyprintpreview.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications
```

To set as default application for images:
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
- Force portrait orientation setting (for Canon PIXMA compatibility)
- Paper source selection (rear/front tray)
- Language preference (English/German)
- Paper size settings

Example configuration:
```json
{
  "printer_name": "Canon-PIXMA-TS3400",
  "last_scale_mode": "fill",
  "paper_size": "4x6",
  "borderless": true,
  "quality": "high",
  "language": "en",
  "force_portrait": true,
  "paper_source": "rear"
}
```

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

### Canon PIXMA Printer Issues

#### Landscape photos print incorrectly or print on the drum

**Solution:** Make sure the **"Always use portrait orientation (Canon PIXMA)"** checkbox is **checked** in the application (this is the default setting).

Canon PIXMA printers require:
- Photo paper inserted in **portrait mode** in the rear tray
- Print jobs sent in **portrait orientation** (even for landscape photos)
- The application handles image rotation internally

If you've unchecked this option, re-enable it and try printing again.

#### Printer shows "Wrong paper size" warning

The printer is expecting a different paper configuration. Try these steps:

1. **Check CUPS printer settings:**
   ```bash
   lpstat -p -d
   lpoptions -p YourCanonPrinterName -l | grep PageSize
   ```

2. **Set paper size explicitly in CUPS:**
   ```bash
   # For 4x6" paper (102x152mm)
   lpoptions -p YourCanonPrinterName -o media=w288h432
   # Or try these Canon-specific sizes:
   lpoptions -p YourCanonPrinterName -o PageSize=w288h432
   lpoptions -p YourCanonPrinterName -o PageSize=4x6
   ```

3. **Specify rear tray as paper source:**

   In the application, use the **"Paper Source"** dropdown and select **"Rear Tray"**.

   Or set it via CUPS:
   ```bash
   lpoptions -p YourCanonPrinterName -o InputSlot=Rear
   # Some Canon drivers use:
   lpoptions -p YourCanonPrinterName -o InputSlot=RearTray
   ```

4. **Check Canon driver settings:**
   ```bash
   # View all available options for your printer
   lpoptions -p YourCanonPrinterName -l

   # Look for media type options
   lpoptions -p YourCanonPrinterName -o MediaType=PhotopaperPro
   # or
   lpoptions -p YourCanonPrinterName -o MediaType=Glossy
   ```

5. **Reset printer configuration:**
   ```bash
   # Remove all custom options
   lpoptions -p YourCanonPrinterName -r media
   lpoptions -p YourCanonPrinterName -r PageSize
   lpoptions -p YourCanonPrinterName -r InputSlot

   # Then set them fresh
   lpoptions -p YourCanonPrinterName -o PageSize=4x6
   lpoptions -p YourCanonPrinterName -o InputSlot=Rear
   ```

6. **Use the print dialog settings:**

   When the print dialog opens:
   - Click "Properties" or "Preferences"
   - Manually select "4x6" or "101.6 x 152.4 mm" paper size
   - Select "Photo Paper Pro Platinum" or "Glossy Photo Paper" as media type
   - Enable "Borderless" if available
   - These settings should persist for future prints

#### Still having issues?

Check your configuration file at `~/.config/pyprintpreview/settings.json`:

```bash
cat ~/.config/pyprintpreview/settings.json
```

It should contain:
```json
{
  "force_portrait": true,
  "paper_source": "auto"
}
```

If `force_portrait` is `false`, change it to `true` or delete the file to reset to defaults.

### General Troubleshooting

#### Script doesn't run
- Make sure it's executable: `chmod +x pyprintpreview.py`
- Check Python version: `python3 --version` (should be 3.6+)
- Verify dependencies: `pip3 list | grep -E "PyQt5|Pillow"`

#### Image appears rotated incorrectly
- The script reads EXIF orientation data automatically
- If still incorrect, try opening the image in an image editor and saving it again

#### Print is too small/large
- Make sure your printer is set to 4x6" paper size
- Check "Fit to page" is NOT selected in printer dialog
- Use "Actual Size" or "100%" scaling in printer settings

#### Context menu doesn't appear
- Make sure the .nemo_action file is in the correct directory
- Restart Nemo: `nemo -q`
- Check file has correct permissions: `ls -l ~/.local/share/nemo/actions/`

#### PyQt5 import errors
- Try installing system package: `sudo apt install python3-pyqt5`
- Or use pip: `pip3 install PyQt5`

## License

This script is provided as-is for personal use.

## Requirements

- Python 3.6+
- PyQt5 5.15+
- Pillow 9.0+
- Linux (tested on Linux Mint 22.2)
