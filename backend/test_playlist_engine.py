
from backend.playlist_engine import (
    calculate_duration,
    within_tolerance,
    remove_excess_tracks,
    add_best_candidates,
)


def song(title, seconds):
    return {
        "title": title,
        "artist": "Test Artist",
        "reason": "Test song",
        "duration_seconds": seconds,
    }


def test_duration_calculation():
    songs = [
        song("Song A", 180),
        song("Song B", 240),
        song("Song C", 210),
    ]

    assert calculate_duration(songs) == 630
    print("PASS: Duration calculation")


def test_duration_tolerance():
    target = 3600

    assert within_tolerance(3600, target)
    assert within_tolerance(3780, target)
    assert within_tolerance(3420, target)
    assert not within_tolerance(3900, target)
    assert not within_tolerance(3300, target)

    print("PASS: 5% duration tolerance")


def test_excess_track_removal():
    songs = [
        song("Song A", 300),
        song("Song B", 300),
        song("Song C", 300),
        song("Song D", 300),
    ]

    result = remove_excess_tracks(songs, 900)

    assert len(result) == 3
    assert calculate_duration(result) == 900

    print("PASS: Excess track removal")


def test_candidate_additions():
    existing = [
        song("Song A", 300),
        song("Song B", 300),
    ]

    candidates = [
        song("Song C", 180),
        song("Song D", 300),
        song("Song E", 420),
    ]

    result = add_best_candidates(existing, candidates, 900)

    assert calculate_duration(result) == 900
    assert len(result) == 3
    assert result[-1]["title"] == "Song D"

    print("PASS: Candidate track selection")


if __name__ == "__main__":
    test_duration_calculation()
    test_duration_tolerance()
    test_excess_track_removal()
    test_candidate_additions()

    print("\nAll four playlist engine tests passed!")
