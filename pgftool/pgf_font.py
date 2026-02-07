"""Core PGF font data structures."""

import struct
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class F26Pairs:
    """26.6 fixed-point pairs for horizontal and vertical values."""
    h: int = 0
    v: int = 0
    
    def to_float(self) -> tuple:
        """Convert to floating point representation."""
        return (self.h / 64.0, self.v / 64.0)


@dataclass
class PGFHeader:
    """PGF font file header."""
    # 0x0000
    header_start: int = 0
    header_len: int = 0x0188
    pgf_id: bytes = b'PGF0'
    revision: int = 0x00000002
    version: int = 0x00000006
    
    # 0x0010
    charmap_len: int = 0
    charptr_len: int = 0
    charmap_bpe: int = 0
    charptr_bpe: int = 0
    
    # 0x0020
    unk_20: bytes = b'\x04\x04'
    bpp: int = 0x04
    unk_23: int = 0x00
    
    h_size: int = 0
    v_size: int = 0
    h_res: int = 0
    v_res: int = 0
    
    unk_34: int = 0x00
    font_name: str = ""
    font_type: str = ""
    unk_B5: int = 0x00
    
    charmap_min: int = 0
    charmap_max: int = 0
    
    # 0x00BA
    unk_BA: int = 0x0000
    unk_BC: int = 0x00010000
    unk_C0: int = 0x00000000
    unk_C4: int = 0x00000000
    unk_C8: int = 0x00010000
    unk_CC: int = 0x00000000
    unk_D0: int = 0x00000000
    
    ascender: int = 0
    descender: int = 0
    max_h_bearingX: int = 0
    max_h_bearingY: int = 0
    min_v_bearingX: int = 0
    max_v_bearingY: int = 0
    max_h_advance: int = 0
    max_v_advance: int = 0
    max_h_dimension: int = 0
    max_v_dimension: int = 0
    max_glyph_w: int = 0
    max_glyph_h: int = 0
    
    # 0x0100
    charptr_scale: int = 0x0004
    dimension_len: int = 0
    bearingX_len: int = 0
    bearingY_len: int = 0
    advance_len: int = 0
    unk_106: bytes = b'\x00' * 102
    
    shadowmap_len: int = 0
    shadowmap_bpe: int = 0x00000010
    unk_174: int = 0x00000604
    shadowscale_x: int = 0x00000020
    shadowscale_y: int = 0x00000020
    unk_180: int = 0
    unk_184: int = 0
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'PGFHeader':
        """Parse PGF header from bytes."""
        header = cls()
        
        # Parse header (0x0000)
        (header.header_start, header.header_len) = struct.unpack('<HH', data[0:4])
        header.pgf_id = data[4:8]
        (header.revision, header.version) = struct.unpack('<II', data[8:16])
        
        # Parse 0x0010
        (header.charmap_len, header.charptr_len, 
         header.charmap_bpe, header.charptr_bpe) = struct.unpack('<IIII', data[16:32])
        
        # Parse 0x0020
        header.unk_20 = data[32:34]
        header.bpp = data[34]
        header.unk_23 = data[35]
        (header.h_size, header.v_size, 
         header.h_res, header.v_res) = struct.unpack('<IIII', data[36:52])
        
        header.unk_34 = data[52]
        header.font_name = data[53:117].decode('utf-8', errors='ignore').rstrip('\x00')
        header.font_type = data[117:181].decode('utf-8', errors='ignore').rstrip('\x00')
        header.unk_B5 = data[181]
        
        (header.charmap_min, header.charmap_max) = struct.unpack('<HH', data[182:186])
        
        # Parse 0x00BA
        (header.unk_BA, header.unk_BC, header.unk_C0, header.unk_C4,
         header.unk_C8, header.unk_CC, header.unk_D0) = struct.unpack('<HIIIIII', data[186:214])
        
        (header.ascender, header.descender,
         header.max_h_bearingX, header.max_h_bearingY,
         header.min_v_bearingX, header.max_v_bearingY,
         header.max_h_advance, header.max_v_advance,
         header.max_h_dimension, header.max_v_dimension,
         header.max_glyph_w, header.max_glyph_h) = struct.unpack('<iiiiiiiiiiHH', data[214:256])
        
        # Parse 0x0100
        (header.charptr_scale,) = struct.unpack('<H', data[256:258])
        header.dimension_len = data[258]
        header.bearingX_len = data[259]
        header.bearingY_len = data[260]
        header.advance_len = data[261]
        header.unk_106 = data[262:364]
        
        (header.shadowmap_len, header.shadowmap_bpe,
         header.unk_174, header.shadowscale_x, header.shadowscale_y,
         header.unk_180, header.unk_184) = struct.unpack('<IIIIIII', data[364:392])
        
        return header
    
    def to_bytes(self) -> bytes:
        """Convert header to bytes."""
        data = bytearray(392)
        
        struct.pack_into('<HH', data, 0, self.header_start, self.header_len)
        data[4:8] = self.pgf_id
        struct.pack_into('<II', data, 8, self.revision, self.version)
        
        struct.pack_into('<IIII', data, 16, self.charmap_len, self.charptr_len,
                        self.charmap_bpe, self.charptr_bpe)
        
        data[32:34] = self.unk_20
        data[34] = self.bpp
        data[35] = self.unk_23
        struct.pack_into('<IIII', data, 36, self.h_size, self.v_size, 
                        self.h_res, self.v_res)
        
        data[52] = self.unk_34
        font_name_bytes = self.font_name.encode('utf-8')[:64]
        data[53:53+len(font_name_bytes)] = font_name_bytes
        font_type_bytes = self.font_type.encode('utf-8')[:64]
        data[117:117+len(font_type_bytes)] = font_type_bytes
        data[181] = self.unk_B5
        
        struct.pack_into('<HH', data, 182, self.charmap_min, self.charmap_max)
        
        struct.pack_into('<HIIIIII', data, 186, self.unk_BA, self.unk_BC,
                        self.unk_C0, self.unk_C4, self.unk_C8, self.unk_CC, self.unk_D0)
        
        struct.pack_into('<iiiiiiiiiiHH', data, 214,
                        self.ascender, self.descender,
                        self.max_h_bearingX, self.max_h_bearingY,
                        self.min_v_bearingX, self.max_v_bearingY,
                        self.max_h_advance, self.max_v_advance,
                        self.max_h_dimension, self.max_v_dimension,
                        self.max_glyph_w, self.max_glyph_h)
        
        struct.pack_into('<H', data, 256, self.charptr_scale)
        data[258] = self.dimension_len
        data[259] = self.bearingX_len
        data[260] = self.bearingY_len
        data[261] = self.advance_len
        data[262:364] = self.unk_106
        
        struct.pack_into('<IIIIIII', data, 364, self.shadowmap_len, self.shadowmap_bpe,
                        self.unk_174, self.shadowscale_x, self.shadowscale_y,
                        self.unk_180, self.unk_184)
        
        return bytes(data)


