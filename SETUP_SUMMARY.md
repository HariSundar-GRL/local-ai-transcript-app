# AI Transcript App - Docker Setup Summary

**Date:** December 18, 2025
**Project:** Local AI Transcript App
**Repository:** HariSundar-GRL/local-ai-transcript-app

---

## 📋 Overview

This document summarizes all modifications made to run the AI Transcript App using Docker containers, and provides the commands needed to run the servers.

---

## 🔧 Changes Made to Original Code

### 1. **Modified: `.devcontainer/docker-compose.yml`**

**Location:** `e:\Hari Sundar\local-ai-transcript-app\.devcontainer\docker-compose.yml`

#### Changes:

1. **Removed obsolete `version` attribute** (Line 1)

   - **Before:**

     ```yaml
     version: "3.8"

     services:
     ```
   - **After:**

     ```yaml
     services:
     ```
   - **Reason:** Docker Compose v2+ doesn't require version specification and shows warnings
2. **Commented out `user: vscode` directive** (Line 19)

   - **Before:**
     ```yaml
     # Use non-root user
     user: vscode
     ```
   - **After:**
     ```yaml
     # Use non-root user (commented out for manual docker-compose)
     # user: vscode
     ```
   - **Reason:** The `vscode` user is created by devcontainer features, which don't run in manual docker-compose. Running as root in container avoids permission issues when running manually.

### 2. **Fixed: `.devcontainer/post-create.sh`**

**Location:** `e:\Hari Sundar\local-ai-transcript-app\.devcontainer\post-create.sh`

#### Issue Fixed:

- **Problem:** Script had Windows line endings (CRLF - `\r\n`)
- **Solution:** Converted to Unix line endings (LF - `\n`) using `dos2unix`
- **Command Used:**
  ```bash
  docker exec -it devcontainer-app-1 bash -c "dos2unix /workspaces/ai-transcript-app/.devcontainer/post-create.sh"
  ```
- **Reason:** Bash scripts in Linux containers require Unix line endings. Windows line endings cause syntax errors like `$'\r': command not found`

### 3. **Created: `backend/.env`**

**Location:** `e:\Hari Sundar\local-ai-transcript-app\backend\.env`

#### Status:

- **Already existed** in the workspace (based on context)
- **Contents:**

  ```bash
  # LLM API Configuration (OpenAI-compatible)
  LLM_BASE_URL=http://ollama:11434/v1
  LLM_API_KEY=ollama
  LLM_MODEL=gemma3:4b

  # Whisper Configuration (local speech-to-text)
  WHISPER_MODEL=base.en
  ```

---

## 🐳 Docker Setup Process

### Prerequisites Verified:

- ✅ Docker Desktop installed and running
- ✅ Docker version: 29.1.2
- ✅ Docker Compose available

### Containers Created:

| Container Name            | Image                         | Purpose                                    | Ports      |
| ------------------------- | ----------------------------- | ------------------------------------------ | ---------- |
| `devcontainer-app-1`    | `devcontainer-app` (custom) | Development environment (Python + Node.js) | 8000, 3000 |
| `devcontainer-ollama-1` | `ollama/ollama:0.12.9`      | LLM inference server                       | 11434      |

### Volume Created:

- `ai-transcript-ollama-models` - Persistent storage for Ollama models (~3.3GB for Gemma3:4b)

---

## 💻 Commands Used - Complete Workflow

### **Step 1: Start Docker Containers**

```powershell
# Navigate to devcontainer directory
cd "e:\Hari Sundar\local-ai-transcript-app\.devcontainer"

# Start containers in detached mode
docker-compose up -d
```

**Output:**

```
✔ Network devcontainer_default     Created
✔ Container devcontainer-ollama-1  Started
✔ Container devcontainer-app-1     Started
```

---

### **Step 2: Fix Line Endings Issue**

```powershell
# Install dos2unix utility in container
docker exec -it devcontainer-app-1 bash -c "apt-get update && apt-get install -y dos2unix"

# Convert post-create script to Unix line endings
docker exec -it devcontainer-app-1 bash -c "dos2unix /workspaces/ai-transcript-app/.devcontainer/post-create.sh"
```

---

### **Step 3: Download AI Models**

```powershell
# Download Ollama Gemma3:4b model (~3.3GB)
docker exec -it devcontainer-ollama-1 ollama pull gemma3:4b

# Check installed models
docker exec -it devcontainer-ollama-1 ollama list
```

