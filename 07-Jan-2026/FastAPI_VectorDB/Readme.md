FastAPI Vector Database (Ollama)
What this project does

This project converts input text into vector embeddings using Ollama and stores them in a vector database exposed via a FastAPI REST API.

It demonstrates the core building block behind semantic search and RAG systems:

text → embedding → vector storage → retrieval

The system is general-purpose and not tied to any specific dataset.

How it works (high level)

Client sends text via an API request

Ollama generates a numeric embedding for the text

The embedding is stored along with metadata

Stored vectors can be inspected via debug endpoints

Tech stack

FastAPI – REST API

Ollama – local embedding generation (no API keys)

Vector Storage – in-memory / persistent (project dependent)

Python

API flow
Add a document (store vector)

POST /add-document

{
  "text": "FastAPI is a modern Python framework"
}


What happens

Text is converted to a vector

Vector is stored in the database

Search using a query

POST /search

{
  "query": "Python API framework",
  "top_k": 3
}


What happens

Query is embedded

Similar vectors are retrieved

Results are returned

Debug endpoints

GET /debug/documents
Shows stored documents with vector previews

GET /debug/queries
Shows stored query embeddings

These endpoints prove that vectors are actually being created and stored.

Run the project
uvicorn app.main:app --reload


Open Swagger UI:

http://127.0.0.1:8000/docs

Why this project matters

This project demonstrates:

Understanding of embeddings

Vector storage fundamentals

API-based ML system design

Foundations for RAG and semantic search systems
