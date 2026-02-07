"""PGF file writing utilities."""

import struct
from typing import List, Tuple
from .pgf_font import PGFFont, PGFGlyph, F26Pairs


def put_value(nbit: int, buf: bytearray, data: int, ptr: int) -> int:
    """
    Write nbit bits of data to buf at bit position ptr.
    Returns new bit position.
    """
    for i in range(nbit):
        mask = 1 << (ptr % 8)
        bit = ((data >> i) << (ptr % 8)) & mask
        byte_idx = ptr // 8
        if byte_idx < len(buf):
            buf[byte_idx] &= ~mask
            buf[byte_idx] |= bit
        ptr += 1
    return ptr


def rle_data(out: bytearray, bmp: bytes, bmp_len: int) -> int:
    """
    RLE encode bitmap data.
    Returns size in bits.
    """
    size = 0
    i = 0
    
    while i < bmp_len:
        k = i
        rcnt = 0
        scnt = 0
        
        while k < bmp_len:
            rlen = 0
            slen = 0
            
            # Count different values
            j = k + 1
            while j < min(k + 9, bmp_len):
                if bmp[j - 1] == bmp[j]:
                    j -= 1
                    break
                j += 1
            rlen = j - k
            
            # Count same values
            j = k + 1
            while j < min(k + 8, bmp_len):
                if bmp[j - 1] != bmp[j]:
                    break
                j += 1
            slen = j - k
            
            if slen > 2:
                scnt = slen
                break
            elif slen == 2:
                scnt += 2
                k += slen
                if scnt > 6 or rcnt == 0:
                    break
            else:
                rcnt += rlen + scnt
                k += rlen
                scnt = 0
                if rcnt > 7:
                    break
        
        if rcnt > 8:
            rcnt = 8
        if scnt > 8:
            scnt = 8
        
        if rcnt:
            size = put_value(4, out, 16 - rcnt, size)
            for j in range(rcnt):
                size = put_value(4, out, bmp[i + j], size)
            i += rcnt
        elif scnt:
            size = put_value(4, out, scnt - 1, size)
            size = put_value(4, out, bmp[i], size)
            i += scnt
    
    return size


def find_in_table(table: List[F26Pairs], total: int, fp: F26Pairs) -> int:
    """Find F26Pairs in table, return index or -1."""
    for i in range(total):
        if table[i].h == fp.h and table[i].v == fp.v:
            return i
    return -1


class MetricsTable:
    """Helper for building optimized metrics tables."""
    
    def __init__(self):
        self.table: List[F26Pairs] = []
        self.freq: List[int] = []
        self.total = 0
    
    def add(self, fp: F26Pairs):
        """Add metrics to table with frequency tracking."""
        # Find existing entry
        for i in range(self.total):
            if self.table[i].h == fp.h and self.table[i].v == fp.v:
                self.freq[i] += 1
                # Re-sort by frequency
                p = i
                for j in range(p):
                    if self.freq[j] < self.freq[p]:
                        # Swap
                        self.table[j], self.table[p] = self.table[p], self.table[j]
                        self.freq[j], self.freq[p] = self.freq[p], self.freq[j]
                        break
                return
        
        # Add new entry
        self.table.append(F26Pairs(fp.h, fp.v))
        self.freq.append(1)
        self.total += 1


def build_metrics_table(pgft: PGFFont):
    """Build optimized metrics tables."""
    dim = MetricsTable()
    bx = MetricsTable()
    by = MetricsTable()
    adv = MetricsTable()
    
    for glyph in pgft.char_glyph.values():
        dim.add(glyph.dimension)
        bx.add(glyph.bearingX)
        by.add(glyph.bearingY)
        adv.add(glyph.advance)
    
    # Limit to 255 entries max
    pgft.header.dimension_len = min(dim.total, 255)
    pgft.dimension = dim.table[:pgft.header.dimension_len]
    
    pgft.header.bearingX_len = min(bx.total, 255)
    pgft.bearingX = bx.table[:pgft.header.bearingX_len]
    
    pgft.header.bearingY_len = min(by.total, 255)
    pgft.bearingY = by.table[:pgft.header.bearingY_len]
    
    pgft.header.advance_len = min(adv.total, 255)
    pgft.advance = adv.table[:pgft.header.advance_len]


