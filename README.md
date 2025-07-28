# Adobe Hackathon - Round 1B Submission

## My Approach

Our solution tackles the "Persona-Driven Document Intelligence" challenge by implementing a semantic analysis pipeline. The core of our approach is based on the following steps:

1.  **Structured Content Extraction**: We first parse each PDF using our robust engine from Round 1A. This engine identifies not only headings (H1, H2, H3) but also intelligently associates all the text content that belongs to each heading, forming structured "sections."
2.  **Semantic Representation**: We use a pre-trained `all-mpnet-base-v2` sentence-transformer model to convert the user's query (a combination of their persona and job-to-be-done) and each document section into high-dimensional vectors (embeddings). This model was chosen for its excellent balance of performance and size (**under 500MB**), making it ideal for the offline, CPU-only environment and compliant with the <1GB constraint.
3.  **Relevance Ranking**: The relevance of each section is calculated by computing the cosine similarity between the query embedding and the section's embedding. This gives us a precise score indicating how well a section answers the user's need. Sections are then ranked globally across all documents.
4.  **Granular Sub-section Analysis**: For the top-ranked sections, we perform a sub-section analysis using a TF-IDF vectorizer to extract the most significant keywords. This provides a "refined text" summary, giving the user a quick glance at the core topics of the most relevant content.

## Key Achievements & Features

* **High-Precision Semantic Ranking:** Goes beyond simple keyword matching to understand the contextual meaning of text, resulting in highly accurate section rankings that align with the user's true intent.
* **Performance Under Constraints:** The entire pipeline is optimized for speed, processing multiple documents in under 60 seconds on a standard CPU. The ML model's small footprint (**under 500MB**) comfortably meets the hackathon's performance requirements.
* **Completely Offline:** A critical feature is that the entire analysis process runs locally without any need for an internet connection, ensuring absolute data privacy and compliance with hackathon rules.
* **Intelligent Section Extraction:** Automatically identifies and extracts structured sections (headings and content) from multiple PDFs.
* **Persona-Driven Analysis:** Ranks the extracted sections based on their relevance to a given persona and "job-to-be-done."

## Models and Libraries Used

* **`PyMuPDF`**: For robust and fast PDF text and structure parsing.
* **`sentence-transformers`**: To load and use the `all-mpnet-base-v2` embedding model.
* **`scikit-learn`**: For calculating cosine similarity and for keyword extraction via `TfidfVectorizer`.
* **`numpy`**: For numerical operations.

## 🛠️ Execution Instructions

The solution is containerized with Docker for seamless execution as per the hackathon requirements.

### 1. Build and Run with Docker (Recommended)

From the project’s root directory, run:

```bash
# Build the Docker image
docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .

# Run the container
docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" --network none mysolutionname:somerandomidentifier
```

### 2. Run Locally

* **Windows**: Double-click and run `run_project.bat`.
* **Linux/macOS**: Open a terminal and run `./run_project.sh`.

After execution, the results will be saved in the `output/output.json` file.
