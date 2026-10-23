
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google import genai

from backend.image_processing import optimize_image
from backend.playlist_generator import generate_playlist

app = FastAPI(
    title="Photo Playlist Generator API",
    description="Python backend for the Photo Playlist Generator application.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Photo Playlist Generator API",
        "version": "0.1.0",
    }

@app.post("/api/playlists/generate")
async def generate_playlist_endpoint(
    photo: UploadFile = File(...),
    keywords: str = Form(""),
    length_mode: str = Form("# of Songs"),
    length_value: int = Form(10),
):
    # Validate the playlist settings.
    if length_mode == "# of Songs":
        if not 5 <= length_value <= 50:
            raise HTTPException(
                status_code=400,
                detail="Song count must be between 5 and 50.",
            )
    elif length_mode == "Duration":
        if not 30 <= length_value <= 180:
            raise HTTPException(
                status_code=400,
                detail="Duration must be between 30 and 180 minutes.",
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid playlist length mode.",
        )

    # Read and optimize the uploaded photograph.
    try:
        image_bytes = optimize_image(await photo.read())
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to process the uploaded photograph.",
        )

    # Load the intended Gemini API key.
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key is not configured.",
        )

    # Explicitly select our Gemini key.
    os.environ.pop("GOOGLE_API_KEY", None)
    client = genai.Client(api_key=api_key)

    # Generate the playlist using our existing backend.
    try:
        result = generate_playlist(
            client=client,
            image_bytes=image_bytes,
            keywords=keywords,
            length_mode=length_mode,
            length_value=length_value,
        )
        return result
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Playlist generation failed.",
        )