def build_glyph_data(pgft: PGFFont):
    """Build encoded glyph data for all glyphs."""
    bmp_buf = bytearray(64 * 64)
    
    for glyph in pgft.char_glyph.values():
        glyph.flag = 0
        gsize = 40  # Base size in bytes
        
        # Check if metrics can use table references
        glyph.dim_id = find_in_table(pgft.dimension, pgft.header.dimension_len, glyph.dimension)
        if glyph.dim_id >= 0:
            glyph.flag |= 0x04
            gsize -= 7
        
        glyph.bx_id = find_in_table(pgft.bearingX, pgft.header.bearingX_len, glyph.bearingX)
        if glyph.bx_id >= 0:
            glyph.flag |= 0x08
            gsize -= 7
        
        glyph.by_id = find_in_table(pgft.bearingY, pgft.header.bearingY_len, glyph.bearingY)
        if glyph.by_id >= 0:
            glyph.flag |= 0x10
            gsize -= 7
        
        glyph.adv_id = find_in_table(pgft.advance, pgft.header.advance_len, glyph.advance)
        if glyph.adv_id >= 0:
            glyph.flag |= 0x20
            gsize -= 7
        
        glyph.size = gsize
        
        # Encode bitmap with RLE
        bmp_len = glyph.width * glyph.height
        hbuf = bytearray(bmp_len + 40)
        vbuf = bytearray(bmp_len + 40)
        
        # Horizontal RLE
        hsize = rle_data(hbuf[gsize:], glyph.bmp, bmp_len)
        
        # Vertical RLE (transpose bitmap first)
        p = 0
        for h in range(glyph.width):
            for v in range(glyph.height):
                bmp_buf[p] = glyph.bmp[v * glyph.width + h]
                p += 1
        vsize = rle_data(vbuf[gsize:], bytes(bmp_buf[:bmp_len]), bmp_len)
        
        # Choose smaller encoding
        if hsize <= vsize:
            glyph.flag |= 0x01
            glyph.size += (hsize + 7) // 8
            glyph.data = hbuf[:glyph.size]
        else:
            glyph.flag |= 0x02
            glyph.size += (vsize + 7) // 8
            glyph.data = vbuf[:glyph.size]
        
        # Build glyph header
        p = 0
        p = put_value(14, glyph.data, glyph.size, p)
        p = put_value(7, glyph.data, glyph.width, p)
        p = put_value(7, glyph.data, glyph.height, p)
        p = put_value(7, glyph.data, glyph.left & 0x7f, p)
        p = put_value(7, glyph.data, glyph.top & 0x7f, p)
        p = put_value(6, glyph.data, glyph.flag, p)
        p = put_value(7, glyph.data, glyph.shadow_flag, p)
        p = put_value(9, glyph.data, glyph.shadow_id, p)
        
        # Build metrics data
        p = 8
        if glyph.flag & 0x04:
            glyph.data[p] = glyph.dim_id
            p += 1
        else:
            struct.pack_into('<ii', glyph.data, p, glyph.dimension.h, glyph.dimension.v)
            p += 8
        
        if glyph.flag & 0x08:
            glyph.data[p] = glyph.bx_id
            p += 1
        else:
            struct.pack_into('<ii', glyph.data, p, glyph.bearingX.h, glyph.bearingX.v)
            p += 8
        
        if glyph.flag & 0x10:
            glyph.data[p] = glyph.by_id
            p += 1
        else:
            struct.pack_into('<ii', glyph.data, p, glyph.bearingY.h, glyph.bearingY.v)
            p += 8
        
        if glyph.flag & 0x20:
            glyph.data[p] = glyph.adv_id
            p += 1
        else:
            struct.pack_into('<ii', glyph.data, p, glyph.advance.h, glyph.advance.v)
            p += 8


