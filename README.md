![Lint-free](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/lint.yml/badge.svg)

# Containerized App Exercise

Build a containerized app that uses machine learning. See [instructions](./instructions.md) for details.

# Receipt Scanner & Expense Categorizer

![ML Client CI](https://github.com/swe-students-fall2025/4-containers-six-seven/actions/workflows/ml-client-ci.yml/badge.svg)
![Web App CI](https://github.com/swe-students-fall2025/4-containers-six-seven/actions/workflows/web-app-ci.yml/badge.svg)

## Project Overview
The **Receipt Scanner & Expense Categorizer** is a containerized application designed to automate expense tracking. It consists of three subsystems:
1.  **Machine Learning Client:** Captures images, performs OCR, and categorizes expenses using AI.
2.  **Web App:** A dashboard to view receipts, analytics, and spending history.
3.  **Database:** A MongoDB instance storing all data.

## Team Members 
* **Person 1 (DevOps):** [Majo Salgado](https://github.com/mariajsalgadoq)
* **Person 2 (Data/ML):** [Apoorv Belgundi](https://github.com/apoorvib)
* **Person 3 (ML Client):** [Galal Bichara](https://github.com/gkbichara)
* **Person 4 (Web Backend):** [Asim](https://github.com/asimd0)
* **Person 5 (Web Frontend):** [Anshu Aramandla](https://github.com/aa10150)

## Setup Instructions

### Prerequisites
* Python 3.10+ (for local development)
* Docker Desktop installed and running (for Docker deployment)
* OpenAI API Key (for OCR processing)

### Option 1: Local Development Setup

**Step 1: Start MongoDB**

Run MongoDB in Docker (easiest for local testing):

**PowerShell (Windows):**
```powershell
docker run -d -p 27017:27017 --name mongodb-local -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=password123 mongo:latest
```

**Bash/Linux/Mac:**
```bash
docker run -d -p 27017:27017 --name mongodb-local \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password123 \
  mongo:latest
```

**Step 2: Create Environment File**

Create a `.env` file in the **project root** (same directory as `docker-compose.yml`):

**PowerShell (Windows):**
```powershell
@"
MONGO_USER=admin
MONGO_PASS=password123
MONGO_DB_NAME=receipts_db
MONGO_HOST=localhost
SECRET_KEY=dev-secret-key-change-in-production
OPENAI_API_KEY=your-openai-api-key-here
"@ | Out-File -FilePath .env -Encoding utf8
```

**Bash/Linux/Mac:**
```bash
cat > .env << EOF
MONGO_USER=admin
MONGO_PASS=password123
MONGO_DB_NAME=receipts_db
MONGO_HOST=localhost
SECRET_KEY=dev-secret-key-change-in-production
OPENAI_API_KEY=your-openai-api-key-here
EOF
```

**Step 3: Install Dependencies and Run Web App**

```bash
# Install web app dependencies
cd web-app
pip install -r requirements.txt

# Run the Flask application
python app.py
```

The web app will start at: **http://localhost:5000**

**Step 4: Run Worker Process (Required for Processing Receipts)**

Open a **new terminal** and run:

```bash
# Install ML client dependencies
cd machine-learning-client
pip install -r requirements.txt

# Run the worker (keeps running, processes receipts)
python worker.py
```

**Important:** Keep both terminals running:
- Terminal 1: Web app (Flask server)
- Terminal 2: Worker (processes receipts)

### Option 2: Docker Deployment

**Step 1: Create Environment File**

Create a `.env` file in the **project root**:

**PowerShell (Windows):**
```powershell
@"
MONGO_USER=admin
MONGO_PASS=password123
MONGO_DB_NAME=receipts_db
MONGO_HOST=mongodb
SECRET_KEY=dev-secret-key-change-in-production
OPENAI_API_KEY=your-openai-api-key-here
"@ | Out-File -FilePath .env -Encoding utf8
```

**Bash/Linux/Mac:**
```bash
cat > .env << EOF
MONGO_USER=admin
MONGO_PASS=password123
MONGO_DB_NAME=receipts_db
MONGO_HOST=mongodb
SECRET_KEY=dev-secret-key-change-in-production
OPENAI_API_KEY=your-openai-api-key-here
EOF
```

**Note:** For Docker, `MONGO_HOST` must be `mongodb` (Docker service name), not `localhost`.

**Step 2: Run with Docker Compose**

```bash
# From project root
docker-compose up --build
```

This starts all services:
- MongoDB container
- Web app container (http://localhost:5000)
- ML client worker container (processes receipts automatically)

**Step 3: Access the Application**

- **Web Dashboard:** http://localhost:5000
- **MongoDB:** localhost:27017

### Key Differences: Local vs Docker

| Aspect | Local Development | Docker |
|--------|-------------------|--------|
| **MONGO_HOST** | `localhost` | `mongodb` |
| **Processes** | Run manually in 2 terminals | All run automatically |
| **File Storage** | `{project_root}/uploads/` | Shared Docker volume `/app/uploads` |
| **Worker** | Must run `python worker.py` manually | Runs automatically in container |

### First Time Setup Checklist

- [ ] MongoDB is running (Docker container or local install)
- [ ] `.env` file created in project root with correct values
- [ ] `MONGO_HOST=localhost` for local, `MONGO_HOST=mongodb` for Docker
- [ ] `OPENAI_API_KEY` set in `.env` (required for OCR)
- [ ] Web app dependencies installed (`pip install -r requirements.txt` in `web-app/`)
- [ ] ML client dependencies installed (`pip install -r requirements.txt` in `machine-learning-client/`)
- [ ] Web app running (local) or Docker containers started
- [ ] Worker process running (local) or Docker containers started

### Quick Start

**Local (Fastest for Development):**
```bash
# Terminal 1: Web app
cd web-app && python app.py

# Terminal 2: Worker  
cd machine-learning-client && python worker.py
```

**Docker (Production-like):**
```bash
docker-compose up --build
```

For detailed instructions and troubleshooting, see [TESTING_GUIDE.md](./TESTING_GUIDE.md).

## Technologies Used
* **Containerization:** Docker, Docker Compose
* **Database:** MongoDB
* **Backend:** Python, Flask
* **Machine Learning:** TensorFlow / PyTorch (depending on Person 3's choice), OpenCV
* **CI/CD:** GitHub Actions
* **Linting & Testing:** Pylint, Black, Pytest