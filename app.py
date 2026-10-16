import os
import streamlit as st
from google import genai
from google.genai import types
from playlist_slider import playlist_slider
from urllib.parse import quote
from PIL import Image, ImageOps
from io import BytesIO

# Shared Gemini response schemas
SONG_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "artist": {"type": "STRING"},
        "reason": {"type": "STRING"},
        "duration_seconds": {"type": "INTEGER"},
    },
    "required": ["title", "artist", "reason", "duration_seconds"],
}

PLAYLIST_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "playlist_title": {"type": "STRING"},
        "vibe": {"type": "STRING"},
        "songs": {"type": "ARRAY", "items": SONG_SCHEMA},
        "musical_journey": {"type": "STRING"},
    },
    "required": ["playlist_title", "vibe", "songs", "musical_journey"],
}

ADDITIONS_SCHEMA = {
    "type": "OBJECT",
    "properties": {"songs": {"type": "ARRAY", "items": SONG_SCHEMA}},
    "required": ["songs"],
}

DURATION_TOLERANCE = 0.05
MAX_ADDITION_ATTEMPTS = 2


def calculate_duration(songs):
    return sum(max(0, int(song.get("duration_seconds") or 0)) for song in songs)


def track_key(song):
    return (song["title"].strip().casefold(), song["artist"].strip().casefold())


def within_tolerance(seconds, target_seconds):
    return abs(seconds - target_seconds) <= target_seconds * DURATION_TOLERANCE


def remove_excess_tracks(songs, target_seconds):
    """Remove tracks only when doing so improves the total-duration error."""
    songs = list(songs)
    while songs and calculate_duration(songs) > target_seconds * (1 + DURATION_TOLERANCE):
        current = calculate_duration(songs)
        best_index = min(
            range(len(songs)),
            key=lambda i: abs(current - int(songs[i]["duration_seconds"]) - target_seconds),
        )
        reduced = current - int(songs[best_index]["duration_seconds"])
        if abs(reduced - target_seconds) >= abs(current - target_seconds):
            break
        songs.pop(best_index)
    return songs


def add_best_candidates(existing, candidates, target_seconds):
    """Accept candidate tracks only when each addition improves duration accuracy."""
    songs = list(existing)
    used = {track_key(song) for song in songs}
    available = [
        song for song in candidates
        if isinstance(song, dict)
        and all(field in song for field in ("title", "artist", "reason", "duration_seconds"))
        and isinstance(song["duration_seconds"], int)
        and song["duration_seconds"] > 0
        and track_key(song) not in used
    ]
    while available:
        current = calculate_duration(songs)
        best = min(
            available,
            key=lambda song: abs(current + song["duration_seconds"] - target_seconds),
        )
        if abs(current + best["duration_seconds"] - target_seconds) >= abs(current - target_seconds):
            break
        songs.append(best)
        used.add(track_key(best))
        available = [song for song in available if track_key(song) not in used]
        if within_tolerance(calculate_duration(songs), target_seconds):
            break
    return songs


