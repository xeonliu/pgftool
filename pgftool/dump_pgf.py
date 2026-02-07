"""Dump PGF font information and bitmaps."""

import os
import sys
import struct
from typing import Optional
from .pgf_reader import load_pgf_font
from .pgf_font import PGFFont, PGFGlyph


def put_f26(value: int) -> str:
    """Convert 26.6 fixed point to string."""
    return f" {value / 64.0:9.6f}"


def print_header(pgft: PGFFont):
    """Print PGF font header information."""
    h = pgft.header
    if not h:
        return
    
    print("# PGF header:")
    print("# -----------------------------")
    print(f"header_len: {h.header_len:04x}")
    print(f"version   : {h.version}.{h.revision}")
    print(f"font name : {h.font_name}")
    print(f"font type : {h.font_type}")
    print(f"h_size    :{put_f26(h.h_size)}")
    print(f"v_size    :{put_f26(h.v_size)}")
    print(f"ascender  :{put_f26(h.ascender)}")
    print(f"descender :{put_f26(h.descender)}")
    print(f"h_res     :{put_f26(h.h_res)}")
    print(f"v_res     :{put_f26(h.v_res)}")
    print(f"bpp       : {h.bpp}")
    print()
    
    print(f"charmap   : len={h.charmap_len} bpe={h.charmap_bpe}")
    print(f"charptr   : len={h.charptr_len} bpe={h.charptr_bpe} scale={h.charptr_scale}")
    print(f"shadowmap : len={h.shadowmap_len} bpe={h.shadowmap_bpe}")
    print()
    
    print(f"min charmap : {h.charmap_min:04x}")
    print(f"max charmap : {h.charmap_max:04x}")
    print(f"x shadowscale :{put_f26(h.shadowscale_x)}")
    print(f"y shadowscale :{put_f26(h.shadowscale_y)}")
    print()
    
    print(f"max hori_bearingX  :{put_f26(h.max_h_bearingX)}")
    print(f"max hori_bearingY  :{put_f26(h.max_h_bearingY)}")
    print(f"min vert_bearingX  :{put_f26(h.min_v_bearingX)}")
    print(f"max vert_bearingY  :{put_f26(h.max_v_bearingY)}")
    print(f"max hori_advance   :{put_f26(h.max_h_advance)}")
    print(f"max vert_advance   :{put_f26(h.max_v_advance)}")
    print(f"max hori_dimension :{put_f26(h.max_h_dimension)}")
    print(f"max vert_dimension :{put_f26(h.max_v_dimension)}")
    print(f"max glyph width  : {h.max_glyph_w}")
    print(f"max glyph height : {h.max_glyph_h}")
    print()
    
    print(f"dimension table len : {h.dimension_len}")
    print(f"bearingX  table len : {h.bearingX_len}")
    print(f"bearingY  table len : {h.bearingY_len}")
    print(f"advance   table len : {h.advance_len}")
    print()
    print()


def print_dim_table(pgft: PGFFont):
    """Print dimension table."""
    n_dim = len(pgft.dimension)
    print(f"# Dimension table: {n_dim}")
    print("# -----------------------------")
    for i, dim in enumerate(pgft.dimension):
        print(f"{i:3d}: h ={put_f26(dim.h)}    v ={put_f26(dim.v)}")
    print()


def print_bearingX_table(pgft: PGFFont):
    """Print left bearing table."""
    n_bx = len(pgft.bearingX)
    print(f"# Left bearing table: {n_bx}")
    print("# -----------------------------")
    for i, bx in enumerate(pgft.bearingX):
        print(f"{i:3d}: h ={put_f26(bx.h)}    v ={put_f26(bx.v)}")
    print()


def print_bearingY_table(pgft: PGFFont):
    """Print top bearing table."""
    n_by = len(pgft.bearingY)
    print(f"# Top bearing table: {n_by}")
    print("# -----------------------------")
    for i, by in enumerate(pgft.bearingY):
        print(f"{i:3d}: h ={put_f26(by.h)}    v ={put_f26(by.v)}")
    print()


