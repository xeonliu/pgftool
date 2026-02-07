"""Convert TrueType font to PGF format."""

import sys
import freetype
from .pgf_font import PGFFont, PGFGlyph, PGFHeader, F26Pairs
from .pgf_writer import save_pgf
from .pgf_reader import load_ucs_list


def face_to_pgf(face: freetype.Face, pgft: PGFFont):
    """Convert FreeType face metadata to PGF header."""
    h_size = face.size.x_ppem
    h_res = 128
    
    pgft.header.h_res = h_res << 6
    pgft.header.v_res = h_res << 6
    pgft.header.h_size = (h_size << 6) * 72 // h_res
    pgft.header.v_size = (h_size << 6) * 72 // h_res
    
    # Set font name
    if face.family_name:
        pgft.header.font_name = face.family_name.decode('utf-8', errors='ignore')
    else:
        pgft.header.font_name = "Dummy Font"
    
    if face.style_name:
        pgft.header.font_type = face.style_name.decode('utf-8', errors='ignore')
    else:
        pgft.header.font_type = "Regular"
    
    # Use fixed values for ascender/descender
    pgft.header.ascender = 0x000003f5
    pgft.header.descender = 0xffffff75


def load_ttf_glyph(face: freetype.Face, ucs: int) -> dict:
    """Load a glyph from TrueType font."""
    try:
        face.load_char(ucs, freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_NO_BITMAP)
    except (freetype.FT_Exception, Exception):
        return None
    
    if face.glyph.format != freetype.FT_GLYPH_FORMAT_BITMAP:
        try:
            face.glyph.render_mode = freetype.FT_RENDER_MODE_NORMAL
        except (freetype.FT_Exception, Exception):
            pass
    
    bitmap = face.glyph.bitmap
    metrics = face.glyph.metrics
    
    width = bitmap.width
    height = bitmap.rows
    left = face.glyph.bitmap_left
    top = face.glyph.bitmap_top
    pitch = bitmap.pitch
    
    # Convert bitmap to 4-bit grayscale
    bmp_data = bytearray(width * height)
    if bitmap.buffer:
        for v in range(height):
            for h in range(width):
                src_idx = v * abs(pitch) + h
                dst_idx = v * width + h
                if src_idx < len(bitmap.buffer):
                    # Convert 8-bit to 4-bit
                    bmp_data[dst_idx] = bitmap.buffer[src_idx] >> 4
    
    return {
        'ucs': ucs,
        'width': width,
        'height': height,
        'left': left,
        'top': top,
        'dimension': F26Pairs(metrics.width, metrics.height),
        'bearingX': F26Pairs(metrics.horiBearingX, metrics.vertBearingX),
        'bearingY': F26Pairs(metrics.horiBearingY, metrics.vertBearingY),
        'advance': F26Pairs(metrics.horiAdvance, metrics.vertAdvance),
        'bmp': bytes(bmp_data)
    }


def main():
    """Main entry point for ttf_pgf."""
    if len(sys.argv) < 3:
        print("Usage: ttf_pgf {xxx.ttf} {out.pgf} [unicode list]")
        return 0
    
    ttf_file = sys.argv[1]
    pgf_file = sys.argv[2]
    ucs_list_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Load UCS list
    ucs_list = [0] * 65536
    if ucs_list_file:
        ucs_list = load_ucs_list(ucs_list_file)
    else:
        for i in range(65536):
            ucs_list[i] = 1
    
    # Load TrueType font
    try:
        face = freetype.Face(ttf_file)
        face.set_pixel_sizes(18, 18)  # 18x18 TrueType
    except Exception as e:
        print(f"Error loading TTF font: {e}")
        return -1
    
    # Load all glyphs
    glist = {}
    for i in range(65536):
        if ucs_list[i]:
            ttf_glyph = load_ttf_glyph(face, i)
            if ttf_glyph:
                glist[i] = ttf_glyph
    
    # Create PGF font
    pgft = PGFFont()
    pgft.header = PGFHeader()
    face_to_pgf(face, pgft)
    
    # Convert TTF glyphs to PGF glyphs
    for ucs, ttf_glyph in glist.items():
        glyph = PGFGlyph()
        glyph.ucs = ttf_glyph['ucs']
        glyph.width = ttf_glyph['width']
        glyph.height = ttf_glyph['height']
        glyph.left = ttf_glyph['left']
        glyph.top = ttf_glyph['top']
        glyph.dimension = ttf_glyph['dimension']
        glyph.bearingX = ttf_glyph['bearingX']
        glyph.bearingY = ttf_glyph['bearingY']
        glyph.advance = ttf_glyph['advance']
        glyph.bmp = ttf_glyph['bmp']
        pgft.char_glyph[ucs] = glyph
    
    # Save PGF
    save_pgf(pgft, pgf_file)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