def correct_playlist_duration(client, playlist, target_seconds):
    """Keep the original playlist and make at most two targeted Gemini requests."""

    playlist = dict(playlist)
    playlist["songs"] = list(playlist["songs"])

    initial_seconds = calculate_duration(playlist["songs"])
    attempts = 0

    # Record initial generation
    log_duration_event(
        "Initial generation",
        playlist["songs"],
        target_seconds
    )

    # If already within tolerance, no correction is needed
    if within_tolerance(initial_seconds, target_seconds):
        log_duration_event(
            "Final result",
            playlist["songs"],
            target_seconds,
            correction_attempts=0
        )
        return playlist, initial_seconds, attempts

    # Remove excess tracks only if playlist is too long
    if initial_seconds > target_seconds:
        playlist["songs"] = remove_excess_tracks(
            playlist["songs"], target_seconds
        )

        log_duration_event(
            "Excess removal",
            playlist["songs"],
            target_seconds
        )

    # Request up to two targeted additions
    for _ in range(MAX_ADDITION_ATTEMPTS):

        actual = calculate_duration(playlist["songs"])

        if within_tolerance(actual, target_seconds) or actual >= target_seconds:
            break

        remaining = target_seconds - actual

        approximate_count = max(
            2,
            min(12, round(remaining / 270) + 2)
        )

        existing = "\n".join(
            f'- {song["title"]} — {song["artist"]}'
            for song in playlist["songs"]
        )

        addition_prompt = f"""
        You are extending an existing photograph-inspired music playlist.

        Playlist vibe: {playlist['vibe']}
        Musical journey: {playlist['musical_journey']}

        Existing songs (do not repeat any of these):
        {existing}

        Current duration: {actual} seconds.
        Target duration: {target_seconds} seconds.
        Remaining gap: {remaining} seconds.

        Recommend approximately {approximate_count} ADDITIONAL real, distinct songs
        with realistic standard studio recording durations in duration_seconds.

        Return ONLY new songs.
        Keep the existing atmosphere and musical cohesion.
        Do not alter durations to fit the target.
        Provide a brief reason for each.
        """

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[addition_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ADDITIONS_SCHEMA,
            ),
        )

        attempts += 1

        parsed = response.parsed or {}
        candidates = parsed.get("songs", [])

        # Count songs before adding candidates
        songs_before = len(playlist["songs"])

        # Add suitable candidates
        playlist["songs"] = add_best_candidates(
            playlist["songs"],
            candidates,
            target_seconds
        )

        # Record correction results
        log_duration_event(
            f"Correction {attempts}",
            playlist["songs"],
            target_seconds,
            songs_requested=approximate_count,
            songs_returned=len(candidates),
            songs_accepted=len(playlist["songs"]) - songs_before
        )

    # IMPORTANT: This section is OUTSIDE the for loop

    log_duration_event(
        "Final result",
        playlist["songs"],
        target_seconds,
        correction_attempts=attempts
    )

    return playlist, initial_seconds, attempts

if "generated_playlist" not in st.session_state:
    st.session_state.generated_playlist = None

# Store duration correction diagnostics
if "duration_debug" not in st.session_state:
    st.session_state.duration_debug = []

def log_duration_event(stage, songs, target_seconds, **details):
    """Record playlist duration and correction diagnostics."""

    actual_seconds = sum(
        int(song.get("duration_seconds") or 0)
        for song in songs
    )

    difference_seconds = actual_seconds - target_seconds

    event = {
        "stage": stage,
        "song_count": len(songs),
        "actual_seconds": actual_seconds,
        "target_seconds": target_seconds,
        "difference_seconds": difference_seconds,
        "difference_percent": round(
            difference_seconds / target_seconds * 100, 2
        ),
        **details
    }

    st.session_state.duration_debug.append(event)
    print(
    f"DEBUG LOG: {stage} | "
    f"Events recorded: {len(st.session_state.duration_debug)}"
)

def optimize_image(uploaded_file, max_dimension=1024, quality=85):
    """Resize and compress an image for Gemini analysis."""

    image = Image.open(uploaded_file)

    # Correct orientation using EXIF metadata
    image = ImageOps.exif_transpose(image)

    # Convert to RGB for JPEG compatibility
    image = image.convert("RGB")

    # Resize while preserving aspect ratio
    image.thumbnail(
        (max_dimension, max_dimension),
        Image.Resampling.LANCZOS
    )

    # Compress image into memory
    buffer = BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=quality,
        optimize=True
    )

    return buffer.getvalue()

st.set_page_config(
    page_title="Photo Playlist",
    page_icon="🎵",
    layout="centered"
)

st.title("🎵 Photo Playlist")
st.write("Turn your favorite photographs into personalized music playlists.")