def find_max_min(pgft: PGFFont):
    """Find maximum and minimum values for font header."""
    max_h_bearingX = 0
    max_h_bearingY = 0
    min_v_bearingX = 1000000
    max_v_bearingY = 0
    max_h_advance = 0
    max_v_advance = 0
    max_h_dimension = 0
    max_v_dimension = 0
    max_glyph_w = 0
    max_glyph_h = 0
    
    ucsmin = -1
    ucsmax = -1
    n_chars = 0
    
    for ucs in sorted(pgft.char_glyph.keys()):
        glyph = pgft.char_glyph[ucs]
        
        if ucsmin == -1:
            ucsmin = ucs
        ucsmax = ucs
        n_chars += 1
        
        # Mask to align values
        glyph.bearingX.h &= 0xfffffff0
        if glyph.bearingX.h > max_h_bearingX:
            max_h_bearingX = glyph.bearingX.h
        glyph.bearingX.v &= 0xfffffff0
        if glyph.bearingX.v < min_v_bearingX:
            min_v_bearingX = glyph.bearingX.v
        
        glyph.bearingY.h &= 0xfffffff0
        if glyph.bearingY.h > max_h_bearingY:
            max_h_bearingY = glyph.bearingY.h
        glyph.bearingY.v &= 0xfffffff0
        if glyph.bearingY.v > max_v_bearingY:
            max_v_bearingY = glyph.bearingY.v
        
        glyph.advance.h &= 0xfffffff0
        if glyph.advance.h > max_h_advance:
            max_h_advance = glyph.advance.h
        glyph.advance.v &= 0xfffffff0
        if glyph.advance.v > max_v_advance:
            max_v_advance = glyph.advance.v
        
        glyph.dimension.h &= 0xfffffff0
        if glyph.dimension.h > max_h_dimension:
            max_h_dimension = glyph.dimension.h
        glyph.dimension.v &= 0xfffffff0
        if glyph.dimension.v > max_v_dimension:
            max_v_dimension = glyph.dimension.v
        
        if glyph.width > max_glyph_w:
            max_glyph_w = glyph.width
        if glyph.height > max_glyph_h:
            max_glyph_h = glyph.height
    
    pgft.header.max_h_bearingX = max_h_bearingX
    pgft.header.max_h_bearingY = max_h_bearingY
    pgft.header.min_v_bearingX = min_v_bearingX
    pgft.header.max_v_bearingY = max_v_bearingY
    pgft.header.max_h_advance = max_h_advance
    pgft.header.max_v_advance = max_v_advance
    pgft.header.max_h_dimension = max_h_dimension
    pgft.header.max_v_dimension = max_v_dimension
    pgft.header.max_glyph_w = max_glyph_w
    pgft.header.max_glyph_h = max_glyph_h
    
    pgft.header.charmap_min = ucsmin if ucsmin != -1 else 0
    pgft.header.charmap_max = ucsmax if ucsmax != -1 else 0
    pgft.header.charmap_len = ucsmax - ucsmin + 1 if ucsmin != -1 else 0
    pgft.header.charptr_len = n_chars


def write_table(fp, table: List[int], bpe: int):
    """Write bit-packed table to file."""
    if not table:
        return
    
    num = len(table)
    length = ((num * bpe + 31) // 32) * 4
    raw = bytearray(length)
    
    pos = 0
    for value in table:
        pos = put_value(bpe, raw, value, pos)
    
    fp.write(raw)


def calc_bpe(max_value: int) -> int:
    """Calculate bits per element needed."""
    if max_value == 0:
        return 1
    
    bpe = 0
    while (1 << bpe) <= max_value:
        bpe += 1
    return bpe


def save_pgf(pgft: PGFFont, font_name: str) -> int:
    """Save PGF font to file."""
    # Build metrics tables
    build_metrics_table(pgft)
    
    # Find max/min values
    find_max_min(pgft)
    
    # Build charmap and charptr
    charmap = []
    charptr = []
    ptr = 0
    
    for ucs in range(pgft.header.charmap_min, pgft.header.charmap_max + 1):
        if ucs in pgft.char_glyph:
            charmap.append(len(charptr))
            charptr.append(ptr // pgft.header.charptr_scale)
            ptr += pgft.char_glyph[ucs].size
        else:
            charmap.append(0xffff)
    
    pgft.charmap = charmap
    pgft.charptr = charptr
    
    # Calculate BPE values
    pgft.header.charmap_bpe = calc_bpe(max(charmap) if charmap else 0)
    pgft.header.charptr_bpe = calc_bpe(max(charptr) if charptr else 0)
    
    # Build glyph data
    build_glyph_data(pgft)
    
    # Write file
    try:
        with open(font_name, 'wb') as fp:
            # Write header
            fp.write(pgft.header.to_bytes())
            
            # Pad to header_len
            padding = pgft.header.header_len - fp.tell()
            if padding > 0:
                fp.write(b'\x00' * padding)
            
            # Write dimension table
            for dim in pgft.dimension:
                fp.write(struct.pack('<ii', dim.h, dim.v))
            
            # Write bearingX table
            for bx in pgft.bearingX:
                fp.write(struct.pack('<ii', bx.h, bx.v))
            
            # Write bearingY table
            for by in pgft.bearingY:
                fp.write(struct.pack('<ii', by.h, by.v))
            
            # Write advance table
            for adv in pgft.advance:
                fp.write(struct.pack('<ii', adv.h, adv.v))
            
            # Write shadowmap table
            if pgft.shadowmap:
                write_table(fp, pgft.shadowmap, pgft.header.shadowmap_bpe)
            
            # Write charmap table
            write_table(fp, pgft.charmap, pgft.header.charmap_bpe)
            
            # Write charptr table
            write_table(fp, pgft.charptr, pgft.header.charptr_bpe)
            
            # Write glyph data
            for ucs in range(pgft.header.charmap_min, pgft.header.charmap_max + 1):
                if ucs in pgft.char_glyph:
                    glyph = pgft.char_glyph[ucs]
                    fp.write(glyph.data)
        
        print(f"Saved PGF font: {font_name}")
        return 0
    
    except Exception as e:
        print(f"Error saving font {font_name}: {e}")
        return -1
