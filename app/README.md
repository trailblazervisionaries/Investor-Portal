## This project contains all the route and their backend logic for the Investment Portal

For architecture details, see [ARCHITECTURE.md](./ARCHITECTURE.md).

# Project Setup Guide

This guide outlines the steps to set up and run the Investment Portal project built with FastAPI and Uvicorn, PostgresSQL. The project uses Python >= 3.11.8 version and includes a virtual environment setup, dependency installation, and environment configuration.

## Prerequisites
- **Python >= 3.11.8**: Ensure Python 3.11.8 is installed on your system. You can download it from [python.org](https://www.python.org/downloads/).
- **pip**: Ensure `pip` is installed and up-to-date (`pip install --upgrade pip`).

- **Redis is required for Celery to process background tasks. Follow these steps to install Redis on macOS/Linux.**

    #### On macOS:

    `brew install redis`

    #### On Linux (Ubuntu/Debian):

    `sudo apt-get update`
    `sudo apt-get install redis-server`


## Setup Instructions

### Step-1. Clone the Repository
Clone the project repository to your local machine:
```bash
git clone <repository-url>
cd <project-directory>
```


### Step-2. Create and Activate a Virtual Environment
Set up a virtual environment to isolate project dependencies.

#### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

After activation, your terminal should show `(venv)` indicating the virtual environment is active.

### Step-3. Install Dependencies
Install the required dependencies listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

#### Example `requirements.txt`:
```
fastapi==0.121.2
uvicorn==0.38.0
python-dotenv==1.2.1
```

### Step-4. Create a `.env` File
Create a `.env` file in the project root directory to store environment variables (e.g., API keys, database URLs, or configuration settings).

#### Steps:
i. Create a file named `.env` in the project root.
ii. Add environment variables in the format `KEY=VALUE`.
   
# .env
## Add key value pairs to your .env file
    ```From .env.example ``` file and add you value in keys.

**Note**: Do not commit the `.env` file to version control. Ensure it is listed in `.gitignore`.


### Step-5. Configure DOMAIN for Local Development

If running the application on localhost, update the DOMAIN variable in the .env file:
Open the .env file in the project root.

Comment out the production DOMAIN and uncomment the localhost DOMAIN:

# DOMAIN='xyzexample.com'
DOMAIN='localhost'

Save the file before running the application.

### Step-6. Starting celery-worker to performs all background tasks

**Note**: Before running celery_worker command please recheck venv should activated your current terminal.
#### On macOS/Linux:
```bash
source venv/bin/activate
```
#### On Windows:
```bash
venv\Scripts\activate
```

### command to run the celery_worker
```bash
python -m app.backgroundTask.celery_worker
```


### Step-7. Run the FastAPI Application
Before run the server your venv (virtual environment) must be activated. if not active then activate first
Start the Uvicorn server to run the FastAPI application.

#### Command:
```bash
uvicorn app.main:app --reload
```

- `main:app`: FastAPI app is defined in a file named `main.py` with a variable `app`.
- `--reload`: Enables auto-reload for development (optional).



### Step-8. Access the Application
Once the server is running, access the application at:
- **API**: `http://localhost:8000`
- **Interactive Docs**: `http://localhost:8000/docs` (FastAPI's Swagger UI)


### Step-9. To verify the backend is working for the request and response
- **Hit the Health route the url is**: `http://localhost:8000/health`


## Troubleshooting
- **Port already in use**: Change the port by modifying the `--port` flag (e.g., `--port 8001`).
- **Dependencies not found**: Ensure the virtual environment is activated and `requirements.txt` is correctly installed.
- **Python version mismatch**: Verify Python 3.11.8 is used (`python --version`).

## Deactivating the Virtual Environment
To exit the virtual environment:
```bash
deactivate 
```











