import argparse
from .core import generate_pdf

def main():
    p = argparse.ArgumentParser(prog="site-tree")
    p.add_argument("-i", "--input", help="Path to Excel file (.xlsx)")
    p.add_argument("-o", "--output", default="site_tree.pdf", help="Output PDF filename")
    p.add_argument("--show", action="store_true", help="Show plot window (mostly for local use)")
    args = p.parse_args()

    # If input not provided, try Colab upload
    if not args.input:
        try:
            from google.colab import files  # type: ignore
            print("📤 Please upload your Excel file (.xlsx)...")
            uploaded = files.upload()
            if not uploaded:
                raise SystemExit("No file uploaded.")
            args.input = list(uploaded.keys())[0]
            print(f"✅ Uploaded: {args.input}")
        except Exception:
            raise SystemExit(
                "No --input provided and Colab upload is not available. "
                "Please run: site-tree --input yourfile.xlsx"
            )

    generate_pdf(args.input, args.output, show=args.show)

    # If in Colab, auto-download
    try:
        from google.colab import files  # type: ignore
        files.download(args.output)
    except Exception:
        pass

    print(f"✅ Done: {args.output}")
