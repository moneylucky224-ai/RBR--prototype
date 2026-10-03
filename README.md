# RBR - Rent Borrow Reuse (campus prototype)
Run in the VS Code terminal (Python 3.9+):
1. python -m venv venv
2. venv\Scripts\activate         (Windows)  |  source venv/bin/activate  (Mac/Linux)
3. pip install flask
4. python app.py
5. Open http://127.0.0.1:5000

Demo login (sample users): demo1@rbr.in / demo123   (or register a new account)
Sample data (35 items, 5 per category) is created automatically on first run. Delete rbr.db to reset.

Files: app.py (server) | templates_data.py (pages, logo, styling) | static/rbr_logo.svg | static/uploads (photos/videos)
Optional ID auto-detect: pip install pytesseract pillow + install Tesseract OCR (otherwise ID shows "Pending").
