"""Video subtitle embedding utilities"""
import os
from .ui import print_step, print_substep, print_success, print_error, print_warning


def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe"""
    import subprocess
    import json
    
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except:
        return None


def check_gpu_available():
    """Check if NVIDIA GPU is available for hardware acceleration"""
    import subprocess
    try:
        # Check if nvidia-smi exists (NVIDIA GPU driver)
        result = subprocess.run(
            ['nvidia-smi'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return False
        
        # Also check if ffmpeg supports cuda
        result2 = subprocess.run(
            ['ffmpeg', '-hwaccels'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return 'cuda' in result2.stdout.lower() and result.returncode == 0
    except:
        return False


def embed_subtitle_to_video(video_path, subtitle_path, output_path=None, method='standard'):
    """
    Embed subtitle directly into video using ffmpeg
    
    Args:
        video_path: Path to input video
        subtitle_path: Path to SRT subtitle file
        output_path: Path to output video (default: video_with_subtitle.mp4)
        method: Encoding method ('standard', 'fast', 'gpu')
    """
    import subprocess
    
    if output_path is None:
        base_name = os.path.splitext(video_path)[0]
        output_path = f"{base_name}_with_subtitle.mp4"
    
    print_step(4, 4, "Embedding subtitle to video")
    
    # Get video duration
    duration = get_video_duration(video_path)
    if duration:
        print_substep(f"Video duration: {duration:.1f} seconds")
    
    # Escape subtitle path for ffmpeg subtitles filter
    # Convert to absolute path and escape special characters properly
    subtitle_path_abs = os.path.abspath(subtitle_path)
    # For Windows paths in ffmpeg: use forward slashes and escape special chars
    subtitle_path_escaped = subtitle_path_abs.replace('\\', '/').replace(':', '\\:')
    # Escape single quotes by replacing with '\'' (end quote, escaped quote, start quote)
    subtitle_path_escaped = subtitle_path_escaped.replace("'", "'\\''")
    
    # Build ffmpeg command based on method
    # Simplified subtitle filter without force_style to avoid parsing issues
    subtitle_filter = f"subtitles='{subtitle_path_escaped}'"
    
    if method == 'gpu':
        # Check GPU availability
        if not check_gpu_available():
            print_warning("NVIDIA GPU not available, falling back to fast encoding")
            method = 'fast'
        else:
            print_substep("Using GPU acceleration (NVIDIA NVENC)")
            cmd = [
                'ffmpeg',
                '-hwaccel', 'cuda',
                '-i', video_path,
                '-vf', subtitle_filter,
                '-c:v', 'h264_nvenc',
                '-preset', 'fast',
                '-c:a', 'copy',
                '-y',
                output_path
            ]
    
    if method == 'fast':
        print_substep("Using fast encoding preset (veryfast)")
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', subtitle_filter,
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            output_path
        ]
    
    elif method == 'standard':
        print_substep("Using standard quality encoding (medium)")
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', subtitle_filter,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            output_path
        ]
    
    # Estimate time
    if method == 'standard':
        print_substep("Estimated time: ~12-13 minutes for 17 min video")
    elif method == 'fast':
        print_substep("Estimated time: ~4-6 minutes for 17 min video")
    elif method == 'gpu':
        print_substep("Estimated time: ~2-3 minutes for 17 min video")
    
    print_substep("Processing video, please wait...")
    
    try:
        # Run ffmpeg
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print_error(f"FFmpeg error: {result.stderr}")
            raise Exception("Failed to embed subtitle with ffmpeg")
        
        print_success(f"Video with subtitle saved to {output_path}")
        return output_path
        
    except FileNotFoundError:
        print_error("ffmpeg not found!")
        print_substep("Please make sure ffmpeg is installed and in PATH")
        raise
    except Exception as e:
        print_error(f"Error embedding subtitle: {str(e)}")
        raise
