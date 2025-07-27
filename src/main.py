import os
import json
import time
import datetime
from sklearn.metrics.pairwise import cosine_similarity
from utils import load_model, extract_sections, load_outline_if_available


def analyze_documents(doc_paths, persona, job_to_be_done, model, outline_data):
    print("\n🔍 Starting document analysis...")
    start_time = time.time()

    # Step 1: Embed persona and job separately with weights
    persona_query = f"You are a {persona}. Focus on areas relevant to their expertise."
    job_query = f"The user needs to: {job_to_be_done}"
    persona_embedding = model.encode([persona_query])[0]
    job_embedding = model.encode([job_query])[0]
    query_embedding = 0.4 * persona_embedding + 0.6 * job_embedding
    query_embedding = [query_embedding]  # reshape for cosine similarity

    # Step 2: Extract and encode sections
    all_sections = []
    for doc_path in doc_paths:
        if not os.path.exists(doc_path):
            print(f"⚠️ Warning: Document not found at {doc_path}")
            continue
        print(f"📄 Processing: {doc_path}")
        _, sections = extract_sections(doc_path)
        all_sections.extend(sections)

    if not all_sections:
        return []

    print(f"\n🧠 Extracted {len(all_sections)} sections. Creating embeddings...")
    section_texts = [f"{s['text']}: {s['content'][:750]}" for s in all_sections]
    section_embeddings = model.encode(section_texts, show_progress_bar=True)

    relevance_scores = cosine_similarity(query_embedding, section_embeddings)[0]

    for i, section in enumerate(all_sections):
        base_score = relevance_scores[i]
        outline_boost = 0.0

        doc_outline = outline_data.get(section['doc_name'].lower())
        if doc_outline:
            outline_titles = [entry['title'].strip().lower() for entry in doc_outline]
            for title in outline_titles:
                if title in section['text'].lower():
                    outline_boost = 0.1
                    break

        section['relevance_score'] = base_score + outline_boost

        print(f"\n📌 [{section['doc_name']}] '{section['text']}' → Score: {section['relevance_score']:.3f} (base: {base_score:.3f}, boost: {outline_boost:.2f})")

    ranked_sections = sorted(all_sections, key=lambda x: x['relevance_score'], reverse=True)

    end_time = time.time()
    print(f"\n✅ Analysis complete in {end_time - start_time:.2f} seconds.")
    return ranked_sections


def format_submission_json(ranked_sections, doc_paths, persona, job_to_be_done, top_n=5, relevance_threshold=0.4):
    top_sections = [s for s in ranked_sections if s['relevance_score'] > relevance_threshold][:top_n]

    output = {
        "metadata": {
            "input_documents": [os.path.basename(p) for p in doc_paths],
            "persona": persona,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.datetime.now().isoformat()
        },
        "extracted_sections": [],
        "subsection_analysis": []
    }

    for i, section in enumerate(top_sections):
        output["extracted_sections"].append({
            "document": section['doc_name'],
            "section_title": section['text'],
            "importance_rank": i + 1,
            "page_number": section['page']
        })

        if section.get('content'):
            output["subsection_analysis"].append({
                "document": section['doc_name'],
                "refined_text": section['content'],
                "page_number": section['page']
            })

    return output


def save_output(data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_combined_outline(path="output/combined_outlines.json"):
    if not os.path.exists(path):
        print("⚠️ Warning: No combined_outlines.json found.")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load outline: {e}")
        return {}


if __name__ == '__main__':
    INPUT_DIR = "input/"
    OUTPUT_DIR = "output/"
    INPUT_JSON_PATH = os.path.join(INPUT_DIR, "input.json")
    OUTPUT_JSON_PATH = os.path.join(OUTPUT_DIR, "output.json")

    try:
        with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"The required '{INPUT_JSON_PATH}' was not found. Please create it for local testing."
        )

    PERSONA = input_data.get('persona', {}).get('role', '')
    JOB_TO_BE_DONE = input_data.get('job_to_be_done', {}).get('task', '')

    documents = input_data.get('documents', [])
    if not documents:
        raise ValueError("No documents listed in input.json")

    document_paths = [os.path.join(INPUT_DIR, doc['filename']) for doc in documents]

    print(f"\n🧑‍💼 Persona: {PERSONA}")
    print(f"🎯 Job to be done: {JOB_TO_BE_DONE}")

    model = load_model()
    outline_data = load_combined_outline()
    ranked_sections = analyze_documents(document_paths, PERSONA, JOB_TO_BE_DONE, model, outline_data)
    final_output = format_submission_json(ranked_sections, document_paths, PERSONA, JOB_TO_BE_DONE)
    save_output(final_output, OUTPUT_JSON_PATH)

    print(f"\n✅ Output saved to: {OUTPUT_JSON_PATH}")
