import os
import json
import faiss
import traceback
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# Resolve and load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=str(env_path))

# Debug (optional): Confirm API key is found
print("OPENAI_API_KEY =", os.getenv("OPENAI_API_KEY"))

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not found in environment variables")

client = OpenAI(api_key=api_key)
router = APIRouter()
model = SentenceTransformer("all-MiniLM-L6-v2")


class AskRequest(BaseModel):
    question: str
    realm: str


@router.post("/api/ask")
def ask_oracle(req: AskRequest):
    question = req.question.strip()
    realm = req.realm.strip().lower()
    realm_path = f"libraries/{realm}/faiss_index"

    index_file = os.path.join(realm_path, "articles.index")
    meta_file = os.path.join(realm_path, "articles_metadata.json")

    if not os.path.exists(index_file) or not os.path.exists(meta_file):
        raise HTTPException(status_code=404, detail="Realm index not found.")

    try:
        index = faiss.read_index(index_file)
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load index or metadata: {e}"
        )

    question_vec = model.encode([question])
    top_k = 5
    D, I = index.search(question_vec, top_k)

    top_docs = []
    context_parts = []

    for idx, score in zip(I[0], D[0]):
        if idx >= len(metadata):
            continue
        doc = metadata[idx]
        score_fmt = f"{score:.2f}"
        print(f"Match: {doc.get('title')} (type={doc.get('type')}, score={score_fmt})")
        top_docs.append(doc)

        if doc.get("type") == "kbd":
            context_parts.append(f"KBD: {doc.get('title')}\n{doc.get('content')}")
        elif doc.get("type") == "tsd":
            issue = doc.get("issue_description", "No issue description provided.")
            resolution = doc.get("resolution_steps", "No resolution steps provided.")
            context_parts.append(
                f"TSD: {doc.get('title')}\nIssue: {issue}\nResolution: {resolution}"
            )

    if not context_parts:
        return {
            "answer": "No relevant documents found in the knowledge base.",
            "references": [],
        }

    context_text = "\n\n".join(context_parts)
    prompt = (
        f"You are the Oracle AI. Answer the user's question using only the context below.\n\n"
        f"Context:\n{context_text}\n\nQuestion: {question}\nAnswer:"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful DevOps assistant. Only answer using the provided context.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=500,
        )
        answer = response.choices[0].message.content.strip()

        return {
            "answer": answer,
            "references": [
                {
                    "title": d.get("title"),
                    "type": d.get("type"),
                    "tags": d.get("tags", []),
                    "id": d.get("id", f"file_{i}"),
                }
                for i, d in enumerate(top_docs)
            ],
        }

    except Exception as e:
        print("OpenAI request failed:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="OpenAI error. Check server logs.")