**Note:** The backend automatically downloads the Whisper model (base.en, ~145MB) on first startup.

---

### **Step 4: Start Backend Server** ⭐

```powershell
docker exec -it devcontainer-app-1 bash -c "cd /workspaces/ai-transcript-app/backend && /workspaces/ai-transcript-app/backend/.venv/bin/uvicorn app:app --reload --host 0.0.0.0 --port 8000 --timeout-keep-alive 600"
```

**Backend will be available at:** http://localhost:8000

**Expected Output:**

```
INFO:     Will watch for changes in these directories: ['/workspaces/ai-transcript-app/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [306] using WatchFiles
INFO:     Started server process [313]
INFO:     Waiting for application startup.
🚀 Starting AI Transcript App...
🔄 Loading Whisper model 'base.en'...
✅ Ready!
INFO:     Application startup complete.
```

---

### **Step 5: Start Frontend Server** ⭐

**Open a new PowerShell terminal and run:**

```powershell
docker exec -it devcontainer-app-1 bash -c "cd /workspaces/ai-transcript-app/frontend && npm run dev"
```

**Frontend will be available at:** http://localhost:3000

**Expected Output:**

```
> ai-transcript-app-frontend@0.1.0 dev
> vite

  VITE v7.1.12  ready in 2821 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://172.18.0.3:3000/
  ➜  press h + enter to show help
```

---

## 🌐 Access Points

| Service                     | URL                        | Description                          |
| --------------------------- | -------------------------- | ------------------------------------ |
| **Frontend (React)**  | http://localhost:3000      | User interface for transcription     |
| **Backend (FastAPI)** | http://localhost:8000      | API server                           |
| **API Docs**          | http://localhost:8000/docs | FastAPI auto-generated documentation |
| **Ollama API**        | http://localhost:11434     | LLM inference endpoint               |

---

## 🛠️ Utility Commands

### Check Container Status

```powershell
# List running containers
docker ps

# Check logs for app container
docker logs devcontainer-app-1

# Check logs for Ollama container
docker logs devcontainer-ollama-1
```

### Stop Servers

```powershell
# Stop backend/frontend: Press Ctrl+C in their respective terminals

# Stop all containers
cd "e:\Hari Sundar\local-ai-transcript-app\.devcontainer"
docker-compose down
```

### Restart Containers

```powershell
cd "e:\Hari Sundar\local-ai-transcript-app\.devcontainer"
docker-compose restart
```

### Access Container Shell

```powershell
# Access app container bash
docker exec -it devcontainer-app-1 bash

# Access Ollama container bash
docker exec -it devcontainer-ollama-1 bash
```

### Check Python/Node Installations

```powershell
# Check Python environment
docker exec -it devcontainer-app-1 bash -c "cd /workspaces/ai-transcript-app/backend && /workspaces/ai-transcript-app/backend/.venv/bin/python --version"

# Check installed Python packages
docker exec -it devcontainer-app-1 bash -c "cd /workspaces/ai-transcript-app/backend && /workspaces/ai-transcript-app/backend/.venv/bin/pip list"

# Check Node.js version
docker exec -it devcontainer-app-1 node --version

# Check npm version
docker exec -it devcontainer-app-1 npm --version
```

---

## 📦 Installed Dependencies

### Python Dependencies (Backend)

- **faster-whisper** >= 1.2.0 - Speech-to-text transcription
- **numpy** >= 2.3.4 - Numerical computing
- **fastapi** >= 0.115.0 - Web framework
- **uvicorn[standard]** >= 0.32.0 - ASGI server
- **python-multipart** >= 0.0.9 - File upload support
- **openai** >= 1.0.0 - OpenAI-compatible API client
- **python-dotenv** >= 1.0.0 - Environment variable management

### Node.js Dependencies (Frontend)

- **react** ^19.2.0 - UI library
- **react-dom** ^19.2.0 - React DOM renderer
- **lucide-react** ^0.552.0 - Icon library
- **vite** ^7.1.12 - Build tool and dev server
- **typescript** ^5.9.3 - Type checking
- **eslint** & **prettier** - Code quality tools

### AI Models

- **Whisper base.en** (~145MB) - English speech-to-text
- **Gemma3:4b** (~3.3GB) - Language model for text cleaning

---

## 🎯 Quick Start Guide (Summary)

### For First-Time Setup:

