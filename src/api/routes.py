import json
import os

from fastapi import APIRouter, Form, Request, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from llm.completions import ask_llm_lambda_stream
from llm.embeddings import embed_texts_remote
from services.retrieval_service import build_rag_prompt
from storage.vector.read import search_chunks
from storage.db.read import get_chunk_sources
from storage.db.auth import verify_password
from storage.db.session import get_db_session_di
from storage.db.models import User

from sqlalchemy.orm import Session
from parsing.sanitize import sanitize_prompt
from pydantic import BaseModel, constr

from utils.config import settings

from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer
from slowapi import Limiter


templates = Jinja2Templates(directory="src/api/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


# CSRF token
SECRET_KEY = settings.SECRET_KEY
csrf_serializer = URLSafeTimedSerializer(SECRET_KEY)


def generate_csrf_token():
    return csrf_serializer.dumps(os.urandom(12).hex(), salt="csrf")


def validate_csrf_token(token):
    try:
        csrf_serializer.loads(token, salt="csrf", max_age=3600)
        return True
    except Exception:
        return False


# Rate limiting
limiter = Limiter(key_func=lambda request: request.client.host)


# Auth dependency
def get_current_user_session(
    request: Request, db: Session = Depends(get_db_session_di)
):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token
    return templates.TemplateResponse(
        "login.html", {"request": request, "csrf_token": csrf_token}
    )


@limiter.limit("10/minute")
@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)


@router.post("/login", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db_session_di),
):
    if not validate_csrf_token(csrf_token) or csrf_token != request.session.get(
        "csrf_token"
    ):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid or missing CSRF token.",
                "csrf_token": generate_csrf_token(),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    user = db.query(User).filter(User.username == username).first()
    # Always generic error message
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid username or password.",
                "csrf_token": generate_csrf_token(),
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    # Login success: clear and set session, redirect to /infer
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse("/infer", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")


@router.get("/infer", response_class=HTMLResponse)
async def get_infer(request: Request):
    """
    Serve the main UI for user question input.
    """
    return templates.TemplateResponse("infer.html", {"request": request})


@router.get("/infer", response_class=HTMLResponse)
async def get_infer(request: Request, user=Depends(get_current_user_session)):
    return templates.TemplateResponse("infer.html", {"request": request, "user": user})


@router.get("/infer_stream")
@limiter.limit("5/minute")
async def infer_stream(
    request: Request,
    prompt: str = Query(..., min_length=5, max_length=512),
    db: Session = Depends(get_db_session_di),
    user=Depends(get_current_user_session),
):
    """
    SSE endpoint: streams the answer and references chunk by chunk as they arrive.
    The prompt is passed as a query parameter for EventSource compatibility.
    """
    prompt = sanitize_prompt(prompt)
    if not prompt or len(prompt) < 5:
        raise HTTPException(status_code=400, detail="Prompt is invalid or too short.")

    user_query = prompt.strip()
    query_embedding = embed_texts_remote([user_query])[0]
    retrieved_chunks = search_chunks(query_embedding, limit=5)
    chunk_ids = [chunk["id"] for chunk in retrieved_chunks if "id" in chunk]
    # Lookup doc names from Postgres
    chunk_id_to_doc = get_chunk_sources(chunk_ids) if chunk_ids else {}

    # Add doc name to each chunk
    for chunk in retrieved_chunks:
        chunk["source"] = chunk_id_to_doc.get(chunk.get("id"), "?")

    rag_prompt, references = build_rag_prompt(user_query, retrieved_chunks)

    def event_stream():
        answer_buffer = ""
        for chunk in ask_llm_lambda_stream(rag_prompt):
            # Stream each answer chunk as it is generated
            answer_buffer += chunk
            event = f"data: {json.dumps({'answer': answer_buffer, 'references': references})}\n\n"

            yield event

    return StreamingResponse(event_stream(), media_type="text/event-stream")
