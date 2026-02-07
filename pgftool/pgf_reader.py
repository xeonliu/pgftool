"""PGF file reading utilities."""

import struct
from typing import List, Optional
from .pgf_font import PGFFont, PGFGlyph, PGFHeader, F26Pairs


def get_value(bpe: int, buf: bytes, pos: int) -> tuple:
    """
    Extract a value of bpe bits from buffer starting at bit position pos.
    Returns (value, new_pos).
    """
    v = 0
    for i in range(bpe):
        byte_idx = pos // 8
        bit_idx = pos % 8
        if byte_idx < len(buf):
            bit = (buf[byte_idx] >> bit_idx) & 1
            v += bit << i
        pos += 1
    return v, pos


def read_table(fp, num: int, bpe: int) -> List[int]:
    """Read a bit-packed table from file."""
    length = ((num * bpe + 31) // 32) * 4
    raw = fp.read(length)
    
    table = []
    pos = 0
    for _ in range(num):
        value, pos = get_value(bpe, raw, pos)
        table.append(value)
    
    return table


def get_bitmap(glyph: PGFGlyph) -> bytes:
    """Decode RLE-compressed glyph bitmap."""
    if not glyph.data:
        return b''
    
    length = glyph.width * glyph.height
    if (glyph.flag & 3) == 2:
        bmp = bytearray(length)
    else:
        bmp = bytearray(length) if glyph.bmp is None else bytearray(glyph.bmp)
    
    i = 0
    p = 0
    
    while i < length:
        nb, p = get_value(4, glyph.data, p)
        
        if nb < 8:
            # RLE: repeat next value nb+1 times
            data, p = get_value(4, glyph.data, p)
            for _ in range(nb + 1):
                if i < length:
                    bmp[i] = data
                    i += 1
        else:
            # Literal: read 16-nb values
            for _ in range(16 - nb):
                if i < length:
                    data, p = get_value(4, glyph.data, p)
                    bmp[i] = data
                    i += 1
    
    # Handle transposed bitmap
    if (glyph.flag & 3) == 2:
        final_bmp = bytearray(length)
        idx = 0
        for h in range(glyph.width):
            for v in range(glyph.height):
                final_bmp[v * glyph.width + h] = bmp[idx]
                idx += 1
        return bytes(final_bmp)
    
    return bytes(bmp)


def load_shadow_glyph(ptr: bytes) -> PGFGlyph:
    """Load a shadow glyph from data pointer."""
    glyph = PGFGlyph()
    pos = 0
    
    glyph.size, pos = get_value(14, ptr, pos)
    glyph.width, pos = get_value(7, ptr, pos)
    glyph.height, pos = get_value(7, ptr, pos)
    glyph.left, pos = get_value(7, ptr, pos)
    glyph.top, pos = get_value(7, ptr, pos)
    glyph.flag, pos = get_value(6, ptr, pos)
    
    # Sign extend 7-bit values
    if glyph.left > 63:
        glyph.left |= -128  # Sign extend from 7 bits
    if glyph.top > 63:
        glyph.top |= -128
    
    glyph.data = ptr[pos // 8:]
    glyph.bmp = get_bitmap(glyph)
    
    return glyph


def load_char_glyph(pgft: PGFFont, index: int, glyph: PGFGlyph):
    """Load a character glyph from font data."""
    if not pgft.glyphdata or not pgft.charptr:
        return
    
    ptr = pgft.glyphdata[pgft.charptr[index]:]
    pos = 0
    
    glyph.index = index
    glyph.have_shadow = pgft.have_shadow(glyph.ucs)
    
    glyph.size, pos = get_value(14, ptr, pos)
    glyph.width, pos = get_value(7, ptr, pos)
    glyph.height, pos = get_value(7, ptr, pos)
    glyph.left, pos = get_value(7, ptr, pos)
    glyph.top, pos = get_value(7, ptr, pos)
    glyph.flag, pos = get_value(6, ptr, pos)
    
    # Sign extend 7-bit values
    if glyph.left > 63:
        glyph.left |= -128
    if glyph.top > 63:
        glyph.top |= -128
    
    # Read extension info
    glyph.shadow_flag, pos = get_value(7, ptr, pos)
    glyph.shadow_id, pos = get_value(9, ptr, pos)
    
    if glyph.flag & 0x04:
        id_val, pos = get_value(8, ptr, pos)
        glyph.dimension = F26Pairs(
            pgft.dimension[id_val].h,
            pgft.dimension[id_val].v
        )
    else:
        h, pos = get_value(32, ptr, pos)
        v, pos = get_value(32, ptr, pos)
        glyph.dimension = F26Pairs(h, v)
    
    if glyph.flag & 0x08:
        id_val, pos = get_value(8, ptr, pos)
        glyph.bearingX = F26Pairs(
            pgft.bearingX[id_val].h,
            pgft.bearingX[id_val].v
        )
    else:
        h, pos = get_value(32, ptr, pos)
        v, pos = get_value(32, ptr, pos)
        glyph.bearingX = F26Pairs(h, v)
    
    if glyph.flag & 0x10:
        id_val, pos = get_value(8, ptr, pos)
        glyph.bearingY = F26Pairs(
            pgft.bearingY[id_val].h,
            pgft.bearingY[id_val].v
        )
    else:
        h, pos = get_value(32, ptr, pos)
        v, pos = get_value(32, ptr, pos)
        glyph.bearingY = F26Pairs(h, v)
    
    if glyph.flag & 0x20:
        id_val, pos = get_value(8, ptr, pos)
        glyph.advance = F26Pairs(
            pgft.advance[id_val].h,
            pgft.advance[id_val].v
        )
    else:
        h, pos = get_value(32, ptr, pos)
        v, pos = get_value(32, ptr, pos)
        glyph.advance = F26Pairs(h, v)
    
    glyph.data = ptr[pos // 8:]
    glyph.bmp = get_bitmap(glyph)
    
    # Load shadow glyph if present
    if glyph.have_shadow:
        shadow_id = glyph.shadow_id
        shadow_glyph = load_shadow_glyph(ptr[glyph.size:])
        pgft.shadow_glyph[shadow_id] = shadow_glyph


def load_ucs_list(list_name: str) -> List[int]:
    """Load UCS code list from file."""
    ucs_list = [0] * 65536
    
    try:
        with open(list_name, 'r') as f:
            count = 0
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                try:
                    ucs = int(line, 16)
                    if 0 <= ucs < 65536:
                        ucs_list[ucs] = ucs
                        count += 1
                except ValueError:
                    continue
            print(f"Load list from {list_name}: {count}")
    except FileNotFoundError:
        # If no list file, load all glyphs
        for i in range(65536):
            ucs_list[i] = i
    
    return ucs_list


def load_pgf_font(font_name: str) -> Optional[PGFFont]:
    """Load a PGF font from file."""
    pgft = PGFFont()
    
    try:
        with open(font_name, 'rb') as fp:
            # Read PGF header
            header_data = fp.read(392)
            pgft.header = PGFHeader.from_bytes(header_data)
            
            # Seek to end of header
            fp.seek(pgft.header.header_len)
            
            # Read dimension table
            length = pgft.header.dimension_len
            for _ in range(length):
                h, v = struct.unpack('<ii', fp.read(8))
                pgft.dimension.append(F26Pairs(h, v))
            
            # Read left bearing table
            length = pgft.header.bearingX_len
            for _ in range(length):
                h, v = struct.unpack('<ii', fp.read(8))
                pgft.bearingX.append(F26Pairs(h, v))
            
            # Read top bearing table
            length = pgft.header.bearingY_len
            for _ in range(length):
                h, v = struct.unpack('<ii', fp.read(8))
                pgft.bearingY.append(F26Pairs(h, v))
            
            # Read advance table
            length = pgft.header.advance_len
            for _ in range(length):
                h, v = struct.unpack('<ii', fp.read(8))
                pgft.advance.append(F26Pairs(h, v))
            
            # Read shadowmap table
            if pgft.header.shadowmap_len:
                pgft.shadowmap = read_table(fp, pgft.header.shadowmap_len, 
                                           pgft.header.shadowmap_bpe)
            
            # Read charmap table
            pgft.charmap = read_table(fp, pgft.header.charmap_len,
                                     pgft.header.charmap_bpe)
            
            # Read charptr table
            pgft.charptr = read_table(fp, pgft.header.charptr_len,
                                     pgft.header.charptr_bpe)
            for i in range(len(pgft.charptr)):
                pgft.charptr[i] *= pgft.header.charptr_scale
            
            # Read font glyph data
            pgft.glyphdata = fp.read()
        
        # Load UCS list
        ucs_list = load_ucs_list(f"{font_name}.txt")
        
        # Load all glyphs
        n_chars = pgft.header.charptr_len
        for i in range(n_chars):
            ucs = pgft.ptr2ucs(i)
            if ucs_list[ucs] == 0:
                continue
            
            glyph = PGFGlyph()
            glyph.ucs = ucs
            pgft.char_glyph[ucs] = glyph
            load_char_glyph(pgft, i, glyph)
        
        # Free glyph data as it's no longer needed
        pgft.glyphdata = None
        
        return pgft
    
    except Exception as e:
        print(f"Error loading font {font_name}: {e}")
        return None