```powershell
# 1. Start containers
cd "e:\Hari Sundar\local-ai-transcript-app\.devcontainer"
docker-compose up -d

# 2. Download Ollama model
docker exec -it devcontainer-ollama-1 ollama pull gemma3:4b

# 3. Start backend (Terminal 1)
docker exec -it devcontainer-app-1 bash -c "cd /workspaces/ai-transcript-app/backend && /workspaces/ai-transcript-app/backend/.venv/bin/uvicorn app:app --reload --host 0.0.0.0 --port 8000 --timeout-keep-alive 600"

# 4. Start frontend (Terminal 2)
docker exec -it devcontainer-app-1 bash -c "cd /workspaces/ai-transcript-app/frontend && npm run dev"

# 5. Open browser
# Navigate to: http://localhost:3000
```

### For Subsequent Runs:

```powershell
# If containers are stopped, start them:
cd "e:\Hari Sundar\local-ai-transcript-app\.devcontainer"
docker-compose up -d

# Then run steps 3 & 4 from above (start backend & frontend)
```

---

## 🔍 Troubleshooting

### Issue: Docker daemon not running

**Error:** `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`
**Solution:** Start Docker Desktop and wait for it to fully initialize

### Issue: Port already in use

**Error:** `Address already in use`
**Solution:**

```powershell
# Find process using port 8000 or 3000
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Kill the process (replace PID)
taskkill /PID <process_id> /F
```

### Issue: Container fails to start

**Solution:**

```powershell
# Remove and recreate containers
cd "e:\Hari Sundar\local-ai-transcript-app\.devcontainer"
docker-compose down
docker-compose up -d --build
```

### Issue: Models not downloading

**Solution:**

```powershell
# Check Ollama container logs
docker logs devcontainer-ollama-1

# Manually pull model again
docker exec -it devcontainer-ollama-1 ollama pull gemma3:4b
```

---

## 📝 Configuration Files Summary

### `.devcontainer/docker-compose.yml`

- Orchestrates multi-container setup
- Defines app and Ollama services
- Maps ports: 8000 (backend), 3000 (frontend), 11434 (Ollama)

### `backend/.env`

- Configures LLM API endpoint (Ollama)
- Sets Whisper model variant
- OpenAI-compatible API settings

### `.devcontainer/Dockerfile`

- Base image: Python 3.12 slim
- Installs: Python, Node.js 24, uv package manager
- System dependencies for ML packages

### `.devcontainer/post-create.sh`

- Automated setup script
- Installs Python/Node dependencies
- Downloads AI models

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Docker containers running: `docker ps`
- [ ] Backend accessible: http://localhost:8000/api/status
- [ ] Frontend accessible: http://localhost:3000
- [ ] Ollama models installed: `docker exec -it devcontainer-ollama-1 ollama list`
- [ ] Python venv exists: `backend/.venv/`
- [ ] Node modules exist: `frontend/node_modules/`

---

## 📊 System Requirements

- **OS:** Windows (with Docker Desktop)
- **RAM:** 8GB minimum, 32GB recommended for smooth AI inference
- **CPU:** 8 cores recommended
- **Storage:** 64GB free (for models and dependencies)
- **Docker Desktop:** Latest version

---

## 🎓 Architecture Overview

```
┌─────────────────────────────────────────┐
│         Browser (localhost:3000)        │
│         React + Vite Frontend           │
└────────────────┬────────────────────────┘
                 │ HTTP Requests
                 ▼
┌─────────────────────────────────────────┐
│       FastAPI Backend (port 8000)       │
│    - Audio upload/recording             │
│    - Whisper transcription              │
│    - LLM text cleaning                  │
└────────────────┬────────────────────────┘
                 │ OpenAI API calls
                 ▼
┌─────────────────────────────────────────┐
│       Ollama Server (port 11434)        │
│       Gemma3:4b Model                   │
│    - Text cleaning & enhancement        │
└─────────────────────────────────────────┘

All running in Docker containers on Windows
```

---

## 📚 Additional Resources

- **Project README:** `e:\Hari Sundar\local-ai-transcript-app\README.md`
- **Backend Code:** `e:\Hari Sundar\local-ai-transcript-app\backend\app.py`
- **Frontend Code:** `e:\Hari Sundar\local-ai-transcript-app\frontend\src\`
- **Docker Compose:** `e:\Hari Sundar\local-ai-transcript-app\.devcontainer\docker-compose.yml`

---

**Document Version:** 1.0
**Last Updated:** December 18, 2025
**Status:** ✅ Fully Operational
