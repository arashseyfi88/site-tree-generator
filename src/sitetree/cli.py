import argparse
from .core import generate_pdf

def main():
    p = argparse.ArgumentParser(prog="site-tree")
    p.add_argument("-i", "--input", required=True, help="Path to Excel file (.xlsx)")
    p.add_argument("-o", "--output", default="site_tree.pdf", help="Output PDF filename")
    args = p.parse_args()

    generate_pdf(args.input, args.output)
    print(f"✅ Done: {args.output}")
