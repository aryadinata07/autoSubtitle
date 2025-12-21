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
        result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace')
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
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        
        if result.returncode != 0:
            return False
        
        # Also check if ffmpeg supports cuda
        result2 = subprocess.run(
            ['ffmpeg', '-hwaccels'],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        
        return 'cuda' in result2.stdout.lower() and result.returncode == 0
    except:
        return False


def embed_subtitle_to_video(video_path, subtitle_path, output_path=None, method='soft'):
    """
    Embed subtitle directly into video using ffmpeg
    
    Args:
        video_path: Path to input video
        subtitle_path: Path to SRT subtitle file
        output_path: Path to output video (default: video_with_subtitle.mp4)
        method: Encoding method ('soft', 'standard', 'fast', 'gpu')
            - 'soft': Soft subtitle (instant, 1-5 seconds, subtitle can be toggled)
            - 'standard': Hardsub with best quality (slow)
            - 'fast': Hardsub with fast encoding (2-3x faster)
            - 'gpu': Hardsub with GPU acceleration (fastest hardsub)
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
    
    # Build ffmpeg command based on method
    cmd = []
    
    # --- MODE 1: SOFT SUBTITLE (INSTANT) ---
    if method == 'soft':
        print_substep("🚀 Mode: SOFT SUBTITLE (Stream Copy)")
        print_substep("Speed: Instant (No re-encoding)")
        print_substep("Note: Subtitle embedded as separate track")
        print_substep("How to view: Enable subtitle in player (VLC, MPC-HC, YouTube)")
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', subtitle_path,
            '-c:v', 'copy',  # Copy video stream (no re-encoding!)
            '-c:a', 'copy',  # Copy audio stream
            '-c:s', 'mov_text',  # Subtitle format for MP4
            '-metadata:s:s:0', 'language=ind',  # Tag as Indonesian
            '-metadata:s:s:0', 'title=Indonesian',  # Subtitle title
            '-disposition:s:0', 'default',  # Set as default subtitle track
            '-y',
            output_path
        ]
    
    else:
        # For hardsub methods, need to escape subtitle path
        subtitle_path_abs = os.path.abspath(subtitle_path)
        # For Windows paths in ffmpeg: use forward slashes and escape special chars
        subtitle_path_escaped = subtitle_path_abs.replace('\\', '/').replace(':', '\\:')
        # Escape single quotes by replacing with '\'' (end quote, escaped quote, start quote)
        subtitle_path_escaped = subtitle_path_escaped.replace("'", "'\\''")
        
        subtitle_filter = f"subtitles='{subtitle_path_escaped}'"
        
        # --- MODE 2: GPU HARDSUB ---
        if method == 'gpu':
            # Check GPU availability
            if not check_gpu_available():
                print_warning("NVIDIA GPU not available, falling back to fast encoding")
                method = 'fast'
            else:
                print_substep("🔥 Mode: GPU HARDSUB (NVENC)")
                print_substep("Subtitle: Permanently burned into video")
                cmd = [
                    'ffmpeg',
                    '-hwaccel', 'cuda',
                    '-i', video_path,
                    '-vf', subtitle_filter,
                    '-c:v', 'h264_nvenc',
                    '-preset', 'p1',  # p1 = fastest preset
                    '-c:a', 'copy',
                    '-y',
                    output_path
                ]
        
        # --- MODE 3: FAST HARDSUB ---
        if method == 'fast':
            print_substep("⚙️ Mode: CPU HARDSUB (Ultrafast)")
            print_substep("Subtitle: Permanently burned into video")
            print_substep("Best for: Instagram, TikTok")
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', subtitle_filter,
                '-c:v', 'libx264',
                '-preset', 'ultrafast',  # Fastest CPU preset
                '-crf', '28',  # Lower quality for speed
                '-c:a', 'copy',
                '-y',
                output_path
            ]
        
        # --- MODE 4: STANDARD HARDSUB ---
        elif method == 'standard':
            print_substep("✨ Mode: CPU HARDSUB (Standard Quality)")
            print_substep("Subtitle: Permanently burned into video")
            print_substep("Best quality, slower encoding")
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
    if method == 'soft':
        print_substep("Estimated time: ~1-5 seconds (instant)")
    elif method == 'standard':
        print_substep("Estimated time: ~12-13 minutes for 17 min video")
    elif method == 'fast':
        print_substep("Estimated time: ~3-5 minutes for 17 min video")
    elif method == 'gpu':
        print_substep("Estimated time: ~2-3 minutes for 17 min video")
    
    print_substep("Processing video, please wait...")
    
    try:
        # Run ffmpeg with progress monitoring
        from tqdm import tqdm
        import re
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace'  # Replace undecodable bytes with ?
        )
        
        # Create progress bar if we know duration (skip for soft subtitle - too fast)
        pbar = None
        if duration and method != 'soft':
            pbar = tqdm(total=int(duration), desc="      Embedding", unit="s", ncols=80)
        
        # Monitor ffmpeg progress
        for line in process.stderr:
            if pbar and 'time=' in line:
                # Extract time from ffmpeg output (format: time=00:01:23.45)
                match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                if match:
                    hours, minutes, seconds = match.groups()
                    current_time = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                    # Update progress bar
                    if current_time <= duration:
                        pbar.n = int(current_time)
                        pbar.refresh()
        
        # Wait for process to complete
        process.wait()
        
        # Close progress bar
        if pbar:
            pbar.n = pbar.total
            pbar.refresh()
            pbar.close()
        
        if process.returncode != 0:
            stderr_output = process.stderr.read() if hasattr(process.stderr, 'read') else ""
            print_error(f"FFmpeg error: {stderr_output}")
            raise Exception("Failed to embed subtitle with ffmpeg")
        
        print_success(f"Video with subtitle saved to {output_path}")
        
        # Show instructions for soft subtitle
        if method == 'soft':
            # Verify subtitle track exists
            try:
                verify_cmd = [
                    'ffprobe',
                    '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_streams',
                    '-select_streams', 's',
                    output_path
                ]
                verify_result = subprocess.run(verify_cmd, capture_output=True, encoding='utf-8', errors='replace')
                
                if verify_result.returncode == 0:
                    import json
                    data = json.loads(verify_result.stdout)
                    if data.get('streams'):
                        print_substep("✅ Subtitle track verified successfully")
                    else:
                        print_warning("⚠️ Subtitle track not detected (might be an issue)")
            except:
                pass  # Ignore verification errors
            
            print_substep("")
            print_substep("📺 HOW TO VIEW SOFT SUBTITLE:")
            print_substep("   1. Open video with VLC, MPC-HC, or modern player")
            print_substep("   2. Right-click → Subtitle → Track 1 (Indonesian)")
            print_substep("   3. Or press 'V' key in VLC to cycle subtitle tracks")
            print_substep("")
            print_substep("✅ Subtitle is embedded but NOT burned in")
            print_substep("✅ You can toggle it On/Off anytime")
            print_substep("✅ Perfect for YouTube upload (auto-detected)")
            print_substep("")
            print_substep("💡 TIP: If subtitle not showing, use Hardsub mode instead")
            print_substep("      (Choose option 2, 3, or 4 in embedding menu)")
        
        return output_path
        
    except FileNotFoundError:
        print_error("ffmpeg not found!")
        print_substep("Please make sure ffmpeg is installed and in PATH")
        raise
    except Exception as e:
        print_error(f"Error embedding subtitle: {str(e)}")
        raise
