# Testing Guide - Receipt Scanner Application

This guide explains how to run and test the application locally first, then with Docker.

## Prerequisites

- Python 3.10+
- MongoDB (local installation or Docker)
- pip or pipenv
- Node.js (optional, for any frontend tooling)

## Part 1: Local Testing (Web App First)

### Step 1: Set Up MongoDB Locally

**Option A: Install MongoDB locally**

- Download and install MongoDB from https://www.mongodb.com/try/download/community
- Start MongoDB service: `mongod` (or use Windows service)

**Option B: Run MongoDB in Docker (Easiest)**

**For PowerShell (Windows):**

```powershell
docker run -d -p 27017:27017 --name mongodb-local -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=password123 mongo:latest
```

**For Bash/Linux/Mac:**

```bash
docker run -d -p 27017:27017 --name mongodb-local \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password123 \
  mongo:latest
```

### Step 2: Create Environment File

Create a `.env` file in the project root:

```bash
# MongoDB Configuration
MONGO_USER=admin
MONGO_PASS=password123
MONGO_DB_NAME=receipts_db
MONGO_HOST=localhost  # Use "localhost" for local testing, "mongodb" for Docker

# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production

# OpenAI API Key (for OCR processing)
OPENAI_API_KEY=your-openai-api-key-here
```

### Step 3: Set Up Web App

```bash
# Navigate to web-app directory
cd web-app

# Install dependencies (using pipenv)
pipenv install

# OR using pip
pip install -r requirements.txt

# Create uploads directory
mkdir -p uploads

# Run the Flask app
pipenv run flask run
# OR
python app.py
# OR
flask run
```

The web app should start at: **http://localhost:5000**

### Step 4: Test Web App Endpoints

1. **Sign Up** (create a test user):

   ```bash
   curl -X POST http://localhost:5000/api/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","email":"test@example.com","password":"test123"}'
   ```

2. **Login**:

   ```bash
   curl -X POST http://localhost:5000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test123"}'
   ```

   Save the session cookie for authenticated requests.

3. **Upload a Receipt** (use Postman or browser with login session):
   - Go to http://localhost:5000/upload
   - Upload a receipt image
   - Check that it returns `{"receipt_id": "...", "status": "pending"}`

### Step 5: Set Up ML Client Worker (REQUIRED for Processing Receipts)

**IMPORTANT:** The worker must be running for receipts to be processed. Without it, receipts will stay in "pending" status forever.

The worker processes pending receipts. You can test it locally:

```bash
# Open a NEW terminal/PowerShell window (keep web app running in first terminal)

# Navigate to machine-learning-client directory
cd machine-learning-client

# Install dependencies
pipenv install
# OR
pip install -r requirements.txt

# Make sure MongoDB is running and .env is configured in project root
# The worker will read .env from project root automatically

# Run the worker
python worker.py
```

The worker will:

- Connect to MongoDB (using same .env file)
- Poll for pending receipts every 5 seconds
- Process them through OCR and classification
- Update receipts with status "completed"

**Keep both terminals running:**

- **Terminal 1:** Web app (`cd web-app && python app.py`)
- **Terminal 2:** Worker (`cd machine-learning-client && python worker.py`)

**Note:** The worker requires `OPENAI_API_KEY` in your `.env` file to process receipts. Without it, OCR processing will fail.

## Part 2: Docker Testing

### Step 1: Create .env File for Docker

**IMPORTANT:** For Docker, you need to change `MONGO_HOST` from `localhost` to `mongodb` (the Docker service name).

Create a `.env` file in the project root:

```bash
MONGO_USER=admin
MONGO_PASS=password123
MONGO_DB_NAME=receipts_db
MONGO_HOST=mongodb  # MUST be "mongodb" for Docker (not "localhost")
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

**Key Difference:**

- **Local testing:** `MONGO_HOST=localhost`
- **Docker:** `MONGO_HOST=mongodb` (Docker service name)

### Step 2: Build and Run with Docker Compose

```bash
# From project root
docker-compose up --build
```

This will:

- Build MongoDB container
- Build and run web-app container (port 5000)
- Build and run ml-client container (worker process)
- Create shared volume `receipt-uploads` for file access between containers

### Step 3: Access the Application

- **Web App**: http://localhost:5000
- **MongoDB**: localhost:27017 (if you need to connect directly)

### Step 4: Verify Everything is Running

```bash
# Check all containers are running
docker ps

# Should show:
# - mongodb (database)
# - web-app (Flask application)
# - ml-client (worker process)
```

### Step 5: View Logs

```bash
# Web app logs
docker logs web-app -f