def print_adv_table(pgft: PGFFont):
    """Print advance table."""
    n_adv = len(pgft.advance)
    print(f"# Advance table: {n_adv}")
    print("# -----------------------------")
    for i, adv in enumerate(pgft.advance):
        print(f"{i:3d}: h ={put_f26(adv.h)}    v ={put_f26(adv.v)}")
    print()


def print_shadowmap(pgft: PGFFont):
    """Print shadow map table."""
    n_shadowmap = len(pgft.shadowmap)
    print(f"# Shadow map table: {n_shadowmap}")
    print("# -----------------------------")
    for shadow in pgft.shadowmap:
        print(f"{shadow:04x}")
    print()


def print_charmap(pgft: PGFFont):
    """Print character map."""
    n_charmap = len(pgft.char_glyph)
    print(f"# charmap table: {n_charmap}")
    print("# -----------------------------")
    for ucs in sorted(pgft.char_glyph.keys()):
        print(f"{ucs:04x}")
    print()


def print_charptr(pgft: PGFFont):
    """Print character pointer table."""
    n_charptr = len(pgft.charptr)
    print(f"# charptr table: {n_charptr}")
    print("# -----------------------------")
    for i, ptr in enumerate(pgft.charptr):
        print(f"{i:4x} : {ptr:08x}")
    print()


def print_charinfo(pgft: PGFFont):
    """Print character information."""
    p = 0
    for ucs in sorted(pgft.char_glyph.keys()):
        glyph = pgft.char_glyph[ucs]
        
        print(f"\n---- {p:5d} : U_{ucs:04x} ----")
        print(f"    dimension: h={put_f26(glyph.dimension.h)} v={put_f26(glyph.dimension.v)}")
        print(f"    bearingX : h={put_f26(glyph.bearingX.h)} v={put_f26(glyph.bearingX.v)}")
        print(f"    bearingY : h={put_f26(glyph.bearingY.h)} v={put_f26(glyph.bearingY.v)}")
        print(f"    advance  : h={put_f26(glyph.advance.h)} v={put_f26(glyph.advance.v)}")
        print(f"    bitmap: width={glyph.width} height={glyph.height} left={glyph.left} top={glyph.top}")
        
        if pgft.shadowmap and glyph.shadow_id < len(pgft.shadowmap):
            shadow_ucs = pgft.shadowmap[glyph.shadow_id]
            print(f"    shadow_id: U_{shadow_ucs:04x}  shadow_flag: "
                  f"{(glyph.shadow_flag >> 5) & 3}:{(glyph.shadow_flag >> 3) & 3}:{glyph.shadow_flag & 7}")
        
        p += 1


