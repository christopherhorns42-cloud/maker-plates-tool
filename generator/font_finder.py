"""
Font Finder - Locates font files on Windows for Maker Plates generator.
Searches Windows Fonts directory and Adobe Creative Cloud font directories.
"""

import os
import glob

# Map of font display names to search patterns
FONT_SEARCH_MAP = {
    # Windows filename patterns (case-insensitive substring match against filename)
    "Times New Roman": ["times.ttf", "timesnewroman", "times new roman", "timesnr"],
    "Arial": ["arial.ttf", "arialmt", "arial"],
    "Old English": ["oldengl", "oldeng", "old english", "engrossedtext"],
    "Century Gothic": ["gothic.ttf", "centurygothic", "century gothic"],
    "Broadway": ["broadw", "broadway"],
    "Myriad Pro": ["myriadpro", "myriad pro", "myriad"],
    "Comic Sans": ["comic.ttf", "comicsans", "comic sans"],
    "Cortado": ["cortado"],
    "Mr. Dafoe": ["mrdafoe", "mr dafoe"],
    "Niconne": ["niconne"],
    "Adage Script": ["adagescript", "adage script", "adage"],
    "Stencil": ["stencil.ttf", "stencil"],
    "Univia Pro": ["univiapro", "univia pro", "univia"],
}

# Fallback fonts for when a font can't be found
FALLBACK_MAP = {
    "Times New Roman": "Times New Roman",
    "Arial": "Arial",
    "Old English": "Arial",
    "Century Gothic": "Arial",
    "Broadway": "Arial",
    "Myriad Pro": "Arial",
    "Comic Sans": "Arial",
    "Cortado": "Arial",
    "Mr. Dafoe": "Arial",
    "Niconne": "Arial",
    "Adage Script": "Arial",
    "Stencil": "Arial",
    "Univia Pro": "Arial",
}

def get_font_search_dirs():
    """Return list of directories to search for font files."""
    dirs = []
    
    # Windows system fonts
    windows_fonts = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    if os.path.isdir(windows_fonts):
        dirs.append(windows_fonts)
    
    # User fonts (Windows 10+)
    user_fonts = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")
    if os.path.isdir(user_fonts):
        dirs.append(user_fonts)
    
    # Adobe Creative Cloud / CoreSync fonts
    local_app = os.environ.get("LOCALAPPDATA", "")
    adobe_coresync = os.path.join(local_app, "Adobe", "CoreSync", "plugins", "livetype")
    if os.path.isdir(adobe_coresync):
        # Adobe fonts can be nested in subdirectories
        for root, subdirs, files in os.walk(adobe_coresync):
            dirs.append(root)
    
    # Adobe Illustrator bundled fonts
    program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
    for ai_version in ["Adobe Illustrator 2024", "Adobe Illustrator 2023", "Adobe Illustrator 2022",
                        "Adobe Illustrator 2021", "Adobe Illustrator CC 2020", "Adobe Illustrator CC 2019"]:
        ai_fonts = os.path.join(program_files, "Adobe", ai_version,
                                "Support Files", "Contents", "Windows", "Resources",
                                "TypeSupport", "Unicode", "Reqd")
        if os.path.isdir(ai_fonts):
            dirs.append(ai_fonts)
    
    return dirs

def find_font_file(font_name):
    """
    Find the font file path for a given font display name.
    Returns (path, actual_name) or (None, None) if not found.
    """
    search_patterns = FONT_SEARCH_MAP.get(font_name, [font_name.lower()])
    search_dirs = get_font_search_dirs()
    
    for search_dir in search_dirs:
        try:
            all_fonts = []
            for ext in ["*.ttf", "*.otf", "*.TTF", "*.OTF"]:
                all_fonts.extend(glob.glob(os.path.join(search_dir, ext)))
            
            for font_path in all_fonts:
                fname = os.path.basename(font_path).lower()
                for pattern in search_patterns:
                    if pattern.lower() in fname:
                        return font_path, font_name
        except (PermissionError, OSError):
            continue
    
    return None, None

def get_all_available_fonts():
    """
    Returns dict of {font_display_name: font_file_path} for all fonts in FONT_SEARCH_MAP.
    Fonts not found get None as the path.
    """
    result = {}
    for font_name in FONT_SEARCH_MAP:
        path, _ = find_font_file(font_name)
        result[font_name] = path
    return result

def get_font_status():
    """Returns a human-readable status of all fonts - found or missing."""
    available = get_all_available_fonts()
    status = []
    for name, path in available.items():
        status.append({
            "name": name,
            "found": path is not None,
            "path": path or "Not found"
        })
    return status
