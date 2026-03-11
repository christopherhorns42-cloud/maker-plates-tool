"""
Plate Generator - Core logic for generating laser-ready EPS and DXF files.
Produces vector files with plate outline + centered text for fiber laser engraving.
"""

import os
import math
import tempfile
from io import BytesIO

# ReportLab imports for EPS/SVG output
from reportlab.graphics.shapes import Drawing, Rect, Path, String, Group, Line
from reportlab.graphics import renderPS, renderSVG
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# DXF output
import ezdxf
from ezdxf.enums import TextEntityAlignment

from .font_finder import find_font_file, FONT_SEARCH_MAP

# Font registration cache
_registered_fonts = {}

POINTS_PER_INCH = 72.0
MARGIN_RATIO = 0.10  # 10% margin on each side


def register_font(font_name):
    """Register a font with ReportLab. Returns the reportlab font name to use."""
    if font_name in _registered_fonts:
        return _registered_fonts[font_name]

    font_path, _ = find_font_file(font_name)
    if font_path:
        try:
            safe_name = font_name.replace(" ", "_").replace(".", "_")
            pdfmetrics.registerFont(TTFont(safe_name, font_path))
            _registered_fonts[font_name] = safe_name
            return safe_name
        except Exception as e:
            print(f"Warning: Could not register font '{font_name}': {e}")

    # Fallback to Helvetica (built into ReportLab)
    _registered_fonts[font_name] = "Helvetica"
    return "Helvetica"


def measure_text(text, font_name, font_size):
    """Measure text width in points using ReportLab."""
    try:
        return pdfmetrics.stringWidth(text, font_name, font_size)
    except Exception:
        # Rough estimate if measurement fails
        return len(text) * font_size * 0.6


def auto_size_font(lines, font_name, max_width_pt, max_height_pt):
    """
    Find the largest font size where all lines fit within max_width_pt x max_height_pt.
    Returns font_size in points.
    """
    line_spacing_ratio = 1.3  # line height = font_size * ratio

    for font_size in range(200, 4, -1):
        total_height = font_size * line_spacing_ratio * len(lines)
        if total_height > max_height_pt:
            continue
        max_line_width = max(measure_text(line, font_name, font_size) for line in lines)
        if max_line_width <= max_width_pt:
            return font_size

    return 4  # minimum


def parse_text_lines(text):
    """Split personalization text into lines, handling both \n and / as line breaks."""
    lines = []
    for raw_line in text.replace('\\n', '\n').split('\n'):
        for sub in raw_line.split('/'):
            stripped = sub.strip()
            if stripped:
                lines.append(stripped)
    return lines if lines else [""]


def make_plate_outline_path(w, h, corner_style):
    """
    Create a ReportLab Path for the plate outline based on corner style.
    w, h are in points. Returns a Path object.
    """
    notch = min(w, h) * 0.06  # notch size = 6% of smaller dimension
    radius = min(w, h) * 0.08  # round corner radius

    path = Path(fillColor=None, strokeColor=colors.black, strokeWidth=1.0)

    if corner_style == "Square":
        path.moveTo(0, 0)
        path.lineTo(w, 0)
        path.lineTo(w, h)
        path.lineTo(0, h)
        path.closePath()

    elif corner_style == "Round":
        r = radius
        # Start bottom-left, going clockwise
        path.moveTo(r, 0)
        path.lineTo(w - r, 0)
        path.curveTo(w - r + r * 0.552, 0, w, r - r * 0.552, w, r)
        path.lineTo(w, h - r)
        path.curveTo(w, h - r + r * 0.552, w - r + r * 0.552, h, w - r, h)
        path.lineTo(r, h)
        path.curveTo(r - r * 0.552, h, 0, h - r + r * 0.552, 0, h - r)
        path.lineTo(0, r)
        path.curveTo(0, r - r * 0.552, r - r * 0.552, 0, r, 0)
        path.closePath()

    elif corner_style == "Notched":
        n = notch
        path.moveTo(n, 0)
        path.lineTo(w - n, 0)
        path.lineTo(w, n)
        path.lineTo(w, h - n)
        path.lineTo(w - n, h)
        path.lineTo(n, h)
        path.lineTo(0, h - n)
        path.lineTo(0, n)
        path.closePath()

    else:
        # Default to square
        path.moveTo(0, 0)
        path.lineTo(w, 0)
        path.lineTo(w, h)
        path.lineTo(0, h)
        path.closePath()

    return path