uploaded_photo = st.file_uploader(
    "Upload a photograph",
    type=["jpg", "jpeg", "png", "webp"]
)

keywords = st.text_input(
    "Describe the mood in a few words",
    placeholder="Nostalgic, peaceful, adventurous..."
)

# Playlist length settings
MIN_SONGS = 5
MAX_SONGS = 50
DEFAULT_SONGS = 10

MIN_DURATION = 30
MAX_DURATION = 180
DEFAULT_DURATION = 60

# Choose how playlist length is measured
length_mode = st.selectbox(
    "Length of playlist based on",
    ["# of Songs", "Duration"]
)

# Display only the slider for the selected mode
if length_mode == "# of Songs":
    playlist_tracks = playlist_slider(
        label="Number of songs",
        minimum=MIN_SONGS,
        maximum=MAX_SONGS,
        default=DEFAULT_SONGS,
        step=1,
        marks=[5, 10, 20, 30, 40, 50],
        mode="songs",
        key="playlist_songs"
    )

    playlist_minutes = None

else:
    playlist_minutes = playlist_slider(
        label="Playlist duration",
        minimum=MIN_DURATION,
        maximum=MAX_DURATION,
        default=DEFAULT_DURATION,
        step=5,
        marks=[30, 60, 90, 120, 150, 180],
        mode="duration",
        key="playlist_duration"
    )

    playlist_tracks = None



if uploaded_photo:
    st.image(
        uploaded_photo,
        caption="Your uploaded photograph",
        width=480
    )

if st.button("Generate My Playlist"):
    if uploaded_photo and keywords.strip():

        with st.spinner("Analyzing your photograph..."):
            try:
                # Prevent an unrelated environment key from taking precedence
                os.environ.pop("GOOGLE_API_KEY", None)

                # Connect to Gemini using our private API key
                client = genai.Client(
                    api_key=st.secrets["GEMINI_API_KEY"]
                )

                # Optimize the uploaded photograph before Gemini analysis
                image_bytes = optimize_image(uploaded_photo)
                st.session_state.image_optimization = {
                    "original_size": len(uploaded_photo.getvalue()),
                    "optimized_size": len(image_bytes),
}

                # Determine playlist generation requirements
                if length_mode == "# of Songs":
                    length_instruction = f"""
                        Create a playlist containing exactly {playlist_tracks} songs.
                        """

                else:
                    estimated_tracks = round(playlist_minutes / 4.5)

                    length_instruction = f"""
                        Create a playlist targeting {playlist_minutes} minutes.

                        Begin with approximately {estimated_tracks} songs,
                        adjusting the number based on their actual durations.

                        The combined duration of all recommended songs should
                        be within 5% of {playlist_minutes} minutes.

                        IMPORTANT:
                        - Calculate the sum of all duration_seconds values.
                        - Add songs if the total is too short.
                        - Remove songs if the total is too long.
                        - Do not invent or alter recording durations.
                        - Maintain musical cohesion and natural transitions.
                        """

                # Build the prompt
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


                # Send both the photograph and text to Gemini
                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type="image/jpeg"
                        ),
                        prompt
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=PLAYLIST_SCHEMA
                    )
                )

                playlist = response.parsed

                # Clear diagnostics for each new generation
                st.session_state.duration_debug = []

                # Validate and make targeted adjustments to duration-mode playlists
                st.session_state.duration_correction_needed = False
                st.session_state.duration_correction_attempts = 0
                st.session_state.duration_initial_seconds = None
                st.session_state.duration_final_percent = None

                if length_mode == "Duration":
                    target_seconds = playlist_minutes * 60
                    playlist, initial_seconds, attempts = correct_playlist_duration(
                        client, playlist, target_seconds
                    )
                    final_seconds = calculate_duration(playlist["songs"])
                    difference_percent = abs(final_seconds - target_seconds) / target_seconds * 100

                    st.session_state.duration_initial_seconds = initial_seconds
                    st.session_state.duration_correction_needed = not within_tolerance(
                        initial_seconds, target_seconds
                    )
                    st.session_state.duration_correction_attempts = attempts
                    st.session_state.duration_final_percent = difference_percent

                    if not within_tolerance(final_seconds, target_seconds):
                        st.warning(
                            f"Playlist duration is {difference_percent:.1f}% "
                            "away from the requested duration."
                        )

                # Save the successful result for future reruns
                st.session_state.generated_length_mode = length_mode
                st.session_state.generated_playlist = playlist
                

            except Exception as error:
                st.error(f"Gemini request failed: {error}")

    else:
        st.warning("Please upload a photograph and enter some keywords.")

