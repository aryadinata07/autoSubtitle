"""
Media Processing Utilities
Consolidates Audio Extraction and Video Embedding logic using FFmpeg/MoviePy.
"""
import os
import subprocess
import json
from typing import Optional

from utils.system.ui import print_step, print_substep, print_success, print_error, print_warning

# --- AUDIO EXTRACTION ---

def extract_audio(video_path: str, audio_path: str = "temp_audio.wav") -> str:
    """Extract audio from video file using moviepy"""
    try:
        from moviepy.editor import VideoFileClip
    except ImportError:
        try:
            from moviepy import VideoFileClip
        except ImportError:
             raise ImportError("MoviePy not installed. Please install it with: pip install moviepy")
             
    print_step(1, 3, f"Extracting audio from {video_path}")
    
    try:
        video = VideoFileClip(video_path)
        duration = video.duration
        print_substep(f"Video duration: {duration:.2f} seconds")
        
        from tqdm import tqdm
        print_substep("Extracting audio...")
        
        with tqdm(total=100, desc="      Extracting", unit="%", ncols=80) as pbar:
            try:
                # Try moviepy 1.x syntax
                video.audio.write_audiofile(audio_path, verbose=False, logger=None)
            except TypeError:
                # Fallback to moviepy 2.x syntax
                video.audio.write_audiofile(audio_path, logger=None)
            except AttributeError:
                 # Video has no audio
                 print_warning("No audio track found in video!")
                 # Create silent audio to prevent crash
                 cmd = ['ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-t', str(duration), '-q:a', '9', '-acodec', 'libmp3lame', audio_path, '-y']
                 subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            pbar.update(100)
        
        video.close()
        print_success(f"Audio extracted to {audio_path}")
        return audio_path
        
    except Exception as e:
        print_error(f"Failed to extract audio: {e}")
        raise e

# --- VIDEO EMBEDDING ---

def get_video_duration(video_path: str) -> Optional[float]:
    """Get video duration in seconds using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace')
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except:
        return None

def check_gpu_available() -> bool:
    """Check if NVIDIA GPU is available for hardware acceleration"""
    try:
        # Check nvidia-smi
        result = subprocess.run(
            ['nvidia-smi'], capture_output=True, encoding='utf-8', errors='replace', timeout=5
        )
        if result.returncode != 0: return False
        
        # Check ffmpeg support
        result2 = subprocess.run(
            ['ffmpeg', '-hwaccels'], capture_output=True, encoding='utf-8', errors='replace', timeout=5
        )
        return 'cuda' in result2.stdout.lower()
    except:
        return False

def embed_subtitle_to_video(video_path: str, subtitle_path: str, output_path: str = None, method: str = 'soft') -> str:
    """Embed subtitle directly into video using ffmpeg"""
    if output_path is None:
        base_name = os.path.splitext(video_path)[0]
        output_path = f"{base_name}_with_subtitle.mp4"
    
    print_step(4, 4, "Embedding subtitle to video")
    duration = get_video_duration(video_path)
    if duration: print_substep(f"Video duration: {duration:.1f} seconds")
    
    # Pre-process paths
    subtitle_path_abs = os.path.abspath(subtitle_path)
    # FFMpeg escaping for Windows: Escape backslashes and colons
    subtitle_path_escaped = subtitle_path_abs.replace('\\', '/').replace(':', '\\:')
    subtitle_path_escaped = subtitle_path_escaped.replace("'", "'\\''")
    subtitle_filter = f"subtitles='{subtitle_path_escaped}'"

    cmd = []
    
    # 1. SOFT SUBTITLE
    if method == 'soft':
        print_substep("🚀 Mode: SOFT SUBTITLE (Stream Copy)")
        cmd = [
            'ffmpeg', '-i', video_path, '-i', subtitle_path,
            '-c:v', 'copy', '-c:a', 'copy',
            '-c:s', 'mov_text', '-metadata:s:s:0', 'language=ind',
            '-metadata:s:s:0', 'title=Indonesian', '-disposition:s:0', 'default',
            '-y', output_path
        ]
    
    # 2. GPU HARDSUB
    elif method == 'gpu':
        if not check_gpu_available():
            print_warning("NVIDIA GPU not available, falling back to fast encoding")
            method = 'fast'
        else:
            print_substep("🔥 Mode: GPU HARDSUB (NVENC)")
            cmd = [
                'ffmpeg', '-hwaccel', 'cuda', '-i', video_path,
                '-vf', subtitle_filter, '-c:v', 'h264_nvenc', '-preset', 'p1',
                '-c:a', 'copy', '-y', output_path
            ]

    # 3/4. CPU HARDSUB (Fast/Standard)
    if method in ['fast', 'standard']:
        mode_name = "Ultrafast" if method == 'fast' else "Standard Quality"
        preset = "ultrafast" if method == 'fast' else "medium"
        crf = "28" if method == 'fast' else "23"
        
        print_substep(f"⚙️ Mode: CPU HARDSUB ({mode_name})")
        cmd = [
            'ffmpeg', '-i', video_path, '-vf', subtitle_filter,
            '-c:v', 'libx264', '-preset', preset, '-crf', crf,
            '-c:a', 'copy', '-y', output_path
        ]
        
    print_substep("Processing video, please wait...")
    
    try:
        from tqdm import tqdm
        import re
        
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding='utf-8', errors='replace'
        )
        
        pbar = None
        if duration and method != 'soft':
             pbar = tqdm(total=int(duration), desc="      Embedding", unit="s", ncols=80)
             
        for line in process.stderr:
            if pbar and 'time=' in line:
                match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                if match:
                    h, m, s = match.groups()
                    curr = int(h)*3600 + int(m)*60 + float(s)
                    if curr <= duration:
                        pbar.n = int(curr)
                        pbar.refresh()
                        
        process.wait()
        if pbar: pbar.close()
        
        if process.returncode != 0:
            raise Exception("FFmpeg process returned error code")
            
        print_success(f"Saved: {output_path}")
        return output_path
        
    except Exception as e:
        print_error(f"Error embedding subtitle: {e}")
        raise
