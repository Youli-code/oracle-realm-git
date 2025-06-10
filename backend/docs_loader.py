import os
import json
from fastapi import APIRouter, HTTPException, Query
from typing import List

router = APIRouter()


def load_documents_from_folder(folder_path: str) -> List[dict]:
    print(f"Scanning folder: {folder_path}")

    if not os.path.exists(folder_path):
        print("Folder does not exist.")
        return []

    docs = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            full_path = os.path.join(folder_path, filename)
            print(f"Found file: {filename}")
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                    doc["id"] = os.path.splitext(filename)[0]
                    docs.append(doc)
            except Exception as e:
                print(f"Failed to load {filename}: {e}")
    print(f"Loaded {len(docs)} documents.")
    return docs


@router.get("/api/docs/kbd")
def get_kbd_docs(realm: str = Query(...)):
    folder = os.path.join("libraries", realm, "documents", "kbd")
    print(f"\nGET /api/docs/kbd?realm={realm}")
    print(f"Target path: {folder}")

    docs = load_documents_from_folder(folder)
    if not docs:
        raise HTTPException(status_code=404, detail="No KBD documents found.")
    return docs


@router.get("/api/docs/tsd")
def get_tsd_docs(realm: str = Query(...)):
    folder = os.path.join("libraries", realm, "documents", "tsd")
    print(f"\nGET /api/docs/tsd?realm={realm}")
    print(f"Target path: {folder}")

    docs = load_documents_from_folder(folder)
    if not docs:
        raise HTTPException(status_code=404, detail="No TSD documents found.")
    return docs


print("docs_loader router initialized")