# Display the most recently generated playlist
if st.session_state.generated_playlist is not None:
    playlist = st.session_state.generated_playlist
   
    # Convert seconds into minutes:seconds
    def format_duration(seconds):
        minutes, remaining_seconds = divmod(int(seconds), 60)
        return f"{minutes}:{remaining_seconds:02d}"

    # Calculate the combined playlist duration
    total_seconds = sum(
        song.get("duration_seconds", 0)
        for song in playlist["songs"]
    )

    st.subheader(f"🎵 {playlist['playlist_title']}")
    st.write(playlist["vibe"])

    # Calculate hours, minutes, and seconds
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    st.caption(
        f"🎵 {len(playlist['songs'])} songs  |  "
        f"⏱️ Approx. {hours:02d} hr {minutes:02d} min {seconds:02d} sec"
    )
    # Developer diagnostics toggle
    DEBUG_MODE = False

    if DEBUG_MODE:
        st.write(
            "DEBUG EVENT COUNT:",
            len(st.session_state.duration_debug)
        )

        if (
            st.session_state.get("generated_length_mode") == "Duration"
            and st.session_state.duration_debug
        ):
            with st.expander("🔧 Duration Debug Details"):
                st.dataframe(
                    st.session_state.duration_debug,
                    hide_index=True,
                    use_container_width=True
                )

    if DEBUG_MODE and "image_optimization" in st.session_state:
        stats = st.session_state.image_optimization

        original_size = stats["original_size"]
        optimized_size = stats["optimized_size"]

        reduction = (1 - optimized_size / original_size) * 100

        st.write(
            f"Image optimization: "
            f"{original_size / 1024:.1f} KB → "
            f"{optimized_size / 1024:.1f} KB "
            f"({reduction:.1f}% reduction)"
        )

    # Temporary duration correction diagnostics
    if st.session_state.get("generated_length_mode") == "Duration":
        if st.session_state.get("duration_correction_needed"):
            st.caption(
                f"🔧 Duration correction was requested "
                f"({st.session_state.get('duration_correction_attempts', 0)} additional Gemini requests)."
            )
        else:
            st.caption("✓ Initial playlist met duration tolerance.")

    st.divider()

    for number, song in enumerate(playlist["songs"], start=1):

        duration = song.get("duration_seconds")
       

        duration_label = (
            format_duration(duration)
            if duration is not None
            else "--:--"
        )

        with st.expander(
            f"{number}. {song['title']} — {song['artist']}  ·  {duration_label}",
            expanded=False
        ):
            st.write(song["reason"])

            search_query = quote(f"{song['title']} {song['artist']}")

            spotify_url = (
                f"https://open.spotify.com/search/{search_query}"
            )

            youtube_url = (
                f"https://music.youtube.com/search?q={search_query}"
            )

            col_spotify, col_youtube, _ = st.columns([1, 1, 3])

            with col_spotify:
                st.link_button(
                    "Spotify ↗",
                    spotify_url
                )

            with col_youtube:
                st.link_button(
                    "YouTube Music ↗",
                    youtube_url
            )

    st.divider()

    st.markdown("### The Musical Journey")
    st.write(playlist["musical_journey"])

