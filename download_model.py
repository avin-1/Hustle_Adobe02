from sentence_transformers import SentenceTransformer
import os

# Define the model name and the path to save it
MODEL_NAME = 'all-mpnet-base-v2'
SAVE_PATH = 'model/'

# Create the save directory if it doesn't exist
if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)

print(f"Downloading model: {MODEL_NAME}")

# Download and save the model
model = SentenceTransformer(MODEL_NAME)
model.save(SAVE_PATH + MODEL_NAME)

print(f"Model saved successfully to {SAVE_PATH}{MODEL_NAME}")