"""Playlist schemas and duration correction, independent of Streamlit."""

from google.genai import types


def log_duration_event(diagnostics, stage, songs, target_seconds, **details):
    """Append a diagnostic event to a request-scoped list."""
    actual_seconds = calculate_duration(songs)
    difference_seconds = actual_seconds - target_seconds
    event = {
        "stage": stage,
        "song_count": len(songs),
        "actual_seconds": actual_seconds,
        "target_seconds": target_seconds,
        "difference_seconds": difference_seconds,
        "difference_percent": round(difference_seconds / target_seconds * 100, 2),
        **details,
    }
    diagnostics.append(event)


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


def correct_playlist_duration(client, playlist, target_seconds, diagnostics=None):
    """Keep the original playlist and make at most two targeted Gemini requests."""

    if diagnostics is None:
        diagnostics = []

    playlist = dict(playlist)
    playlist["songs"] = list(playlist["songs"])

    initial_seconds = calculate_duration(playlist["songs"])
    attempts = 0

    # Record initial generation
    log_duration_event(diagnostics, 
        "Initial generation",
        playlist["songs"],
        target_seconds
    )

    # If already within tolerance, no correction is needed
    if within_tolerance(initial_seconds, target_seconds):
        log_duration_event(diagnostics, 
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

        log_duration_event(diagnostics, 
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
        log_duration_event(diagnostics, 
            f"Correction {attempts}",
            playlist["songs"],
            target_seconds,
            songs_requested=approximate_count,
            songs_returned=len(candidates),
            songs_accepted=len(playlist["songs"]) - songs_before
        )

    # IMPORTANT: This section is OUTSIDE the for loop

    log_duration_event(diagnostics, 
        "Final result",
        playlist["songs"],
        target_seconds,
        correction_attempts=attempts
    )

    return playlist, initial_seconds, attempts

