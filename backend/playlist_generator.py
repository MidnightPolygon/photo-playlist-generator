
"""Generate photo-inspired playlists using Google Gemini."""

from google.genai import types

from backend.playlist_engine import (
    PLAYLIST_SCHEMA,
    calculate_duration,
    correct_playlist_duration,
    within_tolerance,
)


GEMINI_MODEL = "gemini-3.5-flash-lite"


def generate_playlist(
    client,
    image_bytes,
    keywords,
    length_mode,
    length_value,
):
    """Generate a playlist from an optimized JPEG and user preferences."""

    if length_mode == "# of Songs":
        length_instruction = f"""
            Create a playlist containing exactly {length_value} songs.
        """

    elif length_mode == "Duration":
        estimated_tracks = round(length_value / 4.5)

        length_instruction = f"""
            Create a playlist targeting {length_value} minutes.

            Begin with approximately {estimated_tracks} songs,
            adjusting the number based on their actual durations.

            The combined duration of all recommended songs should
            be within 5% of {length_value} minutes.

            IMPORTANT:
            - Calculate the sum of all duration_seconds values.
            - Add songs if the total is too short.
            - Remove songs if the total is too long.
            - Do not invent or alter recording durations.
            - Maintain musical cohesion and natural transitions.
        """
    else:
        raise ValueError("Invalid playlist length mode.")

    prompt = f"""
        You are an expert music curator creating a personalized
        playlist inspired by a photograph.

        Analyze the uploaded photograph, including its setting,
        colors, subjects, emotional atmosphere, and visual storytelling.

        The user describes the desired mood as:
        {keywords}

        {length_instruction}

        Requirements:
        - Prioritize how the music actually sounds over lyrical themes
        or similarities between song titles and objects in the photograph.
        - Consider instrumentation, tempo, rhythm, energy, production,
        and emotional atmosphere when selecting songs.
        - Do not recommend a song simply because its title contains
        words associated with the photograph.
        - Treat the user's mood keywords as important creative direction.
        - Choose songs that sound cohesive when played consecutively.
        - Build a musical journey with intentional transitions in
        energy and mood.
        - Avoid obvious novelty selections or overly literal associations.
        - Ensure each explanation accurately describes the recording.
        - Include the approximate duration of each recommended song.
        - Express each song's duration in seconds using the
        duration_seconds field.
        - Use the standard studio recording unless the user
        specifically requests a different version.

        Format your response as:

        ## Your Photo Playlist

        **The Vibe:** A short, evocative description of the
        musical atmosphere inspired by the photograph.

        Then provide a numbered list:

        1. **Song Title** — Artist
        *Why it fits:* Brief explanation.

        Finish with a short description of the playlist's
        musical journey.
    """

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg",
            ),
            prompt,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PLAYLIST_SCHEMA,
        ),
    )

    playlist = response.parsed

    if not playlist or not playlist.get("songs"):
        raise ValueError("Gemini did not return a valid playlist.")

    diagnostics = []
    correction_attempts = 0
    initial_seconds = calculate_duration(playlist["songs"])

    if length_mode == "Duration":
        target_seconds = length_value * 60

        playlist, initial_seconds, correction_attempts = (
            correct_playlist_duration(
                client,
                playlist,
                target_seconds,
                diagnostics=diagnostics,
            )
        )

    final_seconds = calculate_duration(playlist["songs"])

    result = {
        "playlist": playlist,
        "total_duration_seconds": final_seconds,
        "duration_correction_attempts": correction_attempts,
        "duration_diagnostics": diagnostics,
    }

    if length_mode == "Duration":
        result["duration_within_tolerance"] = within_tolerance(
            final_seconds,
            length_value * 60,
        )
        result["initial_duration_seconds"] = initial_seconds

    return result
