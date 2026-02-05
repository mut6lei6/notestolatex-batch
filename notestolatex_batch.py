#!/usr/bin/env python3
"""
Batch upload images/PDFs to notestolatex.com using Playwright.
Usage: python notestolatex_batch.py file1.png file2.jpg document.pdf
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from pathlib import Path
import tempfile
import time
import sys
import re

# Optional: PDF support (install with: pip install pdf2image)
try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# =============================================================================
# CONFIGURATION - Update these selectors after inspecting the website
# =============================================================================
SELECTORS = {
    "file_input": 'input[type="file"]',       # File upload input
    "submit_button": 'button:has-text("Transform")',  # Convert/submit button
    "result_text": 'pre, code, .latex-output, textarea',  # Where LaTeX result appears
}

SETTINGS = {
    "headless": False,          # False = watch the browser
    "delay_between": 3,         # Seconds between uploads
    "result_timeout": 120000,   # Max ms to wait for conversion (2 min)
}
# =============================================================================


def extract_document_content(latex: str) -> str:
    """
    Extract content between \\begin{document} and \\end{document}.
    Returns the content only, or the full text if markers not found.
    """
    pattern = r'\\begin\{document\}(.*?)\\end\{document\}'
    match = re.search(pattern, latex, re.DOTALL)
    if match:
        return match.group(1).strip()
    return latex.strip()


def pdf_to_images(pdf_path: Path) -> list[Path]:
    """Convert a PDF to temporary PNG files, one per page."""
    if not PDF_SUPPORT:
        print("Error: pdf2image not installed. Run: pip install pdf2image")
        sys.exit(1)

    images = convert_from_path(str(pdf_path))
    paths = []
    for i, img in enumerate(images):
        tmp_path = Path(tempfile.mktemp(suffix=f"_page{i+1}.png"))
        img.save(tmp_path, "PNG")
        paths.append(tmp_path)
        print(f"  Extracted page {i+1} → {tmp_path.name}")
    return paths


def expand_inputs(filepaths: list[str]) -> list[tuple[Path, str]]:
    """
    Expand input files. PDFs become multiple images.
    Returns list of (image_path, label) tuples.
    """
    result = []
    for fp in filepaths:
        path = Path(fp)
        if not path.exists():
            print(f"Warning: {fp} not found, skipping")
            continue

        if path.suffix.lower() == ".pdf":
            print(f"Converting PDF: {path.name}")
            for i, img_path in enumerate(pdf_to_images(path)):
                result.append((img_path, f"{path.stem}_page{i+1}"))
        else:
            result.append((path, path.stem))

    return result


def process_images(images: list[tuple[Path, str]], output_dir: Path):
    """Open browser and process each image through notestolatex.com."""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=SETTINGS["headless"])
        context = browser.new_context()
        page = context.new_page()

        for i, (image_path, label) in enumerate(images):
            print(f"\n[{i+1}/{len(images)}] Processing: {label}")

            try:
                # Navigate to the site
                page.goto("https://notestolatex.com", wait_until="networkidle")

                # Upload the file
                file_input = page.locator(SELECTORS["file_input"])
                file_input.set_input_files(str(image_path))
                print("  ✓ File uploaded")

                # Click submit
                page.click(SELECTORS["submit_button"])
                print("  ⏳ Waiting for conversion...")

                # Wait for result to appear
                result_el = page.wait_for_selector(
                    SELECTORS["result_text"],
                    timeout=SETTINGS["result_timeout"],
                    state="visible"
                )

                # Extract the LaTeX text
                full_latex = result_el.inner_text()
                content = extract_document_content(full_latex)
                print(f"  ✓ Got {len(content)} characters")

                # Save to individual txt file
                output_file = output_dir / f"{label}.txt"
                output_file.write_text(content)
                print(f"  ✓ Saved to {output_file}")

            except PlaywrightTimeout:
                print(f"  ✗ Timeout waiting for result")
            except Exception as e:
                print(f"  ✗ Error: {e}")

            # Polite delay between requests
            if i < len(images) - 1:
                time.sleep(SETTINGS["delay_between"])

        browser.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python notestolatex_batch.py <file1> [file2] [file3.pdf] ...")
        print("Supports: .png, .jpg, .jpeg, .pdf")
        sys.exit(1)

    # Create output directory
    output_dir = Path("latex_output")
    output_dir.mkdir(exist_ok=True)

    # Expand PDFs to images
    images = expand_inputs(sys.argv[1:])
    if not images:
        print("No valid files to process")
        sys.exit(1)

    print(f"\nWill process {len(images)} image(s)")
    print(f"Output directory: {output_dir.absolute()}")

    # Process through the website
    process_images(images, output_dir)

    print(f"\n{'='*50}")
    print(f"Done! Check the '{output_dir}' folder for results.")


if __name__ == "__main__":
    main()
