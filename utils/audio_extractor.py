"""Audio extraction utilities"""
import os
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    from moviepy import VideoFileClip
from .ui import print_step, print_substep, print_success


def extract_audio(video_path, audio_path="temp_audio.wav"):
    """Extract audio from video file"""
    print_step(1, 3, f"Extracting audio from {video_path}")
    video = VideoFileClip(video_path)
    print_substep(f"Video duration: {video.duration:.2f} seconds")
    try:
        # Try moviepy 1.x syntax
        video.audio.write_audiofile(audio_path, verbose=False, logger=None)
    except TypeError:
        # Fallback to moviepy 2.x syntax
        video.audio.write_audiofile(audio_path, logger=None)
    video.close()
    print_success(f"Audio extracted to {audio_path}")
    return audio_path