# Worker logs (to see receipt processing)
docker logs ml-client -f

# MongoDB logs
docker logs mongodb -f

# All logs together
docker-compose logs -f
```

### Step 4: Test the Full Flow

1. **Sign up/Login** via the web interface

   - Go to http://localhost:5000
   - Click "Sign Up" to create an account
   - Or click "Login" if you already have an account

2. **Upload a receipt** at http://localhost:5000/upload

   - Upload an image file (JPG, PNG, etc.)
   - The receipt will initially show status "pending"
   - The worker will process it automatically (check logs)

3. **Check worker logs**:

   ```bash
   docker logs ml-client -f
   ```

   You should see:

   - "Polling for pending receipts..."
   - "Processing receipt: {receipt_id}"
   - "Receipt processed successfully"

4. **Check receipt status**:

   - Go to http://localhost:5000/history
   - The receipt should appear with status "completed" after processing (usually within 10-30 seconds)
   - You should see extracted data: merchant, total, category, date

5. **View Analytics**:

   - Go to http://localhost:5000/analytics
   - Charts should show real data from your receipts
   - Spending by category, monthly trends, etc.

6. **Test Category Filtering**:
   - Go to http://localhost:5000/history
   - Use the category dropdown to filter receipts
   - Only receipts matching the selected category should appear

## Key Differences: Local vs Docker

### Environment Variables

| Variable     | Local Testing                  | Docker                             |
| ------------ | ------------------------------ | ---------------------------------- |
| `MONGO_HOST` | `localhost`                    | `mongodb`                          |
| `MONGO_USER` | `admin`                        | `admin`                            |
| `MONGO_PASS` | `password123`                  | `password123`                      |
| File Paths   | Absolute paths in project root | `/app/uploads` (inside containers) |

### File Storage

**Local Testing:**

- Files saved to: `{project_root}/uploads/` (absolute path from project root)
- Worker looks in: `{project_root}/uploads/` (resolves relative to project root)
- Both web-app and worker run on your machine, can access same files
- Paths are stored as absolute paths in the database
- Worker automatically resolves paths relative to project root if needed

**Docker:**

- Files saved to: `/app/uploads` inside web-app container
- Worker accesses: `/app/uploads` inside ml-client container
- Shared via Docker volume `receipt-uploads`
- Both containers mount the same volume at `/app/uploads`
- Paths stored in database are `/app/uploads/{filename}`
- Both containers see the same files through the shared volume

**Important Notes:**

- The web app saves files with absolute paths (relative to project root)
- The worker automatically resolves paths to find files
- In Docker, the shared volume ensures both containers see the same files
- If you see "Image file not found" errors, check:
  - **Local:** Files exist in `{project_root}/uploads/`
  - **Docker:** Volume is mounted correctly (`docker volume inspect receipt-uploads`)

### Running Processes

**Local Testing:**

- **Terminal 1:** Flask web app (`cd web-app && python app.py`)
- **Terminal 2:** Worker process (`cd machine-learning-client && python worker.py`)
- Both processes run separately on your machine

**Docker:**

- All processes run automatically in containers
- Worker runs continuously in `ml-client` container
- Web app runs in `web-app` container
- No manual process management needed

### Database Connection

**Local Testing:**

- Web app connects to: `mongodb://admin:password123@localhost:27017/`
- Worker connects to: `mongodb://admin:password123@localhost:27017/`
- Both connect to MongoDB running on your machine (Docker or local install)

**Docker:**

- Web app connects to: `mongodb://admin:password123@mongodb:27017/`
- Worker connects to: `mongodb://admin:password123@mongodb:27017/`
- Both connect to MongoDB container using service name `mongodb`

### Switching Between Local and Docker

**To switch from Local to Docker:**

1. Stop local processes (Ctrl+C in terminals)
2. Update `.env`: Change `MONGO_HOST=localhost` to `MONGO_HOST=mongodb`
3. Run `docker-compose up --build`

**To switch from Docker to Local:**

1. Stop Docker: `docker-compose down`
2. Update `.env`: Change `MONGO_HOST=mongodb` to `MONGO_HOST=localhost`
3. Start MongoDB locally (if not using Docker for MongoDB)
4. Run web app and worker manually

## Troubleshooting

### Web App Issues

**Port 5000 already in use:**

```bash
# Change port in app.py or use:
flask run --port 5001
```

**MongoDB connection failed:**