def save_bitmap(bmp_name: str, buf: bytes, bw: int, bh: int):
    """Save bitmap as BMP file."""
    bpp = 8
    dsize = bw * bh
    psize = (1 << bpp) * 4
    fsize = 14 + 40 + psize + ((bw + 3) & ~3) * bh
    
    # BMP file header
    bm_header = struct.pack('<HI HH I',
                            0x4D42,  # bfType
                            fsize,   # bfSize
                            0, 0,    # bfReserved1, bfReserved2
                            14 + 40 + psize)  # bfOffBits
    
    # BMP info header
    bm_info = struct.pack('<I ii HH I I ii II',
                         40,      # biSize
                         bw,      # biWidth
                         bh,      # biHeight
                         1,       # biPlanes
                         bpp,     # biBitCount
                         0,       # biCompression (BI_RGB)
                         dsize,   # biSizeImage
                         0, 0,    # biXPelsPerMeter, biYPelsPerMeter
                         psize // 4, 0)  # biClrUsed, biClrImportant
    
    # Palette (grayscale for 4-bit values expanded to 8-bit)
    palbuf = bytearray(psize)
    for i in range(16):
        val = i * 17  # 0-15 -> 0-255
        palbuf[i * 4:i * 4 + 3] = bytes([val, val, val])
    
    with open(bmp_name, 'wb') as fp:
        fp.write(bm_header)
        fp.write(bm_info)
        fp.write(palbuf)
        
        # Write bitmap data (bottom-up)
        row_size = (bw + 3) & ~3
        for y in range(bh - 1, -1, -1):
            row = bytearray(row_size)
            start = y * bw
            row[:bw] = buf[start:start + bw]
            fp.write(row)
    
    print(f"Save BMP : {bmp_name}")


def render_glyph(glyph: PGFGlyph, buf: bytearray, ox: int, oy: int, pitch: int):
    """Render glyph onto buffer."""
    if not glyph.bmp:
        return
    
    ox += glyph.left
    oy -= glyph.top
    
    for v in range(glyph.height):
        dst_y = oy + v
        if 0 <= dst_y < len(buf) // pitch:
            for h in range(glyph.width):
                dst_x = ox + h
                if 0 <= dst_x < pitch:
                    dst_idx = dst_y * pitch + dst_x
                    src_idx = v * glyph.width + h
                    if dst_idx < len(buf) and src_idx < len(glyph.bmp):
                        buf[dst_idx] = glyph.bmp[src_idx]


def print_bitmap(pgft: PGFFont, basename: str):
    """Print all glyphs as bitmap pages."""
    # Extract base name
    p = basename.rfind('.')
    if p >= 0:
        basename = basename[:p]
    p = max(basename.rfind('/'), basename.rfind('\\'))
    if p >= 0:
        basename = basename[p + 1:]
    
    # Create output directory
    dirname = f"{basename}_bmp"
    os.makedirs(dirname, exist_ok=True)
    
    if not pgft.header:
        return
    
    xstep = pgft.header.max_glyph_w + 1
    ystep = pgft.header.max_glyph_h + 2
    
    gw = xstep * 17
    gh = ystep * 17
    gsize = gw * gh
    
    gbuf = bytearray(gsize)
    
    for page in range(256):
        cy = ystep
        empty_page = True
        gbuf[:] = b'\x00' * gsize
        
        for v in range(16):
            cx = 0
            for h in range(16):
                ucs = page * 256 + v * 16 + h
                glyph = pgft.get_glyph(ucs)
                if glyph is None:
                    cx += xstep
                    continue
                
                empty_page = False
                bx = (xstep - glyph.width) // 2
                render_glyph(glyph, gbuf, cx + bx, cy, gw)
                cx += xstep
            cy += ystep
        
        if empty_page:
            continue
        
        pagename = f"{dirname}/{basename}_{page:02x}.bmp"
        save_bitmap(pagename, bytes(gbuf), gw, gh)


def main():
    """Main entry point for dump_pgf."""
    import argparse
    
    parser = argparse.ArgumentParser(description='PGF font info dumper V1.0')
    parser.add_argument('font', help='PGF font file')
    parser.add_argument('-H', '--header', action='store_true', help='dump font header')
    parser.add_argument('-m', '--metrics', action='store_true', help='dump metrics table')
    parser.add_argument('-c', '--charmap', action='store_true', help='dump chars map')
    parser.add_argument('-i', '--charinfo', action='store_true', help='dump chars info')
    parser.add_argument('-s', '--shadow', action='store_true', help='dump shadow map')
    parser.add_argument('-p', '--charptr', action='store_true', help='dump chars pointer')
    parser.add_argument('-b', '--bitmap', action='store_true', help='dump chars bitmap')
    
    args = parser.parse_args()
    
    if not any([args.header, args.metrics, args.charmap, args.charinfo, 
                args.shadow, args.charptr, args.bitmap]):
        parser.print_help()
        return 0
    
    pgft = load_pgf_font(args.font)
    if pgft is None:
        return -1
    
    if args.header:
        print_header(pgft)
    
    if args.metrics:
        print_dim_table(pgft)
        print_bearingX_table(pgft)
        print_bearingY_table(pgft)
        print_adv_table(pgft)
    
    if args.charmap:
        print_charmap(pgft)
    
    if args.charptr:
        print_charptr(pgft)
    
    if args.shadow:
        print_shadowmap(pgft)
    
    if args.charinfo:
        print_charinfo(pgft)
    
    if args.bitmap:
        print_bitmap(pgft, args.font)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
