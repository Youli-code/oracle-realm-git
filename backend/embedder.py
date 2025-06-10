import os
import json
import faiss
import psycopg2
import argparse
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# === Load Environment Variables ===
load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# === Parse CLI Argument ===
parser = argparse.ArgumentParser(description="Embed documents for a specific realm")
parser.add_argument(
    "--realm", type=str, default="git", help="Realm ID to embed (e.g., git, cicd)"
)
args = parser.parse_args()
REALM_ID = args.realm

# === Connect to PostgreSQL ===
try:
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    print("✅ Connected to PostgreSQL.")
except Exception as e:
    print("❌ Failed to connect to DB:", e)
    exit()

# === Load SentenceTransformer Model ===
model = SentenceTransformer("all-MiniLM-L6-v2")
print("🧠 Model loaded.")

# === Fetch Realm Articles ===
cursor.execute(
    "SELECT * FROM articles WHERE realm = %s AND status = 'published';", (REALM_ID,)
)
articles = cursor.fetchall()

if not articles:
    print(f"⚠️ No published articles found for realm '{REALM_ID}'.")
    exit()

# === Build Embedding List ===
texts = []
metadata = []
for i, article in enumerate(articles):
    text_blob = f"{article['type']}: {article['title']}\n{article['content']}\nTags: {', '.join(article['tags'])}"
    texts.append(text_blob)
    metadata.append(
        {
            "id": i,
            "db_id": article.get("id"),
            "type": article.get("type"),
            "title": article.get("title"),
            "content": article.get("content"),
            "tags": article.get("tags"),
            "realm": REALM_ID,
        }
    )

# === Generate Embeddings ===
print("⚙️ Generating embeddings...")
embeddings = model.encode(texts, show_progress_bar=True)

# === Create FAISS Index ===
embedding_dim = embeddings[0].shape[0]
index = faiss.IndexFlatL2(embedding_dim)
index.add(embeddings)
print(f"✅ FAISS index built with {len(embeddings)} entries for realm '{REALM_ID}'.")

# === Save Index and Metadata ===
index_dir = os.path.join("libraries", REALM_ID, "faiss_index")
os.makedirs(index_dir, exist_ok=True)

faiss.write_index(index, os.path.join(index_dir, "articles.index"))
with open(os.path.join(index_dir, "articles_metadata.json"), "w") as f:
    json.dump(metadata, f, indent=2)

print(f"📦 Index + metadata saved to '{index_dir}' for realm '{REALM_ID}'.")
