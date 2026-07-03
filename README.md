# 📚 PDF RAG Chatbot

A 100% free, local RAG (Retrieval-Augmented Generation) chatbot that answers questions from your PDF documents.

## ✨ Features

- 📄 **Upload PDFs** - Upload multiple PDF documents
- 🔍 **Semantic Search** - Uses embeddings for intelligent retrieval
- 🤖 **Local LLM** - Powered by Ollama (phi3:mini)
- 💾 **Persistent Storage** - Documents stored in ChromaDB
- 📱 **Responsive UI** - Beautiful React frontend with glassmorphism
- 🔒 **100% Local** - No cloud dependencies, complete privacy

## 🏗️ Architecture

- 📤 Upload PDF → 🔍 Extract Text → ✂️ Chunk → 🧠 Embed → 💾 Store 
- ❓ Ask Question → 🔍 Search → 📊 Retrieve → 🤖 Generate → 💬 Answer


## 📋 Prerequisites

- Python 3.11 or higher
- Node.js 16 or higher
- Ollama (for local LLM)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/aurabydaniyal/pdf-rag-chatbot.git
cd pdf-rag-chatbot

cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py

cd frontend
npm install
npm start

ollama serve

