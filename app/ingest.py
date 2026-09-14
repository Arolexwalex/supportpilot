# app/ingest.py
from google import genai
import chromadb
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
db = chromadb.PersistentClient(path="./chroma_db")
collection = db.get_or_create_collection("support_docs")

def chunk_text(text, chunk_size=500):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def embed(text):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

def read_file_safely(filepath):
    encodings_to_try = ["utf-8", "utf-16", "latin-1"]
    for encoding in encodings_to_try:
        try:
            with open(filepath, encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {filepath} with any known encoding")

def ingest_document(filepath, doc_id):
    text = read_file_safely(filepath)
    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks):
        collection.add(
            ids=[f"{doc_id}-{i}"],
            embeddings=[embed(chunk)],
            documents=[chunk],
            metadatas=[{"source": doc_id}]
        )
    print(f"Ingested {len(chunks)} chunks from {doc_id}")

if __name__ == "__main__":
    for filename in os.listdir("docs"):
        ingest_document(f"docs/{filename}", filename)