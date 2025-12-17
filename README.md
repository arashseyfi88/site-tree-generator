# site-tree-generator

## Install
```bash
pip install git+https://github.com/arashsayfi/site-tree-generator.git

site-tree --input breadcrumbs.xlsx --output site_tree.pdf


Commit.

---

## مرحله 4) حالا نوبت چسبوندن کد اصلی داخل core.py
تو همینجا من باید کد نهایی تولید PDF رو داخل `generate_pdf` بذارم.

برای اینکه دقیق و بدون باگ بچسبونم، یک چیز لازم دارم:
- **همون کد نهایی‌ای که الان توی Colab جواب داده و PDF درست می‌سازه** رو همینجا برام Paste کن (یا فایل نوت‌بوک رو بفرست).

بعدش من:
- `files.upload()` و `files.download()` رو حذف می‌کنم (چون روی سیستم کاربره)
- ورودی رو از `excel_path` می‌گیرم
- خروجی رو با `plt.savefig(output_pdf)` ذخیره می‌کنم
- و همه چیز آماده می‌شه.

---

## مرحله 5) تست سریع (وقتی core.py کامل شد)
کاربر اینو می‌زنه:

```bash
pip install git+https://github.com/arashsayfi/site-tree-generator.git
site-tree -i breadcrumbs.xlsx -o out.pdf
