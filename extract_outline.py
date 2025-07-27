import sys
import json
import fitz  # PyMuPDF
import os

def extract_outline_from_pdf(pdf_path):
    """
    Extracts the outline (table of contents) from a given PDF file.
    """
    doc = fitz.open(pdf_path)
    outline = doc.get_toc(simple=True)

    extracted = []
    for item in outline:
        level, title, page = item
        extracted.append({
            "level": level,
            "title": title.strip(),
            "page_number": page + 1  # Convert to 1-based index
        })

    doc.close()
    return extracted

def save_outline_to_json(outline, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(outline, f, indent=4, ensure_ascii=False)
    print(f"✅ Output written to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_outline.py <input.pdf> <output.json>")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_json = sys.argv[2]

    if not os.path.exists(input_pdf):
        print(f"❌ Error: File not found - {input_pdf}")
        sys.exit(1)

    print(f"📄 Extracting outline from: {input_pdf}")
    outline = extract_outline_from_pdf(input_pdf)

    if not outline:
        print("⚠️ No outline/table of contents found in this PDF.")
    else:
        print(f"📚 Found {len(outline)} entries in the outline.")

    save_outline_to_json(outline, output_json)
