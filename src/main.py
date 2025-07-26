import os
import json
import time
import datetime
from sklearn.metrics.pairwise import cosine_similarity

# Import our custom functions
from utils import load_model, extract_sections

def analyze_documents(doc_paths, persona, job_to_be_done, model):
    """
    Analyzes a collection of documents against a persona and a job,
    then ranks the sections by relevance.
    """
    print("Starting document analysis...")
    start_time = time.time()

    # A hyper-focused query for the final polish
    query = f"As a {persona}, my primary objective is to {job_to_be_done}. I am looking for the most relevant sections, Short explanations, and step-by-step instructions related to this task. Please identify the key concepts, short methodologies, and data points that will help me achieve this goal.More focus on main Keyword like Create Make Help Do this and instructions should be related to that only. No random or off topic things,and lastly Be very Precise and Accurate"
    query_embedding = model.encode([query])

    all_sections = []
    for doc_path in doc_paths:
        if not os.path.exists(doc_path):
            print(f"Warning: Document not found at {doc_path}")
            continue
        print(f"Processing {doc_path}...")
        _, sections = extract_sections(doc_path)
        all_sections.extend(sections)

    if not all_sections:
        return []

    print(f"Extracted {len(all_sections)} sections. Creating embeddings...")
    section_texts_for_embedding = [f"{s['text']}: {s['content'][:750]}" for s in all_sections]
    section_embeddings = model.encode(section_texts_for_embedding, show_progress_bar=True)

    relevance_scores = cosine_similarity(query_embedding, section_embeddings)[0]

    for i, section in enumerate(all_sections):
        section['relevance_score'] = relevance_scores[i]

    ranked_sections = sorted(all_sections, key=lambda x: x['relevance_score'], reverse=True)

    end_time = time.time()
    print(f"Analysis complete in {end_time - start_time:.2f} seconds.")
    
    return ranked_sections

def format_submission_json(ranked_sections, doc_paths, persona, job_to_be_done, top_n=5):
    """
    Formats the analysis results into the final required JSON structure.
    """
    # The correct output shows the top 5 sections
    top_sections = ranked_sections[:top_n]

    output = {
        "metadata": {
            "input_documents": [os.path.basename(p) for p in doc_paths],
            "persona": persona,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.datetime.now().isoformat()
        },
        "extracted_sections": [],
        # CORRECTED: Key name is 'subsection_analysis' (no underscore)
        "subsection_analysis": []
    }

    for i, section in enumerate(top_sections):
        output["extracted_sections"].append({
            "document": section['doc_name'],
            "section_title": section['text'],
            "importance_rank": i + 1,
            "page_number": section['page']
        })

        # The correct output only includes subsection analysis for sections that have content.
        section_content = section.get('content', '').strip()
        if section_content:
            output["subsection_analysis"].append({
                "document": section['doc_name'],
                # CORRECTED: 'refined_text' should be the full content
                "refined_text": section_content,
                "page_number": section['page']
            })
            
    return output

def save_output(data, output_path):
    """Saves the final data to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Main Execution Block ---
# --- Main Execution Block ---
# --- Main Execution Block ---
if __name__ == '__main__':
    # Define standard input and output paths
    INPUT_DIR = "input/"
    OUTPUT_DIR = "output/"
    INPUT_JSON_PATH = os.path.join(INPUT_DIR, "input.json")
    OUTPUT_JSON_PATH = os.path.join(OUTPUT_DIR, "output.json") # Generic output name

    # 1. Load all instructions from the single input.json file
    try:
        with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"The required '{INPUT_JSON_PATH}' was not found. "
            "Please create it for local testing."
        )

    # 2. Extract information from the loaded JSON
    # Note: we get the strings from within the 'persona' and 'job_to_be_done' objects
    PERSONA = input_data.get('persona', {}).get('role', '')
    JOB_TO_BE_DONE = input_data.get('job_to_be_done', {}).get('task', '')
    
    # Get the list of PDF filenames
    documents = input_data.get('documents', [])
    if not documents:
        raise ValueError("No documents listed in input.json")

    # Construct the full paths to the PDF files
    document_paths = [os.path.join(INPUT_DIR, doc['filename']) for doc in documents]
    
    print(f"Persona: {PERSONA}")
    print(f"Job: {JOB_TO_BE_DONE}")
    
    # 3. Run the analysis (the rest of the flow is the same)
    # Load the model
    model = load_model()
    
    # Run the core analysis
    ranked_sections = analyze_documents(document_paths, PERSONA, JOB_TO_BE_DONE, model)
    
    # Format the results into the final JSON structure
    final_output = format_submission_json(ranked_sections, document_paths, PERSONA, JOB_TO_BE_DONE)

    # Save the final output JSON
    save_output(final_output, OUTPUT_JSON_PATH)
    
    print(f"\nSuccessfully generated submission file at: {OUTPUT_JSON_PATH}")