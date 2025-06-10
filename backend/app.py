import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import openai

# Load environment variables
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)

# DB connection
try:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    print("Database connection successful!")
except Exception as e:
    print("Error connecting to the database:", e)
    exit()

# Load FAISS index + metadata
try:
    faiss_index = faiss.read_index("faiss_index/articles.index")
    with open("faiss_index/articles_metadata.json", "r") as f:
        article_metadata = json.load(f)
    vector_model = SentenceTransformer("all-MiniLM-L6-v2")
    print("FAISS index and embedding model loaded.")
except Exception as e:
    print("Warning: Could not load FAISS index or metadata.", e)
    faiss_index = None
    article_metadata = []
    vector_model = None


@app.route("/articles", methods=["POST"])
def add_article():
    try:
        data = request.json
        cursor.execute(
            """
            INSERT INTO articles (type, title, content, tags)
            VALUES (%s, %s, %s, %s)
            RETURNING *;
            """,
            (data["type"], data["title"], data["content"], data["tags"]),
        )
        new_article = cursor.fetchone()
        conn.commit()
        return jsonify(new_article), 201
    except Exception as e:
        print("Error adding article:", e)
        return jsonify({"error": "Failed to add article"}), 500


@app.route("/articles", methods=["GET"])
def get_articles():
    try:
        cursor.execute("SELECT * FROM articles;")
        articles = cursor.fetchall()
        return jsonify(articles), 200
    except Exception as e:
        print("Error retrieving articles:", e)
        return jsonify({"error": "Failed to retrieve articles"}), 500


@app.route("/ask", methods=["POST"])
def ask_question():
    try:
        data = request.json
        question = data.get("question")
        if not question:
            return jsonify({"error": "No question provided"}), 400

        if not faiss_index or not vector_model:
            return jsonify({"error": "Vector search system not available."}), 500

        query_vector = vector_model.encode([question])
        query_vector = np.array(query_vector).astype("float32")
        distances, indices = faiss_index.search(query_vector, 10)
        relevance_threshold = 1.1  # stricter = fewer matches

        references = []
        context = ""

        for i, idx in enumerate(indices[0]):
            if idx < len(article_metadata) and distances[0][i] < relevance_threshold:
                article = article_metadata[idx]
                context += f"Title: {article['title']}\nContent: {article['content']}\nTags: {', '.join(article['tags'])}\n---\n"
                references.append(
                    {
                        "title": article["title"],
                        "type": article["type"],
                        "tags": article["tags"],
                        "id": article["db_id"],
                    }
                )

        if not context:
            return jsonify(
                {"answer": "No relevant documents found in the knowledge base."}
            )

        messages = [
            {
                "role": "system",
                "content": "You are an assistant that answers only based on the provided context documents. If unsure, say so.",
            },
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.3,
        )

        answer = response.choices[0].message.content
        return jsonify({"answer": answer, "references": references})

    except Exception as e:
        print("Error in /ask:", e)
        return jsonify({"error": "Failed to process the question"}), 500


@app.route("/generate-article", methods=["POST"])
def generate_article():
    try:
        data = request.json
        doc_type = data.get("type")
        prompt = data.get("prompt")

        if doc_type not in ["KBD", "TSD"] or not prompt:
            return jsonify({"error": "Invalid input"}), 400

        system_template = {
            "KBD": (
                "You are an AI documentation assistant. Given a user prompt, generate a JSON object for a KBD document. "
                "Use the following fields: type, title, summary, content, tags, last_updated (YYYY-MM-DD)."
            ),
            "TSD": (
                "You are an AI support assistant. Given a user prompt, generate a JSON object for a TSD document. "
                "Use the following fields: type, title, summary, issue_description, resolution_steps, tags, last_updated (YYYY-MM-DD)."
            ),
        }

        messages = [
            {"role": "system", "content": system_template[doc_type]},
            {"role": "user", "content": f"Prompt: {prompt}"},
        ]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages, temperature=0.4
        )

        content = response.choices[0].message.content
        return jsonify({"generated": content})

    except Exception as e:
        print("Error in /generate-article:", e)
        return jsonify({"error": "Failed to generate article"}), 500


@app.route("/articles/<int:article_id>", methods=["GET"])
def get_article_by_id(article_id):
    try:
        cursor.execute("SELECT * FROM articles WHERE id = %s;", (article_id,))
        article = cursor.fetchone()
        if article:
            return jsonify(article)
        else:
            return jsonify({"error": "Article not found"}), 404
    except Exception as e:
        print("Error fetching article by ID:", e)
        return jsonify({"error": "Failed to fetch article"}), 500


@app.route("/")
def home():
    return "Welcome to the AI Knowledge Bot Backend!"


@app.route("/favicon.ico")
def favicon():
    return "", 204


if __name__ == "__main__":
    app.run(debug=True)