def generate_eps(order):
    """
    Generate a laser-ready EPS file from order data.
    
    order dict keys:
        width_in    - plate width in inches (float)
        height_in   - plate height in inches (float)
        orientation - "Horizontal" or "Vertical"
        corner      - "Square", "Round", or "Notched"
        font        - Font display name (string)
        text        - Personalization text (string)
    
    Returns EPS content as bytes.
    """
    width_in = float(order["width_in"])
    height_in = float(order["height_in"])

    # Swap dimensions if vertical
    if order.get("orientation") == "Vertical" and width_in > height_in:
        width_in, height_in = height_in, width_in

    w = width_in * POINTS_PER_INCH
    h = height_in * POINTS_PER_INCH

    # Register the font
    font_name = order.get("font", "Arial")
    rl_font = register_font(font_name)

    # Parse text lines
    lines = parse_text_lines(order.get("text", ""))

    # Calculate usable text area with margin
    margin_x = w * MARGIN_RATIO
    margin_y = h * MARGIN_RATIO
    text_w = w - 2 * margin_x
    text_h = h - 2 * margin_y

    # Auto-size font
    font_size = auto_size_font(lines, rl_font, text_w, text_h)
    line_height = font_size * 1.3

    # Build the drawing
    drawing = Drawing(w, h)

    # Plate outline
    outline = make_plate_outline_path(w, h, order.get("corner", "Square"))
    drawing.add(outline)

    # Place text lines centered
    total_text_height = line_height * len(lines) - (line_height - font_size)
    y_start = h / 2 + total_text_height / 2 - font_size

    for i, line in enumerate(lines):
        line_width = measure_text(line, rl_font, font_size)
        x = (w - line_width) / 2
        y = y_start - i * line_height

        s = String(x, y, line,
                   fontName=rl_font,
                   fontSize=font_size,
                   fillColor=colors.black)
        drawing.add(s)

    # Render to EPS bytes
    buf = BytesIO()
    renderPS.drawToFile(drawing, buf)
    return buf.getvalue()


def generate_dxf(order):
    """
    Generate a laser-ready DXF file from order data.
    Returns DXF content as string.
    """
    width_in = float(order["width_in"])
    height_in = float(order["height_in"])

    if order.get("orientation") == "Vertical" and width_in > height_in:
        width_in, height_in = height_in, width_in

    # DXF in inches
    w = width_in
    h = height_in
    notch = min(w, h) * 0.06
    radius = min(w, h) * 0.08
    corner = order.get("corner", "Square")

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Draw plate outline
    if corner == "Square":
        points = [(0, 0), (w, 0), (w, h), (0, h), (0, 0)]
        msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "OUTLINE"})

    elif corner == "Round":
        # Use polyline with bulge for rounded corners (approximation)
        # For simplicity, use a spline approximation
        r = radius
        # Approximate with many segments
        pts = _rounded_rect_points(w, h, r)
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "OUTLINE"})

    elif corner == "Notched":
        n = notch
        points = [
            (n, 0), (w - n, 0), (w, n), (w, h - n),
            (w - n, h), (n, h), (0, h - n), (0, n), (n, 0)
        ]
        msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "OUTLINE"})

    # Add text
    font_name = order.get("font", "Arial")
    lines = parse_text_lines(order.get("text", ""))

    margin_x = w * MARGIN_RATIO
    margin_y = h * MARGIN_RATIO
    text_area_w = w - 2 * margin_x
    text_area_h = h - 2 * margin_y

    # Estimate font size in inches (roughly 72 pts = 1 inch)
    rl_font = register_font(font_name)
    font_size_pt = auto_size_font(lines, rl_font, text_area_w * POINTS_PER_INCH, text_area_h * POINTS_PER_INCH)
    font_size_in = font_size_pt / POINTS_PER_INCH

    line_height_in = font_size_in * 1.3
    total_height = line_height_in * len(lines)
    y_start = h / 2 + total_height / 2 - font_size_in

    for i, line in enumerate(lines):
        y_pos = y_start - i * line_height_in
        msp.add_text(
            line,
            dxfattribs={
                "layer": "TEXT",
                "height": font_size_in,
                "style": "Standard",
                "halign": 4,  # Middle center alignment
                "insert": (w / 2, y_pos),
                "align_point": (w / 2, y_pos),
            }
        )

    import io
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode('utf-8')


def _rounded_rect_points(w, h, r, segments=8):
    """Generate points for a rectangle with rounded corners."""
    points = []
    corners = [
        (r, r, 180, 270),           # bottom-left
        (w - r, r, 270, 360),        # bottom-right
        (w - r, h - r, 0, 90),       # top-right
        (r, h - r, 90, 180),         # top-left
    ]
    for cx, cy, start_angle, end_angle in corners:
        for j in range(segments + 1):
            angle = math.radians(start_angle + (end_angle - start_angle) * j / segments)
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return points


def generate_svg(order):
    """
    Generate an SVG file from order data (useful for preview or Illustrator import).
    Returns SVG content as bytes.
    """
    width_in = float(order["width_in"])
    height_in = float(order["height_in"])

    if order.get("orientation") == "Vertical" and width_in > height_in:
        width_in, height_in = height_in, width_in

    w = width_in * POINTS_PER_INCH
    h = height_in * POINTS_PER_INCH

    font_name = order.get("font", "Arial")
    rl_font = register_font(font_name)
    lines = parse_text_lines(order.get("text", ""))

    margin_x = w * MARGIN_RATIO
    margin_y = h * MARGIN_RATIO
    text_w = w - 2 * margin_x
    text_h = h - 2 * margin_y

    font_size = auto_size_font(lines, rl_font, text_w, text_h)
    line_height = font_size * 1.3

    drawing = Drawing(w, h)
    outline = make_plate_outline_path(w, h, order.get("corner", "Square"))
    drawing.add(outline)

    total_text_height = line_height * len(lines) - (line_height - font_size)
    y_start = h / 2 + total_text_height / 2 - font_size

    for i, line in enumerate(lines):
        line_width = measure_text(line, rl_font, font_size)
        x = (w - line_width) / 2
        y = y_start - i * line_height
        s = String(x, y, line, fontName=rl_font, fontSize=font_size, fillColor=colors.black)
        drawing.add(s)

    import io
    buf = io.StringIO()
    renderSVG.drawToFile(drawing, buf)
    return buf.getvalue().encode('utf-8')
