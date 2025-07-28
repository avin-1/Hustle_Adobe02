import fitz  # PyMuPDF
import json
import os
import re
from collections import defaultdict
from statistics import median, mode, StatisticsError
from sentence_transformers import SentenceTransformer

# --- Configuration (from 1A) ---
CONFIG = {
    "header_threshold": 0.15,
    "footer_threshold": 0.85,
    "min_heading_score": 1.5,
    "font_size_ratio": 1.0,
    "min_body_text_words": 6,
    "title_page_limit": 2,
}

# --- Model Loading (from Step 2) ---
MODEL_PATH = 'model/all-mpnet-base-v2'

def load_model():
    """
    Loads the SentenceTransformer model from the local directory.
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Please run the download_model.py script first.")
    
    print("Loading model from local path...")
    model = SentenceTransformer(MODEL_PATH)
    print("Model loaded successfully.")
    return model

# --- PDF Parsing Helpers (from your 1A code) ---
# These are your functions, slightly adapted to work within this file.

def get_document_structure(pdf_path):
    doc = fitz.open(pdf_path)
    doc_structure = []
    for page_num, page in enumerate(doc):
        page_data = {
            "page_num": page_num + 1,
            "page_width": page.rect.width,
            "page_height": page.rect.height,
            "blocks": []
        }
        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_LIGATURES).get("blocks", [])
        for b in blocks:
            if b.get("type") == 0:
                block_data = {"bbox": b['bbox'], "lines": []}
                for line in b.get("lines", []):
                    spans = line.get("spans")
                    if spans:
                        line_text = " ".join(s.get("text", "") for s in spans).strip()
                        if line_text:
                            clean_line = {
                                "text": line_text,
                                "bbox": line.get("bbox", []),
                                "spans": spans,
                            }
                            block_data["lines"].append(clean_line)
                if block_data["lines"]:
                    page_data["blocks"].append(block_data)
        doc_structure.append(page_data)
    doc.close()
    return doc_structure

def identify_and_filter_content(doc_structure, config):
    ignored_line_ids = set()
    potential_hf_lines = defaultdict(list)
    
    for page in doc_structure[1:]:
        for block in page['blocks']:
            is_header = block['bbox'][3] < page['page_height'] * config['header_threshold']
            is_footer = block['bbox'][1] > page['page_height'] * config['footer_threshold']
            if is_header or is_footer:
                for line in block['lines']:
                    normalized_text = re.sub(r'\d+', '#', line['text'])
                    if len(normalized_text.split()) < 8:
                        potential_hf_lines[normalized_text].append(page['page_num'])

    num_pages = len(doc_structure)
    for text, pages in potential_hf_lines.items():
        if len(set(pages)) > 2 or (num_pages > 5 and len(set(pages)) > num_pages * 0.5):
            for page in doc_structure:
                if page['page_num'] in pages:
                    for block in page['blocks']:
                        for line in block['lines']:
                            if re.sub(r'\d+', '#', line['text']) == text:
                                ignored_line_ids.add((page['page_num'], tuple(map(round, line['bbox']))))
    return ignored_line_ids

def find_title_by_layout(doc_structure, ignored_line_ids, config):
    candidates = []
    for page in doc_structure[:config['title_page_limit']]:
        for block in page['blocks']:
            if any((page['page_num'], tuple(map(round, line['bbox']))) in ignored_line_ids for line in block['lines']):
                continue
            if not (1 <= len(block['lines']) <= 4) or block['bbox'][1] > page['page_height'] * 0.4:
                continue

            block_text = " ".join(line['text'] for line in block['lines'])
            if not block_text: continue
            
            avg_size = median([s['size'] for line in block['lines'] for s in line['spans']]) if any(line['spans'] for line in block['lines']) else 0
            block_center_x = (block['bbox'][0] + block['bbox'][2]) / 2
            page_center_x = page['page_width'] / 2
            centering_score = (1 - abs(block_center_x - page_center_x) / page_center_x) * 15 if page_center_x > 0 else 0
            position_score = (1 - block['bbox'][1] / (page['page_height'] * 0.4)) * 5
            score = avg_size + centering_score + position_score
            candidates.append({"text": block_text, "score": score, "page_num": page['page_num'], "lines": block['lines']})

    if not candidates: return "Untitled Document", set()

    best_candidate = max(candidates, key=lambda x: x["score"])
    title_line_ids = {(best_candidate['page_num'], tuple(map(round, line['bbox']))) for line in best_candidate['lines']}
    return best_candidate['text'], title_line_ids

def get_heading_score(line, block, body_text_size, config):
    text = line['text']
    spans = line['spans']
    if not spans: return -10

    # --- MORE AGGRESSIVE FILTERING ---
    # 1. Reject if it's too long, ends with punctuation, or looks like a URL.
    if len(text.split()) > 15 or text.endswith(('.', ',', ':', '?', ';')) or re.search(r'https?://\S+|www\.\S+', text):
        return -10

    # 2. Reject if it starts with a list marker or other non-heading characters.
    if re.match(r'^\s*•|^\s*[-–—]|`|^\d+\.$', text.strip()):
        return -10

    # 3. Reject if it's not capitalized like a title (a strong heuristic).
    words = text.split()
    if len(words) > 3: # Avoid penalizing short, all-caps headings
        # Count words starting with an uppercase letter
        capitalized_words = sum(1 for word in words if word[0].isupper())
        # If less than half the words are capitalized, it's likely a sentence.
        if (capitalized_words / len(words)) < 0.5:
            return -10
    # --- END OF FILTERING ---

    font_sizes = {round(s['size']) for s in spans}
    if len(font_sizes) > 1: return -10

    score = 0.0
    line_size = font_sizes.pop()
    # A more reliable way to check for bold text
    is_bold = any('bold' in s['font'].lower() for s in spans)

    # --- ADJUSTED SCORING ---
    # Must be larger than body text
    if line_size > body_text_size:
        score += (line_size - body_text_size) * 2.5
    else:
        return -10 # Penalize heavily if smaller than or same size as body text

    if is_bold:
        score += 2.0

    # A very strong indicator of a heading is that it's the only line in its block
    if len(block['lines']) == 1:
        score += 3.5

    if text.isupper() and len(words) < 5: # All caps is good for short headings
        score += 1.5
    elif text.istitle(): # Title case is also a good sign
        score += 1.5

    if len(text.split()) < 10:
        score += 1.0

    # Penalize if the line looks more like a page number or a list item
    if sum(c.isdigit() for c in text) > len(text) / 2:
        score -= 5.0

    return score

# --- New Main Function for 1B ---

def extract_sections(pdf_path):
    """
    Processes a PDF to extract its title and structured sections (heading + content).
    """
    doc_structure = get_document_structure(pdf_path)
    if not any(page['blocks'] for page in doc_structure):
        return "No Text Found", []

    # --- Step 1: Identify Title and Headers/Footers ---
    ignored_line_ids = identify_and_filter_content(doc_structure, CONFIG)
    title_text, title_line_ids = find_title_by_layout(doc_structure, ignored_line_ids, CONFIG)
    ignored_line_ids.update(title_line_ids)

    font_sizes = [
        round(s['size']) for page in doc_structure for b in page['blocks']
        for line in b['lines'] for s in line['spans']
        if len(line['text'].split()) > CONFIG['min_body_text_words']
    ]
    body_text_size = median(font_sizes) if font_sizes else 10

    # --- Step 2: Find all heading candidates and their styles ---
    heading_candidates = []
    for page in doc_structure:
        for block in page['blocks']:
            for line in block['lines']:
                if (page['page_num'], tuple(map(round, line['bbox']))) in ignored_line_ids:
                    continue
                score = get_heading_score(line, block, body_text_size, CONFIG)
                if score > CONFIG['min_heading_score']:
                    try:
                        style_key = (mode([round(s['size']) for s in line['spans']]), any(s['flags'] & 2 for s in line['spans']))
                        heading_info = {
                            "text": line["text"],
                            "page": page["page_num"],
                            "bbox": line["bbox"],
                            "style_key": style_key
                        }
                        heading_candidates.append(heading_info)
                    except StatisticsError:
                        continue
    
    # --- Step 3: Rank styles and assign H-levels (your 1A logic) ---
    style_properties = defaultdict(list)
    for h in heading_candidates:
        style_properties[h['style_key']].append(h['bbox'][0])

    ranked_styles = sorted(
        [{"size": style[0], "bold": style[1], "x0": median(x0s), "style_key": style} for style, x0s in style_properties.items()],
        key=lambda x: (-x["size"], x["x0"])
    )
    style_to_level = {style["style_key"]: f"H{min(i + 1, 3)}" for i, style in enumerate(ranked_styles[:3])}

    # --- Step 4: Create a final map of headings with assigned levels ---
    final_headings = {}
    for h in heading_candidates:
        level = style_to_level.get(h['style_key'])
        if level:
            # Use a unique identifier for each heading
            heading_id = (h['page'], tuple(map(round, h['bbox'])))
            final_headings[heading_id] = {
                "text": h["text"],
                "page": h["page"],
                "level": level,
            }

    # --- Step 5: Aggregate content between headings ---
    sections = []
    current_section_content = []
    current_section_info = None

    for page in doc_structure:
        for block in page['blocks']:
            for line in block['lines']:
                line_id = (page['page_num'], tuple(map(round, line['bbox'])))
                
                if line_id in ignored_line_ids and line_id not in final_headings:
                    continue
                
                if line_id in final_headings:
                    # If we find a new heading, save the previous section first
                    if current_section_info:
                        sections.append({
                            **current_section_info,
                            "content": " ".join(current_section_content).strip()
                        })
                    
                    # Start a new section
                    current_section_info = {
                        "doc_name": os.path.basename(pdf_path),
                        **final_headings[line_id]
                    }
                    current_section_content = []
                elif current_section_info:
                    # If we are inside a section, accumulate its content
                    current_section_content.append(line['text'])

    # Append the very last section after the loop
    if current_section_info:
        sections.append({
            **current_section_info,
            "content": " ".join(current_section_content).strip()
        })

    return title_text, sections


from sklearn.feature_extraction.text import TfidfVectorizer
