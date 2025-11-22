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

### Step 5: Set Up ML Client Worker (Optional for Local Testing)

The worker processes pending receipts. You can test it locally:

```bash
# Navigate to machine-learning-client directory
cd machine-learning-client

# Install dependencies
pipenv install
# OR
pip install -r requirements.txt

# Make sure MongoDB is running and .env is configured
# Run the worker
python worker.py
```

The worker will:

- Connect to MongoDB
- Poll for pending receipts every 5 seconds
- Process them through OCR and classification
- Update receipts with status "completed"

## Part 2: Docker Testing

### Step 1: Create .env File for Docker

Create a `.env` file in the project root (same as above):

```bash
MONGO_USER=admin
MONGO_PASS=password123
MONGO_DB_NAME=receipts_db
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

### Step 2: Build and Run with Docker Compose

```bash
# From project root
docker-compose up --build
```

This will:

- Build MongoDB container
- Build and run web-app container (port 5000)
- Build and run ml-client container (worker process)

### Step 3: Access the Application

- **Web App**: http://localhost:5000
- **MongoDB**: localhost:27017 (if you need to connect directly)

### Step 4: Test the Full Flow

1. **Sign up/Login** via the web interface
2. **Upload a receipt** at http://localhost:5000/upload
3. **Check worker logs**:

   ```bash
   docker logs ml-client -f
   ```

   You should see the worker processing the receipt.

4. **Check receipt status**:

   - Go to http://localhost:5000/history
   - The receipt should appear with status "completed" after processing

5. **View Analytics**:
   - Go to http://localhost:5000/analytics
   - Charts should show real data from your receipts

## Troubleshooting

### Web App Issues

**Port 5000 already in use:**

```bash
# Change port in app.py or use:
flask run --port 5001
```

**MongoDB connection failed:**

- Check MongoDB is running: `docker ps` (if using Docker) or check MongoDB service
- Verify MONGO_USER, MONGO_PASS, MONGO_HOST in .env match MongoDB setup
- For local MongoDB without auth: remove user/pass from connection string

**Import errors:**

- Make sure all dependencies are installed: `pip install -r requirements.txt` or `pipenv install`

### Worker Issues

**Worker not processing receipts:**

- Check worker logs: `docker logs ml-client`
- Verify MongoDB connection
- Check that OPENAI_API_KEY is set (required for OCR)
- Ensure shared volume is working (check uploads folder exists)

**File not found errors:**

- Verify shared volume is mounted correctly
- Check that web-app is saving files to `/app/uploads`
- Check file paths in database match actual file locations

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
