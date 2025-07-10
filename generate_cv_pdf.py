import argparse
from bs4 import BeautifulSoup
from weasyprint import HTML
from pathlib import Path


def main(html_path, output_pdf):
    base_dir = Path(html_path).parent.resolve()
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    for btn in soup.select(".download-btn" ):
        btn.decompose()
    html_str = str(soup)
    HTML(string=html_str, base_url=base_dir).write_pdf(output_pdf)
    print(f"PDF saved to {output_pdf}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate PDF CV from HTML")
    parser.add_argument("html", nargs="?", default="index.html", help="Path to input HTML file")
    parser.add_argument("output", nargs="?", default="curriculum/ACacioppo_CV.pdf", help="Output PDF path")
    args = parser.parse_args()
    main(args.html, args.output)
