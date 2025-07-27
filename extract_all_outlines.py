import os
import json
import fitz  # PyMuPDF
from pathlib import Path

# Path to input and output folders
INPUT_JSON = "input/input.json"
INPUT_DIR = "input/"
OUTPUT_DIR = "output/"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_outline(pdf_path):
    """
    Extracts the outline (table of contents) from a PDF using PyMuPDF.
    Returns a list of entries with title, level, and page number.
    """
    doc = fitz.open(pdf_path)
    outline = doc.get_toc()
    
    results = []
    for item in outline:
        level, title, page_num = item
        results.append({
            "level": level,
            "title": title,
            "page_number": page_num
        })
    
    return results

def main():
    # Load input.json
    try:
        with open(INPUT_JSON, "r", encoding="utf-8") as f:
            input_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: {INPUT_JSON} not found.")
        return

    documents = input_data.get("documents", [])
    if not documents:
        print("⚠️ No documents listed in input.json")
        return

    for doc in documents:
        filename = doc.get("filename")
        if not filename:
            continue
        
        pdf_path = os.path.join(INPUT_DIR, filename)
        output_filename = Path(filename).stem.replace(" ", "_").lower() + "_outline.json"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        print(f"📄 Extracting outline from: {pdf_path}")
        if not os.path.exists(pdf_path):
            print(f"❌ Skipped: File not found.")
            continue
        
        outline_data = extract_outline(pdf_path)
        print(f"📚 Found {len(outline_data)} entries.")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(outline_data, f, indent=4, ensure_ascii=False)

        print(f"✅ Outline saved to: {output_path}\n")

if __name__ == "__main__":
    main()
