from fastapi import (
    FastAPI,
    Request,
    File,
    HTTPException,
    Depends,
    Form,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pathlib import Path
import uvicorn
import shutil
from time import time

from database import SessionLocal
from crud import *
from utils import *


app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


websocket_limit = {}


async def websocket_rate_limiter(client_id: str):
    REQUEST_LIMIT = 2
    TIME_WINDOW = 3600  # 60 mins
    current_time = time()
    request_log = websocket_limit.get(client_id, [])
    # Checking for the no. of requests done in the last time window
    # Then usko check karwayenge ki kya usne limit exceed kar di hai ya nahi that is REQUEST_LIMIT

    request_log = [t for t in request_log if current_time - t < TIME_WINDOW]
    websocket_limit[client_id] = request_log

    if len(request_log) >= REQUEST_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Isko baad me append karne ka reason is to not include this request in the request_log
    # as we won't give connection instead we will raise exception.
    websocket_limit[client_id].append(current_time)


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    return templates.TemplateResponse("homepage.html", {"request": request})


@app.post("/upload", response_class=HTMLResponse)
async def upload_pdf(
    request: Request, db: Session = Depends(get_db), pdf: UploadFile = File(...)
):
    pdf_path = UPLOADS_DIR / "pdfs" / pdf.filename
    with pdf_path.open("wb") as buffer:
        shutil.copyfileobj(pdf.file, buffer)

    add_pdf(db, pdf_name=pdf.filename)
    await make_vec_db(pdf_path=pdf_path, pdf_name=pdf_path.name)

    context = {
        "request": request,
        "pdf_path": pdf_path,
        "pdf_name": pdf.filename,
        "pdf_uploaded": True,
    }

    return templates.TemplateResponse("ask.html", context)


@app.get("/ask_page", response_class=HTMLResponse)
async def get_ask_page(request: Request):
    return templates.TemplateResponse("ask.html", {"request": request})


@app.websocket("/ask")
async def ask_question(websocket: WebSocket):
    await websocket.accept()
    client_id = websocket.client.host
    try:
        await websocket_rate_limiter(client_id)
    except HTTPException as e:
        # Sending policy violation code to notify user about rate limit exceeded and close connection
        await websocket.close(code=1008)
        return

    try:
        message_count = 0
        while True:
            data = await websocket.receive_text()
            pdf_name, question = data.split("||")
            response = await generate_response(pdf_name, question)
            await websocket.send_text("done")
            await websocket.send_text(response)
            message_count += 1
            if message_count >= 5:
                await websocket.close(code=1008)
                break
    except:
        await websocket.close()
