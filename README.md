pgftool
=======

My PGF font tools - Pure Python implementation

## Installation

### From source
```bash
pip install -e .
```

### Dependencies
```bash
pip install Pillow freetype-py
```

## Usage

### Dump PGF font information
```bash
dump_pgf -H font.pgf         # Display header
dump_pgf -m font.pgf         # Display metrics tables
dump_pgf -c font.pgf         # Display character map
dump_pgf -b font.pgf         # Export bitmaps
```

### Mix two PGF fonts
```bash
mix_pgf target.pgf source.pgf
```

### Convert TrueType to PGF
```bash
ttf_pgf font.ttf output.pgf [unicode_list.txt]
```

## Legacy C Implementation

The original C implementation can still be built using Make or CMake:

### Using Make
```bash
make
```

### Using CMake
```bash
mkdir build
cd build
cmake ..
make
```

Note: The CMake build will use the system FreeType library if available.
If not found, it will fall back to the bundled library.
To install system FreeType on Ubuntu/Debian: `sudo apt-get install libfreetype6-dev`