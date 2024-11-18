# AI Planet Internship Assignment

This is a FastAPI application. It uses the `uvicorn` server to run the application.

## API endpoints
1. /upload : This endpoint accepts a file and stores it in the local file system.
2. /ask : This is websocket end point which recieves text (pdf_name||question) and sends answer. In between it also sends `loading` and `done` response to make sure the loader appear while the response is getting generated.

## Rate Limit
1. User/Client can open the websocket connection only twice in an hour.
2. User/Client can only send five messages for a pdf.

## Data storing
There are two models. One is `questions` which store all the questions and their answers for a particular pdf and the other one is `pdfMetadata` which stores the metadata of all the pdfs ever uploaded.

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/itsvineetkr/ai-planet-backend.git
    cd ai-planet-backend
    ```

2. **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Setting up the .env file

1. **Create a `.env` file in the root directory of your project.**

2. **Add the following environment variables to the `.env` file:**
    ```env
    HUGGINGFACEHUB_API_TOKEN = "hf_----xxxxxxx----"
    ```
    Replace `hf_----xxxxxxx----` and `<your-secret-key>` with your huggingface api key.

## Running the Application

1. **Start the FastAPI server:**
    ```bash
    uvicorn main:app --reload
    ```

    The application will be available at `http://localhost:8000/`.
