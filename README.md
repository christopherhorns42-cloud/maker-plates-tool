# Maker Plates – Design Generator

A local web app for generating laser-ready design files from customer order details.
Runs on your Windows machine and uses your locally installed fonts (including Adobe Fonts).

## Setup (First Time Only)

1. Install Python from https://python.org  
   ⚠️ During install, check **"Add Python to PATH"**

2. Double-click **install.bat** to install dependencies

## Running the App

Double-click **start.bat** — your browser will open automatically to http://localhost:5000

## How to Use

1. Fill in the order details (material, size, corner style, font, text)
2. Click **Download EPS** (recommended for fiber laser) or **DXF** as alternative
3. Load the file into your laser software and engrave

## Output Formats

| Format | Best For |
|--------|----------|
| **EPS** | Fiber laser (primary format) |
| **DXF** | Alternative for fiber laser |
| **SVG** | Preview in browser / import to Illustrator |

## Text Tips

- Use **Enter** or **/** to create multiple lines of text
- Text is automatically sized to fit the plate with 10% margins
- Font is auto-detected from your system (including Adobe CC fonts)

## Font Status

Visit http://localhost:5000/font-status to see which fonts were found on your machine.
Any missing fonts will fall back to Helvetica until located.

## File Structure

```
maker-plates-tool/
├── app.py              Main application
├── generator/
│   ├── plate_generator.py   EPS/DXF/SVG generation logic
│   └── font_finder.py       Windows font detection
├── templates/          HTML pages
├── install.bat         First-time setup
├── start.bat           Launch the app
└── requirements.txt    Python dependencies
```
