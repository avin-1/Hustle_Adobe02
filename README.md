# Adobe Hackathon - Round 1B Submission

## Our Approach

Our solution tackles the "Persona-Driven Document Intelligence" challenge by implementing a semantic analysis pipeline. The core of our approach is based on the following steps:

1.  **Structured Content Extraction**: We first parse each PDF using our robust engine from Round 1A. This engine identifies not only headings (H1, H2, H3) but also intelligently associates all the text content that belongs to each heading, forming structured "sections."
2.  **Semantic Representation**: We use a pre-trained `all-MiniLM-L6-v2` sentence-transformer model to convert the user's query (a combination of their persona and job-to-be-done) and each document section into high-dimensional vectors (embeddings). This model was chosen for its excellent balance of performance and small size (under 100MB), making it ideal for the offline, CPU-only environment.
3.  **Relevance Ranking**: The relevance of each section is calculated by computing the cosine similarity between the query embedding and the section's embedding. This gives us a precise score indicating how well a section answers the user's need. Sections are then ranked globally across all documents.
4.  **Granular Sub-section Analysis**: For the top-ranked sections, we perform a sub-section analysis using a TF-IDF vectorizer to extract the most significant keywords. This provides a "refined text" summary, giving the user a quick glance at the core topics of the most relevant content.

## Models and Libraries Used

-   **`PyMuPDF`**: For robust and fast PDF text and structure parsing.
-   **`sentence-transformers`**: To load and use the `all-MiniLM-L6-v2` embedding model.
-   **`scikit-learn`**: For calculating cosine similarity and for keyword extraction via `TfidfVectorizer`.
-   **`numpy`**: For numerical operations.

## How to Build and Run the Solution

### Build the Docker Image

Navigate to the project root directory and run the following command:
docker build -t my-1b-solution .

```bash



### Project Setup Instructions

This repository contains the codebase for our project. Please follow **each step carefully** to set up and run the project successfully.


## 🛠️ Setup Instructions

### 1. Clone the Repository
Open your terminal or CMD and run:

git clone https://github.com/avin-1/Hustle_Adobe02.git

 *Clone Directory then make virtual environment using this command

python -m venv venv

 then activate venv using
 venv\scripts\activate

then run this command

pip install -r requirement.txt

 then after wards run

python download_model.py

this will create model directory and add model into it after run the python script main.py using
python src/main.py

 Note: run main.py from root directory only dont go inside src then run  
