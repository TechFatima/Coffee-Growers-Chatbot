# ☕ Coffee Growers Chatbot

A document-based AI chatbot designed to help coffee growers find answers from coffee farming resources. Users can upload PDF documents—such as cultivation guides, disease-management manuals, or best-practice reports—and ask questions in natural language.

The application uses Retrieval-Augmented Generation (RAG), meaning its responses are grounded in the uploaded documents instead of relying only on a general AI model.

## Features

- Upload one or more coffee-related PDF documents
- Extract text from uploaded PDFs
- Split document text into manageable chunks
- Convert chunks into vector embeddings using Cohere
- Store embeddings locally using ChromaDB
- Search the most relevant document sections for each user question
- Generate context-aware answers with Cohere Chat
- Maintain chat history during the active Streamlit session
- Coffee-themed custom user interface with a background image, animated coffee icons, and styled chat messages

## How It Works

1. The user uploads PDF documents through the sidebar.
2. The app reads each PDF using `pypdf`.
3. Extracted text is split into chunks of approximately 900 characters.
4. Cohere's embedding model converts each chunk into a numerical vector.
5. ChromaDB stores the text chunks and vectors in a local persistent database.
6. When the user asks a question, the question is also converted into an embedding.
7. ChromaDB retrieves the three most relevant document chunks.
8. Those chunks are sent to Cohere along with the question.
9. Cohere generates a final answer based on the retrieved context.

## Tech Stack

- **Python** — application logic
- **Streamlit** — interactive web interface
- **Cohere API** — text embeddings and AI-generated answers
- **ChromaDB** — local vector database for semantic search
- **PyPDF** — PDF text extraction
- **python-dotenv** — secure loading of API keys

## Project Structure

```text
coffee/
├── app.py                 # Main Coffee Growers Chatbot application
├── coff.py                # Earlier/alternate version of the chatbot UI
├── COFFEE BOOKS.jpg       # Background image used in the chatbot interface
├── chroma_db/             # Local persistent ChromaDB data
├── .env                   # Stores the Cohere API key locally
├── game.py                # Separate Flask number-guessing demo (ignored by Git)
└── templates/
    └── index.html         # Front end for the Flask game demo
