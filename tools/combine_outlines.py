import os
import json

INPUT_FOLDER = "output"
OUTPUT_FILE = "output/combined_outlines.json"

combined_outlines = {}

for file_name in os.listdir(INPUT_FOLDER):
    if file_name.endswith("_outline.json"):
        base_doc_name = file_name.replace("_outline.json", "").replace("_", " ").title()
        with open(os.path.join(INPUT_FOLDER, file_name), "r", encoding="utf-8") as f:
            outline_data = json.load(f)
        combined_outlines[base_doc_name] = outline_data

# Save combined output
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(combined_outlines, f, indent=4, ensure_ascii=False)

print(f"✅ Combined outlines saved to: {OUTPUT_FILE}")
