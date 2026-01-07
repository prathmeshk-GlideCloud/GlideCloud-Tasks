FastAPI Vector Database (Ollama)
📌 Overview

This project converts input text into vector embeddings using Ollama and stores them in a vector database exposed via a FastAPI REST API.

It demonstrates the core building block behind semantic search and Retrieval-Augmented Generation (RAG) systems:

Text → Embedding → Vector Storage → Retrieval


The system is general-purpose and not tied to any specific dataset.

⚙️ How It Works (High Level)

A client sends text through a REST API request

Ollama generates a numeric embedding for the text

The embedding is stored along with metadata in a vector database

Stored vectors can be inspected using debug endpoints

🛠 Tech Stack

FastAPI – REST API framework

Ollama – Local embedding generation (no API keys required)

Vector Storage – In-memory or persistent (project dependent)

Python

🔁 API Flow
➕ Add a Document (Store Vector)

Endpoint

POST /add-document


Request Body

{
  "text": "FastAPI is a modern Python framework"
}


What Happens

Input text is converted into a vector embedding

The vector is stored in the vector database

🔍 Search Using a Query

Endpoint

POST /search


Request Body

{
  "query": "Python API framework",
  "top_k": 3
}


What Happens

The query text is embedded

Similar vectors are retrieved using vector similarity

Matching documents are returned

🐞 Debug Endpoints
View Stored Documents
GET /debug/documents


Shows stored documents

Displays a preview of vector values

View Stored Queries
GET /debug/queries


Shows stored query embeddings

Displays a preview of vector values

These endpoints confirm that vectors are being generated and stored correctly.

▶️ Run the Project

From the project root directory:

uvicorn app.main:app --reload


Open Swagger UI:

http://127.0.0.1:8000/docs

🎯 Why This Project Matters

This project demonstrates:

Practical understanding of embeddings

Vector storage fundamentals

API-driven ML system design

Strong foundation for semantic search and RAG pipelines
