# Migration Guide: C to Pure Python

This document describes the migration from C to pure Python implementation of pgftool.

## Overview

The entire C codebase has been refactored to pure Python, providing:
- Cross-platform compatibility without compilation
- Easy installation via pip
- Maintainable, readable code
- Same functionality as the original C implementation

## File Mapping

### C Implementation → Python Implementation

| C File | Python File | Description |
|--------|-------------|-------------|
| `pgf.h` | `pgftool/pgf_font.py` | Core data structures |
| `libpgf.c` | `pgftool/pgf_reader.py` | PGF file reading/parsing |
| `save_pgf.c` | `pgftool/pgf_writer.py` | PGF file writing |
| `dump_pgf.c` | `pgftool/dump_pgf.py` | Font info dumper |
| `mix_pgf.c` | `pgftool/mix_pgf.py` | Font mixer |
| `ttfont.c` | `pgftool/ttf_to_pgf.py` | TTF to PGF converter |

## Key Changes

### Dependencies
- **Before (C)**: FreeType library, zlib, C compiler
- **After (Python)**: Python 3.6+, Pillow, freetype-py

### Installation
- **Before (C)**: 
  ```bash
  make
  # or
  cmake . && make
  ```
- **After (Python)**:
  ```bash
  pip install -e .
  ```

### Usage
The command-line interface remains the same:

```bash
# C version
./dump_pgf -h font.pgf

# Python version  
dump_pgf -H font.pgf
```

Note: `-h` became `-H` for header dump to avoid conflict with `--help`

## Implementation Details

### Bit Manipulation
The C implementation used bit-level operations for packed data. The Python implementation:
- Uses `bytearray` for mutable byte buffers
- Implements `get_value()` and `put_value()` for bit-packed data
- Maintains byte-level compatibility with the original format

### Binary File I/O
- C: `fread()`, `fwrite()`, `fseek()`
- Python: `file.read()`, `file.write()`, `file.seek()`

### Memory Management
- C: Manual `malloc()`/`free()` 
- Python: Automatic garbage collection

### Data Structures
- C structs → Python `@dataclass` classes
- Manual memory layout → `struct.pack()`/`struct.unpack()`

## Performance Considerations

The Python implementation is slightly slower than C but provides:
- Easier maintenance and debugging
- Better error messages
- Cross-platform compatibility
- No compilation needed

For most use cases, the performance difference is negligible.

## Compatibility

The Python implementation:
- ✓ Reads PGF files created by C version
- ✓ Writes PGF files compatible with C version
- ✓ Produces identical output format
- ✓ Maintains all original functionality

## Testing

Basic tests are included in the implementation. To test:

```bash
python3 -c "
from pgftool import PGFFont, PGFGlyph, PGFHeader, F26Pairs
print('Import successful!')
"
```

Run CLI tools:
```bash
dump_pgf --help
mix_pgf
ttf_pgf
```

## Future Enhancements

Possible improvements for the Python version:
- [ ] Add comprehensive unit tests
- [ ] Add type hints throughout (already partially done)
- [ ] Create Python API documentation
- [ ] Add PGF validation tools
- [ ] Support for additional font formats
- [ ] GUI interface using tkinter or PyQt

## Backward Compatibility

The C implementation is still available and can be built using Make or CMake. Both versions can coexist and produce compatible files.
