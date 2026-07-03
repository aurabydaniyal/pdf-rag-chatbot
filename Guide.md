# 📦 PDF RAG Chatbot – Complete Installation Guide

## 1. System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python    | 3.11    | 3.12        |
| Node.js   | 16.0    | 18.0+       |
| npm       | 8.0     | 9.0+        |
| Git       | Latest  | Latest      |
| RAM       | 4 GB    | 8 GB+       |
| Storage   | 2 GB    | 5 GB+       |

---

## 2. Pre‑Installation Checklist

- [ ] Python installed (`python --version`)
- [ ] Node.js installed (`node --version`)
- [ ] npm installed (`npm --version`)
- [ ] Git installed (`git --version`)
- [ ] Stable internet connection
- [ ] Admin/root rights (if required)

---

## 3. Install Ollama (Local LLM)

Ollama is required to run the language model locally.

### Windows
```powershell
# Download from: https://ollama.com/download/windows
# Or via winget
winget install Ollama.Ollama
```

### macOS
```bash
# Using Homebrew
brew install ollama

# Or download from: https://ollama.com/download/mac
```

### Linux
```bash
# Ubuntu/Debian
curl -fsSL https://ollama.com/install.sh | sh

# Arch Linux
yay -S ollama
```

### Pull the Required Model
```bash
ollama pull phi3:mini          # ~2 GB (recommended)
# Optional alternatives:
ollama pull gemma3:4b          # ~2.5 GB (better quality)
ollama pull qwen2.5:3b         # ~1.8 GB (faster)
```

---

## 4. Clone the Repository

```bash
git clone https://github.com/aurabydaniyal/pdf-rag-chatbot.git
cd pdf-rag-chatbot
```

---

## 5. Setup Python Backend

### Windows (PowerShell)
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Backend Dependencies (`requirements.txt`)
```txt
fastapi==0.104.1
uvicorn==0.24.0
pymupdf==1.23.8
langchain==0.3.0
langchain-text-splitters==0.3.0
sentence-transformers==2.2.2
chromadb==0.5.0
requests==2.31.0
python-multipart==0.0.6
```

---

## 6. Setup React Frontend

```bash
cd ../frontend
npm install
```

### Frontend Dependencies (`package.json`)
```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "bootstrap": "^5.3.0",
    "framer-motion": "^10.16.0",
    "react": "^18.2.0",
    "react-bootstrap": "^2.9.0",
    "react-copy-to-clipboard": "^5.1.0",
    "react-dom": "^18.2.0",
    "react-dropzone": "^14.2.3",
    "react-icons": "^4.11.0",
    "react-loader-spinner": "^5.3.4",
    "react-scripts": "5.0.1"
  }
}
```

---

## 7. Pre‑Download Embedding Model (Optional)

```bash
cd ../backend
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2'); print('✅ Model ready')"
```

---

## 8. Verify Installations

### Backend
```bash
python -c "import fastapi, uvicorn, fitz, langchain, chromadb; print('✅ Backend packages OK')"
```

### Frontend
```bash
cd ../frontend
npm list --depth=0
```

---

## 9. Quick Start Commands

### Start All Services
```bash
# Terminal 1 – Ollama
ollama serve

# Terminal 2 – Backend
cd backend
source venv/bin/activate          # Windows: venv\Scripts\activate
python app.py

# Terminal 3 – Frontend
cd frontend
npm start
```

### Access the Application
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## 10. Troubleshooting Common Issues

| Issue | Solution |
|-------|----------|
| `pip not found` | `python -m ensurepip --upgrade` |
| Permission errors | Add `--user` flag to pip install |
| Python 3.14 issues | Use Python 3.11 or 3.12 |
| `node_modules` errors | `npm cache clean --force` |
| Ollama not recognized | Add to PATH or restart terminal |
| ModuleNotFoundError | Activate virtual environment |
| Connection timeout | Check firewall/proxy settings |

---

## 11. Uninstall / Cleanup

```bash
# Remove project
rm -rf pdf-rag-chatbot

# Remove Ollama model
ollama rm phi3:mini

# Uninstall Ollama (if needed)
# Windows: Control Panel → Programs → Uninstall
# macOS: brew uninstall ollama
# Linux: depends on installation method
```

---

## 12. File Size Summary

| Component | Size | Notes |
|-----------|------|-------|
| phi3:mini model | ~2 GB | Ollama model |
| all-MiniLM‑L6‑v2 | ~90 MB | Embedding model |
| Python packages | ~200 MB | Virtual environment |
| Node packages | ~150 MB | `node_modules` |
| Source code | ~5 MB | Your project files |
| **Total** | **~2.5 GB** | |

---

## 13. Update Commands

```bash
# Update backend
cd backend
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install --upgrade -r requirements.txt

# Update frontend
cd ../frontend
npm update

# Update Ollama model
ollama pull phi3:mini
```

---

## 14. Quick Reference Card

| Command | Purpose |
|---------|---------|
| `ollama serve` | Start LLM server |
| `python app.py` | Start backend |
| `npm start` | Start frontend |
| `ollama pull phi3:mini` | Download model |
| `deactivate` | Exit virtual environment |
| `Ctrl+C` | Stop any running server |

---

✅ **Installation Complete!** Your PDF RAG Chatbot is ready to use.  
For issues or contributions, visit the [GitHub repository](https://github.com/aurabydaniyal/pdf-rag-chatbot).
