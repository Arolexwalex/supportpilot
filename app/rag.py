# app/rag.py
from google import genai
from groq import Groq
import chromadb
import os
import json
import logging
import time
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
db = chromadb.PersistentClient(path="./chroma_db")
collection = db.get_or_create_collection("scamshield_docs")

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

def build_prompt(question, context):
    return f"""You are Pangolin, a friendly Nigerian assistant that helps people understand and recognize online scams. Answer naturally and warmly, like a knowledgeable friend, not a formal document. You may use a light, natural touch of Nigerian Pidgin where it fits, but keep it clear.
    

Never mention "the context" or "the provided text" — just answer as if you simply know this information.

If the answer isn't covered by what you know below, say you don't have that information — without mentioning documents or context.

What you know:
{context}

Question: {question}"""

def stream_from_groq(prompt):
    stream = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content

def generate_answer(question):
    chunks = retrieve(question)
    context = "\n\n".join(chunks)
    prompt = build_prompt(question, context)

    try:
        response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        return response.text, chunks
    except Exception as e:
        logging.warning(f"Gemini failed ({e}), falling back to Groq for eval")
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content, chunks

def generate_answer_stream(question, max_retries=3):
    try:
        chunks = retrieve(question)
        context = "\n\n".join(chunks)
        prompt = build_prompt(question, context)

        try:
            for attempt in range(max_retries):
                try:
                    response_stream = client.models.generate_content_stream(
                        model="gemini-3.6-flash",
                        contents=prompt
                    )
                    for chunk in response_stream:
                        if chunk.text:
                            yield chunk.text
                    logging.info(f"Answered via Gemini. Sources for '{question[:50]}...': {json.dumps(chunks)}")
                    return
                except Exception as e:
                    if "503" in str(e) and attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logging.warning(f"Model overloaded, retrying in {wait_time}s (attempt {attempt + 1})")
                        time.sleep(wait_time)
                        continue
                    raise
        except Exception as e:
            logging.warning(f"Gemini failed after retries ({e}), falling back to Groq")
            yield from stream_from_groq(prompt)
            logging.info(f"Answered via Groq fallback. Sources for '{question[:50]}...': {json.dumps(chunks)}")

    except Exception as e:
        yield "I'm having trouble reaching the AI service right now — please try again in a moment."
        logging.error(f"generate_answer_stream failed completely: {e}")