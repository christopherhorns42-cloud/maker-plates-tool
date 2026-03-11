"""
Maker Plates - Design File Generator
A local web app for generating laser-ready EPS/DXF files from order details.
"""

from flask import Flask, render_template, request, send_file, jsonify
from io import BytesIO
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from generator.plate_generator import generate_eps, generate_dxf, generate_svg
from generator.font_finder import get_font_status

app = Flask(__name__)

# All plate size options matching the Shopify store
PLATE_SIZES = [
    '2.5" x 1"', '2" x 2"',
    '3" x 1"', '3" x 1.5"', '3" x 2"', '3" x 2.5"', '3" x 3"',
    '4" x 1"', '4" x 1.5"', '4" x 2"', '4" x 2.5"', '4" x 3"', '4" x 3.5"', '4" x 4"',
    '5" x 2"', '5" x 2.5"', '5" x 3"', '5" x 3.5"', '5" x 4"', '5" x 4.5"', '5" x 5"',
    '6" x 2"', '6" x 2.5"', '6" x 3"', '6" x 3.5"', '6" x 4"', '6" x 4.5"', '6" x 5"', '6" x 6"',
    '7" x 2"', '7" x 2.5"', '7" x 3"', '7" x 3.5"', '7" x 4"', '7" x 4.5"', '7" x 5"', '7" x 5.5"', '7" x 6"', '7" x 6.5"', '7" x 7"',
    '8" x 2"', '8" x 2.5"', '8" x 3"', '8" x 3.5"', '8" x 4"', '8" x 4.5"', '8" x 5"', '8" x 5.5"', '8" x 6"', '8" x 6.5"', '8" x 7"', '8" x 7.5"', '8" x 8"',
    '9" x 2"', '9" x 2.5"', '9" x 3"', '9" x 3.5"', '9" x 4"', '9" x 4.5"', '9" x 5"', '9" x 5.5"', '9" x 6"', '9" x 6.5"', '9" x 7"', '9" x 7.5"', '9" x 8"', '9" x 8.5"', '9" x 9"',
    '10" x 2"', '10" x 2.5"', '10" x 3"', '10" x 3.5"', '10" x 4"', '10" x 4.5"', '10" x 5"', '10" x 5.5"', '10" x 6"', '10" x 6.5"', '10" x 7"', '10" x 7.5"', '10" x 8"', '10" x 8.5"', '10" x 9"', '10" x 9.5"', '10" x 10"',
]

FONTS = [
    "Times New Roman", "Arial", "Old English", "Century Gothic",
    "Broadway", "Myriad Pro", "Comic Sans", "Cortado",
    "Mr. Dafoe", "Adage Script", "Niconne", "Stencil", "Univia Pro"
]

MATERIALS = {
    "Brass": ["Polished Gold", "Gloss Black", "Brushed Gold"],
    "Aluminum": ["Polished Silver", "Gloss Black", "DuraBlack Matte"],
    "Acrylic": ["Black", "White", "Red", "Blue", "Sky Blue", "Pink",
                "Yellow", "Maroon", "Khaki", "Purple", "Forest Green",
                "Light Green", "Orange", "Gray"],
}

CORNER_STYLES = ["Square", "Round", "Notched"]
ORIENTATIONS = ["Horizontal", "Vertical"]
MOUNTING = ["No Holes or Adhesive", "2 Holes Middle", "4 Holes Corners", "Adhesive Tape Backing"]


def parse_size(size_str):
    """Parse a size string like '4" x 2"' into (width, height) floats."""
    try:
        size_str = size_str.replace('"', '').replace("'", '')
        parts = [p.strip() for p in size_str.split('x')]
        width = float(parts[0].replace(' ', '').replace('1/2', '.5').replace('1/4', '.25'))
        height = float(parts[1].replace(' ', '').replace('1/2', '.5').replace('1/4', '.25'))
        return width, height
    except Exception:
        return 4.0, 2.0  # safe default


@app.route('/')
def index():
    return render_template('index.html',
                           plate_sizes=PLATE_SIZES,
                           fonts=FONTS,
                           materials=MATERIALS,
                           corner_styles=CORNER_STYLES,
                           orientations=ORIENTATIONS,
                           mounting=MOUNTING)


@app.route('/generate', methods=['POST'])
def generate():
    """Generate a design file from form data."""
    try:
        data = request.form
        size_str = data.get('size', '4" x 2"')
        width_in, height_in = parse_size(size_str)

        order = {
            "width_in": width_in,
            "height_in": height_in,
            "orientation": data.get('orientation', 'Horizontal'),
            "corner": data.get('corner', 'Square'),
            "font": data.get('font', 'Arial'),
            "text": data.get('text', ''),
            "material": data.get('material', ''),
            "finish": data.get('finish', ''),
            "mounting": data.get('mounting', ''),
            "notes": data.get('notes', ''),
        }

        output_format = data.get('format', 'eps').lower()

        # Generate the requested file format
        if output_format == 'eps':
            content = generate_eps(order)
            filename = f"plate_{size_str.replace('\"','').replace(' ','')}.eps"
            mimetype = 'application/postscript'
        elif output_format == 'dxf':
            content = generate_dxf(order)
            filename = f"plate_{size_str.replace('\"','').replace(' ','')}.dxf"
            mimetype = 'application/dxf'
        elif output_format == 'svg':
            content = generate_svg(order)
            filename = f"plate_{size_str.replace('\"','').replace(' ','')}.svg"
            mimetype = 'image/svg+xml'
        else:
            return jsonify({"error": "Invalid format. Use eps, dxf, or svg."}), 400

        return send_file(
            BytesIO(content),
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route('/font-status')
def font_status():
    """Check which fonts are found on this system."""
    status = get_font_status()
    return render_template('font_status.html', fonts=status)


@app.route('/api/finishes')
def get_finishes():
    """Return finish options for a given material (AJAX)."""
    material = request.args.get('material', 'Brass')
    finishes = MATERIALS.get(material, [])
    return jsonify(finishes)


if __name__ == '__main__':
    print("=" * 50)
    print("  Maker Plates Design Generator")
    print("  Open your browser to: http://localhost:5000")
    print("  Press Ctrl+C to stop")
    print("=" * 50)
    app.run(debug=False, host='127.0.0.1', port=5000)
