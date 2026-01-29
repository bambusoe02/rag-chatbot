# Installation Guide

## Web Application (Recommended for Most Users)

### Quick Start

No installation needed! Just visit:
```
https://rag-chatbot.com
```
Create an account and start using immediately.

### System Requirements

- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection
- JavaScript enabled

## Self-Hosted Installation

Want to run RAG Chatbot on your own server? Follow these steps.

### Prerequisites

- Docker and Docker Compose
- 8GB RAM minimum (16GB recommended)
- 20GB disk space
- Linux, macOS, or Windows with WSL2

### Option 1: Docker Compose (Easiest)

**1. Clone the repository:**
```bash
git clone https://github.com/yourusername/rag-chatbot.git
cd rag-chatbot
```

**2. Configure environment:**
```bash
cp .env.example .env
# Edit .env with your settings
nano .env
```

**3. Start services:**
```bash
docker-compose up -d
```

**4. Access application:**
```
http://localhost:8501
```

**5. Create first admin user:**
```bash
docker-compose exec backend python create_admin.py
```

### Option 2: Manual Installation

**1. Install Python 3.11+:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3-pip

# macOS
brew install python@3.11

# Windows
# Download from python.org
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Install Ollama (for local LLM):**
```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Windows
# Download from ollama.com
```

**4. Pull LLM model:**
```bash
ollama pull qwen2.5:14b-instruct
```

**5. Initialize database:**
```bash
python init_db.py
```

**6. Start backend:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**7. Start frontend (new terminal):**
```bash
streamlit run frontend/app.py --server.port 8501
```

**8. Access application:**
```
http://localhost:8501
```

## Verification

Check all services are running:
```bash
# Check backend
curl http://localhost:8000/health/status

# Should return: {"status": "healthy"}

# Check frontend
curl http://localhost:8501/_stcore/health

# Should return: {"status": "ok"}
```

## Troubleshooting Installation

### Port already in use:
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn backend.main:app --port 8001
```

### Docker permission denied:
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in
```

### Ollama not found:
```bash
# Check Ollama is installed
ollama --version

# Start Ollama service
ollama serve
```

### Database error:
```bash
# Reinitialize database
rm data/app.db
python init_db.py
```

## Next Steps

✅ Installation complete! Now:
1. [Create your first account](first-steps.md)
2. [Upload a document](../tutorials/knowledge-base.md)
3. [Ask your first question](../guides/asking-questions.md)

## Need Help?

- 📧 Email: support@rag-chatbot.com
- 💬 Discord: https://discord.gg/ragchatbot
- 🐛 GitHub Issues: https://github.com/yourusername/rag-chatbot/issues

