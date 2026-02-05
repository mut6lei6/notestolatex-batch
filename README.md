# NotesToLaTeX Batch

Batch upload images and PDFs to [notestolatex.com](https://notestolatex.com) using browser automation (Playwright).

## Features

- Process multiple images in one run
- PDF support (auto-splits into pages)
- Extracts only the content between `\begin{document}` and `\end{document}`
- Saves each result to a separate `.txt` file

## Installation

```bash
pip install playwright
playwright install chromium

# Optional: for PDF support
pip install pdf2image
```

For PDF support on Windows, also install [Poppler](https://github.com/oschwartz10612/poppler-windows/releases) and add the `bin` folder to your PATH.

## Usage

```bash
# Single image
python notestolatex_batch.py photo.png

# Multiple images
python notestolatex_batch.py img1.png img2.jpg img3.png

# All PNGs in a folder
python notestolatex_batch.py images/*.png

# A PDF (auto-splits into pages)
python notestolatex_batch.py document.pdf

# Mix of images and PDFs
python notestolatex_batch.py *.png notes.pdf
```

## Output

Results are saved to the `latex_output/` folder:

```
latex_output/
├── img1.txt
├── img2.txt
└── document_page1.txt
```

Each `.txt` file contains only the document content (without the LaTeX preamble).

## Configuration

Edit the `SELECTORS` dict at the top of the script if the website changes:

```python
SELECTORS = {
    "file_input": 'input[type="file"]',
    "submit_button": 'button:has-text("Transform")',
    "result_text": 'pre, code, .latex-output, textarea',
}
```

## License

MIT
