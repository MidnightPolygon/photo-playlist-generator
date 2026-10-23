
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from backend.image_processing import optimize_image
from backend.playlist_generator import generate_playlist


def main():
    load_dotenv()

    # Prevent the SDK from selecting the unrelated Windows API key.
    os.environ.pop("GOOGLE_API_KEY", None)

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    photo_path = Path("test_photo.jpg")

    if not photo_path.is_file():
        raise FileNotFoundError(
            "Place test_photo.jpg in the project root folder."
        )

    image_bytes = optimize_image(photo_path.read_bytes())

    print("Generating playlist with Gemini...", flush=True)

    result = generate_playlist(
        client=client,
        image_bytes=image_bytes,
        keywords="relaxed, atmospheric, thoughtful",
        length_mode="Duration",
        length_value=60,
    )

    playlist = result["playlist"]

    print("\nPlaylist:", playlist["playlist_title"])
    print("Vibe:", playlist["vibe"])

    for index, song in enumerate(playlist["songs"], start=1):
        print(f"{index}. {song['title']} - {song['artist']}")

    minutes, seconds = divmod(
        result["total_duration_seconds"], 60
    )
    print("\nDuration correction attempts:",
      result["duration_correction_attempts"])

    print("Within tolerance:",
        result.get("duration_within_tolerance"))

    print("Duration diagnostics:",
        result["duration_diagnostics"])
    
    print(f"\nTotal duration: {minutes}m {seconds}s")
    print("Generation completed successfully!")


if __name__ == "__main__":
    main()
