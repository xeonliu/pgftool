cmake_minimum_required(VERSION 3.10)
project(pgftool C)

# Set C standard
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Find FreeType package
find_package(Freetype)

# Include directories
include_directories(${CMAKE_SOURCE_DIR})
include_directories(${CMAKE_SOURCE_DIR}/freetype2)
if(FREETYPE_FOUND)
    include_directories(${FREETYPE_INCLUDE_DIRS})
endif()

# Common source files
set(COMMON_SOURCES
    libpgf.c
)

# dump_pgf executable
add_executable(dump_pgf
    dump_pgf.c
    ${COMMON_SOURCES}
)

# mix_pgf executable
add_executable(mix_pgf
    save_pgf.c
    mix_pgf.c
    ${COMMON_SOURCES}
)

# ttf_pgf executable
add_executable(ttf_pgf
    save_pgf.c
    ttfont.c
    ${COMMON_SOURCES}
)

# Link ttf_pgf with FreeType and zlib
if(FREETYPE_FOUND)
    target_link_libraries(ttf_pgf ${FREETYPE_LIBRARIES} z)
else()
    # Fall back to using the prebuilt library if system FreeType is not available
    # Note: This library appears to be built for macOS and may not work on Linux
    target_link_libraries(ttf_pgf ${CMAKE_SOURCE_DIR}/libfreetype.a z)
    message(WARNING "System FreeType not found, using prebuilt library which may not work on all platforms")
endif()

# Compiler flags
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(dump_pgf PRIVATE -Wall -O2)
    target_compile_options(mix_pgf PRIVATE -Wall -O2)
    target_compile_options(ttf_pgf PRIVATE -Wall -O2)
endif()
