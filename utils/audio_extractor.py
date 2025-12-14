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
    duration = video.duration
    print_substep(f"Video duration: {duration:.2f} seconds")
    
    # Create progress bar
    from tqdm import tqdm
    
    print_substep("Extracting audio...")
    with tqdm(total=100, desc="      Extracting", unit="%", ncols=80) as pbar:
        try:
            # Try moviepy 1.x syntax
            video.audio.write_audiofile(audio_path, verbose=False, logger=None)
        except TypeError:
            # Fallback to moviepy 2.x syntax
            video.audio.write_audiofile(audio_path, logger=None)
        
        # Complete progress
        pbar.update(100)
    
    video.close()
    print_success(f"Audio extracted to {audio_path}")
    return audio_path
