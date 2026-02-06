pgftool
=======

My PGF font tools

## Building

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