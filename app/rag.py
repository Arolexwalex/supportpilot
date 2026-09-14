# app/rag.py
from google import genai
import chromadb
import os
from dotenv import load_dotenv
import json
import logging

load_dotenv()


def generate_answer_stream(question):
    try:
        chunks = retrieve(question)
        context = "\n\n".join(chunks)
        prompt = f"""You are Nimbus's support assistant. Answer the question naturally and directly, the way a knowledgeable support agent would — as if you simply know this information. Never mention "the context," "the provided text," or that you're referencing documents.

If the answer isn't covered by what you know below, say you don't have that information — without mentioning documents or context.

What you know:
{context}

Question: {question}"""

        response_stream = client.models.generate_content_stream(
            model="gemini-3.6-flash",
            contents=prompt
        )
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
        logging.info(f"Sources used for  '{question[:50]}...': {json.dumps(chunks)  }")
    except Exception as e:
        yield f"\n\n[ERROR: {str(e)}]"

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
db = chromadb.PersistentClient(path="./chroma_db")
collection = db.get_or_create_collection("support_docs")

def embed_query(text):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

def retrieve(question, top_k=3):
    query_embedding = embed_query(question)
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    return results["documents"][0]

def generate_answer(question):
    chunks = retrieve(question)
    context = "\n\n".join(chunks)
    prompt = f"""You are Nimbus's support assistant. Answer the question naturally and directly, the way a knowledgeable support agent would — as if you simply know this information. Never mention "the context," "the provided text," or that you're referencing documents.

If the answer isn't covered by what you know below, say you don't have that information — without mentioning documents or context.

What you know:
{context}

Question: {question}"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text, chunks