- **Error: `getaddrinfo failed` or `mongodb:27017` not found:**
  - **Local testing:** Make sure `MONGO_HOST=localhost` in `.env`
  - **Docker:** Make sure `MONGO_HOST=mongodb` in `.env`
  - The application uses `MONGO_HOST` to determine where to connect
  - Check `.env` file is in project root (same directory as `docker-compose.yml`)
- **Error: Authentication failed:**

  - Verify `MONGO_USER` and `MONGO_PASS` in `.env` match MongoDB credentials
  - For local MongoDB Docker: Use `admin`/`password123` (as set in docker run command)
  - The application will try connecting without auth if authenticated connection fails (local MongoDB without auth)

- **Connection timeout:**

  - Check MongoDB is running: `docker ps` (if using Docker) or check MongoDB service
  - Verify MongoDB is accessible: `telnet localhost 27017` or `nc -zv localhost 27017`
  - For Docker MongoDB: Check container logs: `docker logs mongodb-local` or `docker logs mongodb`

- **For local MongoDB without auth:**
  - The application will automatically try connecting without credentials if auth fails
  - You can leave `MONGO_USER` and `MONGO_PASS` empty or remove them from `.env`

**Import errors:**

- Make sure all dependencies are installed: `pip install -r requirements.txt` or `pipenv install`

### Worker Issues

**Worker not processing receipts:**

- Check worker logs: `docker logs ml-client`
- Verify MongoDB connection
- Check that OPENAI_API_KEY is set (required for OCR)
- Ensure shared volume is working (check uploads folder exists)

**File not found errors:**

- **Local:** Check files are in `{project_root}/uploads/` or `{project_root}/web-app/uploads/`
- **Docker:** Verify shared volume is mounted correctly: `docker volume inspect receipt-uploads`
- Check that web-app is saving files to `/app/uploads` (check logs for debug output)
- Check file paths in database match actual file locations
- **Local:** Worker tries multiple path locations automatically
- **Docker:** Both containers should mount volume at `/app/uploads`

### Docker Issues

**Containers won't start:**

```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

**Volume issues:**

- Verify `receipt-uploads` volume is created: `docker volume ls`
- Check volume mount paths in docker-compose.yml

## Quick Start Commands

### Local Web App (Fastest Test)

**For PowerShell (Windows):**

```powershell
# 1. Start MongoDB (Docker)
docker run -d -p 27017:27017 --name mongodb-local -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=password123 mongo:latest

# 2. Create .env file in project root
@"
MONGO_USER=admin
MONGO_PASS=password123
MONGO_DB_NAME=receipts_db
MONGO_HOST=localhost
SECRET_KEY=dev-secret-key
OPENAI_API_KEY=your-key-here
"@ | Out-File -FilePath .env -Encoding utf8

# 3. Run web app
cd web-app
pip install -r requirements.txt
New-Item -ItemType Directory -Force -Path uploads
python app.py
# Visit http://localhost:5000
```

**For Bash/Linux/Mac:**

```bash
# 1. Start MongoDB (Docker)
docker run -d -p 27017:27017 --name mongodb-local \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password123 \
  mongo:latest

# 2. Create .env file in project root
cat > .env << EOF
MONGO_USER=admin
MONGO_PASS=password123
MONGO_DB_NAME=receipts_db
MONGO_HOST=localhost
SECRET_KEY=dev-secret-key
OPENAI_API_KEY=your-key-here
EOF

# 3. Run web app
cd web-app
pip install -r requirements.txt
mkdir -p uploads
python app.py
# Visit http://localhost:5000
```

### Full Docker Setup

```bash
# 1. Create .env file (same as above)
# 2. Run everything
docker-compose up --build
# Visit http://localhost:5000
```

## Quick Test Checklist

- [ ] MongoDB is running
- [ ] .env file is configured
- [ ] Web app starts without errors
- [ ] Can sign up a new user
- [ ] Can login
- [ ] Can upload a receipt image
- [ ] Receipt shows as "pending" initially
- [ ] Worker processes the receipt (check logs)
- [ ] Receipt status changes to "completed"
- [ ] Receipt appears in history page
- [ ] Analytics page shows data
- [ ] Category filtering works in history

## Testing with Sample Receipts

You can use the test receipts in `machine-learning-client/test-data/`:

- Copy them to the uploads folder or upload via the web interface
- Make sure they're accessible to the worker process

## Next Steps

Once local testing works:

1. Test all API endpoints
2. Test error handling (invalid files, network issues, etc.)
3. Test with multiple users
4. Test concurrent uploads
5. Verify analytics calculations are correct
