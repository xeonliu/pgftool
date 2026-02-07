"""Mix two PGF fonts together."""

import sys
from .pgf_reader import load_pgf_font
from .pgf_writer import save_pgf


def mix_pgf(dpgf, spgf):
    """Mix source PGF into destination PGF."""
    for ucs, glyph in spgf.char_glyph.items():
        dpgf.char_glyph[ucs] = glyph


def main():
    """Main entry point for mix_pgf."""
    if len(sys.argv) < 3:
        print("mix_pgf <target pgf> <source pgf>")
        return -1
    
    dpgf = load_pgf_font(sys.argv[1])
    if dpgf is None:
        return -1
    
    spgf = load_pgf_font(sys.argv[2])
    if spgf is None:
        return -1
    
    mix_pgf(dpgf, spgf)
    
    save_pgf(dpgf, sys.argv[1])
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
