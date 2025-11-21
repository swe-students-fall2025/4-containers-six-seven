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
* **Person 1 (DevOps):** [Anshu Armandala](https://github.com/aa10150)
* **Person 2 (Data/ML):** [Apoorv Belgundi](https://github.com/apoorvib)
* **Person 3 (ML Client):** [Galal Bichara](https://github.com/gkbichara)
* **Person 4 (Web Backend):** [Asim](https://github.com/asimd0)
* **Person 5 (Web Frontend):** [Majo Salgado](https://github.com/mariajsalgadoq)

## Technologies Used
* **Containerization:** Docker, Docker Compose
* **Database:** MongoDB
* **Backend:** Python, Flask
* **Machine Learning:** TensorFlow / PyTorch (depending on Person 3's choice), OpenCV
* **CI/CD:** GitHub Actions
* **Linting & Testing:** Pylint, Black, Pytest

## Setup Instructions

### Prerequisites
* Docker Desktop installed and running.

### Installation
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/swe-students-fall2025/4-containers-six-seven.git](https://github.com/swe-students-fall2025/4-containers-six-seven.git)
    cd 4-containers-six-seven
    ```  

2.  **Set up Environment Variables:**
    Copy the example file to create your local secrets file.
    ```bash
    cp .env.example .env
    ```
    *Open `.env` and fill in your `MONGO_USER` and `MONGO_PASS` (e.g., admin/password123).*

3.  **Run the Application:**
    Start all containers (Database, ML Client, Web App) with one command:
    ```bash
    docker compose up --build
    ```

4.  **Access the App:**
    * Web Dashboard: [http://localhost:5000](http://localhost:5000)
    * MongoDB: `localhost:27017`

