import os
import json
import faiss
import argparse
from sentence_transformers import SentenceTransformer


def embed_realm(realm_id):
    base_path = f"libraries/{realm_id}/documents"
    index_path = f"libraries/{realm_id}/faiss_index"
    os.makedirs(index_path, exist_ok=True)

    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("Model loaded.")

    documents = []
    for doc_type in ["kbd", "tsd"]:
        folder = os.path.join(base_path, doc_type)
        if not os.path.exists(folder):
            print(f"Folder not found: {folder}")
            continue

        for filename in os.listdir(folder):
            if filename.endswith(".json"):
                file_path = os.path.join(folder, filename)
                print(f"Scanning: {file_path}")
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        if "type" in data and "title" in data:
                            documents.append(data)
                        else:
                            print(f"Skipped {filename} — missing required fields.")
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse {filename}: {e}")

    if not documents:
        print(f"No valid documents found in realm '{realm_id}'.")
        return

    texts, metadata = [], []
    for doc in documents:
        if doc["type"] == "kbd":
            text = f"{doc['type']}: {doc['title']}\n{doc.get('content', '')}\nTags: {', '.join(doc.get('tags', []))}"
        else:
            text = f"{doc['type']}: {doc['title']}\nIssue: {doc.get('issue_description', '')}\nResolution: {doc.get('resolution_steps', '')}\nTags: {', '.join(doc.get('tags', []))}"
        texts.append(text)
        metadata.append(doc)

    embeddings = model.encode(texts, show_progress_bar=True)
    dim = embeddings[0].shape[0]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, os.path.join(index_path, "articles.index"))
    with open(os.path.join(index_path, "articles_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Embedded {len(texts)} documents to '{index_path}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--realm", type=str, required=True, help="Realm ID (e.g. 'git')"
    )
    args = parser.parse_args()
    embed_realm(args.realm)
