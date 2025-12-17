```md
# site-tree-generator

Generate a visual site tree (PDF) from an Excel breadcrumb file.

## Recommended usage (Google Colab)

Paste and run this single cell in a Google Colab notebook:

```python
!pip install -q git+https://github.com/arashsayfi/site-tree-generator.git

from google.colab import files
from sitetree.core import generate_pdf

print("📤 Upload your Excel (.xlsx)")
uploaded = files.upload()
excel_path = list(uploaded.keys())[0]

output = "site_tree.pdf"
generate_pdf(excel_path, output)

files.download(output)
print("✅ Done")
```

## Local / CLI usage

```bash
pip install git+https://github.com/arashsayfi/site-tree-generator.git
site-tree --input breadcrumbs.xlsx --output site_tree.pdf
```

## Input format

Excel file with columns such as:

LVL 0 | LVL 1 | LVL 2 | LVL 3 | LVL 4

Each row represents one path in the site tree.
```