@dataclass
class PGFGlyph:
    """PGF glyph data."""
    index: int = 0
    ucs: int = 0
    have_shadow: bool = False
    
    size: int = 0        # 14 bits
    width: int = 0       # 7 bits
    height: int = 0      # 7 bits
    left: int = 0        # 7 bits signed
    top: int = 0         # 7 bits signed
    flag: int = 0        # 6 bits
    
    shadow_flag: int = 0 # 7 bits
    shadow_id: int = 0   # 9 bits
    
    dim_id: int = 0
    bx_id: int = 0
    by_id: int = 0
    adv_id: int = 0
    
    dimension: F26Pairs = field(default_factory=F26Pairs)
    bearingX: F26Pairs = field(default_factory=F26Pairs)
    bearingY: F26Pairs = field(default_factory=F26Pairs)
    advance: F26Pairs = field(default_factory=F26Pairs)
    
    data: Optional[bytes] = None
    bmp: Optional[bytes] = None


class PGFFont:
    """PGF font representation."""
    
    def __init__(self):
        self.header: Optional[PGFHeader] = None
        
        self.dimension: List[F26Pairs] = []
        self.bearingX: List[F26Pairs] = []
        self.bearingY: List[F26Pairs] = []
        self.advance: List[F26Pairs] = []
        
        self.charmap: List[int] = []
        self.charptr: List[int] = []
        self.shadowmap: List[int] = []
        
        self.glyphdata: Optional[bytes] = None
        self.char_glyph: Dict[int, PGFGlyph] = {}
        self.shadow_glyph: Dict[int, PGFGlyph] = {}
    
    def get_glyph(self, ucs: int) -> Optional[PGFGlyph]:
        """Get glyph by UCS code."""
        return self.char_glyph.get(ucs)
    
    def ptr2ucs(self, ptr: int) -> int:
        """Convert char pointer to UCS code."""
        if not self.header:
            return 0xffff
            
        for i, charmap_ptr in enumerate(self.charmap):
            if charmap_ptr == ptr:
                return i + self.header.charmap_min
        return 0xffff
    
    def have_shadow(self, ucs: int) -> bool:
        """Check if glyph has shadow."""
        return ucs in self.shadowmap
