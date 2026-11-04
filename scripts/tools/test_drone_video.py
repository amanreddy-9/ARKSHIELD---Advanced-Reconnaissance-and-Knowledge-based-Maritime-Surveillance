import json
from pathlib import Path

from pipeline.orchestrator import OATrackPipeline


# ============================================================
# VIDEO FILES
# ============================================================

VIDEO_DIR = Path("data/test_mp4")

VIDEO_FILES = [
    "Oil tanker with a drone! #shorts #merchantnavy #ships #viral #trending #dronevideo #drone #oiltanker.mp4",
    "Allure of the Seas sailing from Port Canaveral🤩 #cruise #drone.mp4",
]


# ============================================================
# PIPELINE
# ============================================================

pipeline = OATrackPipeline()


# ============================================================
# PROCESS VIDEOS
# ============================================================

for video_name in VIDEO_FILES:

    video_path = VIDEO_DIR / video_name

    print()
    print("=" * 70)
    print(f"PROCESSING: {video_name}")
    print("=" * 70)

    if not video_path.exists():
        print(f"\nERROR: Video not found:")
        print(video_path)
        continue

    try:

        result = pipeline.drone_video(
            str(video_path),
            target_x=None,
            target_y=None,
        )

    except Exception as exc:

        print()
        print("PIPELINE ERROR:")
        print(exc)

        continue

    # ========================================================
    # BASIC SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("VIDEO SUMMARY")
    print("=" * 70)

    print(f"Status: {result.get('status')}")
    print(f"Mode: {result.get('mode')}")
    print(f"Video: {result.get('video_path')}")
    print(f"FPS: {result.get('fps')}")
    print(f"Frame count: {result.get('frame_count')}")
    print(f"Processed frames: {result.get('processed_frames')}")
    print(
        f"Resolution: "
        f"{result.get('resolution', {}).get('width')} x "
        f"{result.get('resolution', {}).get('height')}"
    )

    print(
        f"Status message: "
        f"{result.get('status_message')}"
    )

    print(
        f"Unique Track IDs: "
        f"{result.get('unique_track_count')}"
    )

    print(
        f"Total detections: "
        f"{result.get('total_detections')}"
    )

    print(
        f"Average detections/frame: "
        f"{result.get('average_detections_per_frame')}"
    )

    # ========================================================
    # RL PROCESSING MODES
    # ========================================================

    print()
    print("-" * 70)
    print("PROCESSING MODES")
    print("-" * 70)

    processing_modes = result.get(
        "processing_mode_counts",
        {}
    )

    if processing_modes:

        for mode, count in processing_modes.items():
            print(f"{mode}: {count} frames")

    else:
        print("No processing mode information.")

    # ========================================================
    # STABLE TRACK CLASSIFICATIONS
    # ========================================================

    print()
    print("=" * 70)
    print("STABLE TRACK CLASSIFICATIONS")
    print("=" * 70)

    final_tracks = result.get(
        "final_track_classifications",
        {}
    )

    if not final_tracks:

        print("No stable track classifications found.")

    else:

        primary = result.get("primary_vessel")

        if primary:

            print()
            print("DASHBOARD HEADLINE (ONE TRACK, NOT A VIDEO-WIDE LABEL)")
            print(
                f"Primary track: {primary.get('track_id')} "
                f"— {primary.get('label')} "
                f"(stability={primary.get('stability')}, "
                f"observations={primary.get('observations')})"
            )

        print()
        print("INDIVIDUAL TRACKS")

        for track_id, info in sorted(
            final_tracks.items(),
            key=lambda x: int(x[0])
        ):

            print()
            print(f"Track {track_id}")
            print(
                f"  Class: "
                f"{info.get('label')}"
            )

            print(
                f"  Stability: "
                f"{info.get('stability')}"
            )

            print(
                f"  Observations: "
                f"{info.get('observations')}"
            )

            summary = result.get(
                "track_summaries",
                {}
            ).get(str(track_id), {})

            if summary:

                print(
                    f"  Evidence: "
                    f"{summary.get('classification_status')}"
                )

                print(
                    f"  Last seen frame: "
                    f"{summary.get('last_seen_frame')}"
                )

    # ========================================================
    # SHOW LAST OBSERVATION FOR EACH TRACK
    # ========================================================

    print()
    print("=" * 70)
    print("LATEST TRACK OBSERVATIONS")
    print("=" * 70)

    latest_tracks = {}

    for frame in result.get(
        "frames",
        []
    ):

        for track in frame.get(
            "tracks",
            []
        ):

            latest_tracks[
                track["track_id"]
            ] = track

    if not latest_tracks:

        print("No tracks found.")

    else:

        for track_id, track in sorted(
            latest_tracks.items(),
            key=lambda x: int(x[0])
        ):

            print()
            print(f"Track {track_id}")

            current = track.get(
                "classification"
            )

            stable = track.get(
                "classification_stable"
            )

            if current:

                print(
                    f"  Current: "
                    f"{current.get('label')} "
                    f"({current.get('confidence')})"
                )

            if stable:

                print(
                    f"  Stable: "
                    f"{stable.get('label')} "
                    f"(stability="
                    f"{stable.get('stability')}, "
                    f"observations="
                    f"{stable.get('observations')})"
                )

    # ========================================================
    # FIRST 5 FRAMES
    # ========================================================

    print()
    print("=" * 70)
    print("FIRST 5 FRAMES")
    print("=" * 70)

    for frame in result.get(
        "frames",
        []
    )[:5]:

        print()
        print(
            f"Frame {frame.get('frame_index')} "
            f"at {frame.get('timestamp'):.2f}s"
        )

        print(
            f"  Ships: "
            f"{frame.get('ship_count')}"
        )

        print(
            f"  Tracks: "
            f"{frame.get('active_track_count')}"
        )

        print(
            f"  Processing: "
            f"{frame.get('processing_mode')}"
        )

        for track in frame.get(
            "tracks",
            []
        ):

            current = track.get(
                "classification"
            )

            stable = track.get(
                "classification_stable"
            )

            print(
                f"  Track {track.get('track_id')}:"
            )

            if current:

                print(
                    f"    Current: "
                    f"{current.get('label')} "
                    f"{current.get('confidence')}"
                )

            if stable:

                print(
                    f"    Stable: "
                    f"{stable.get('label')} "
                    f"(stability="
                    f"{stable.get('stability')})"
                )

    # ========================================================
    # SAVE RESULT
    # ========================================================

    output_path = (
        video_path.with_name(
            video_path.stem +
            "_result.json"
        )
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 70)
    print(
        f"Saved result: {output_path}"
    )
    print("=" * 70)
