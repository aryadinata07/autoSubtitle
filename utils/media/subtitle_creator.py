"""Subtitle creation utilities"""
import os
import pysrt
from tqdm import tqdm
from utils.system.ui import print_step, print_success


def detect_video_orientation(video_path):
    """
    Detect if video is vertical (portrait) or horizontal (landscape)
    Returns: 'vertical' or 'horizontal'
    """
    try:
        import subprocess
        import json
        
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
        
        # Find video stream
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                width = int(stream.get('width', 0))
                height = int(stream.get('height', 0))
                
                if width > 0 and height > 0:
                    # Vertical if height > width (e.g., 1080x1920 for Reels)
                    return 'vertical' if height > width else 'horizontal'
        
        return 'horizontal'  # Default
    except:
        return 'horizontal'  # Default on error


def get_subtitle_styling(video_path=None):
    """Get subtitle styling from core config"""
    from core.config import load_config
    config = load_config()
    
    # Get values from config (defaults handled in config.py)
    style = {
        'font_size': int(config.get('SUB_FONT_SIZE', 20)),
        'color': config.get('SUB_FONT_COLOR', '&HFFFFFF'),
        'outline': int(config.get('SUB_OUTLINE_WIDTH', 2)),
        'shadow': int(config.get('SUB_SHADOW_DEPTH', 1)),
        'position': config.get('SUB_POSITION', 'bottom'),
        'margin_v': 10, # Default margin
        'alignment': 2  # Bottom center default
    }
    
    # Handle Position Logic
    pos = style['position'].lower()
    if pos == 'top':
        style['alignment'] = 8
        style['margin_v'] = 20
    elif pos == 'center':
        style['alignment'] = 5
        style['margin_v'] = 0
    else:
        style['alignment'] = 2
        style['margin_v'] = 10
        
    return style


def create_srt(segments, output_path, video_path=None):
    """Create SRT subtitle file from segments with styling"""
    print_step(3, 3, "Creating subtitle file")
    subs = pysrt.SubRipFile()
    
    # Get styling configuration
    style = get_subtitle_styling()
    
    for i, segment in enumerate(
        tqdm(segments, desc="      Processing segments", unit="segment"), start=1
    ):
        # Convert seconds to hours, minutes, seconds, milliseconds
        start_sec = segment["start"]
        end_sec = segment["end"]
        
        start_hours = int(start_sec // 3600)
        start_minutes = int((start_sec % 3600) // 60)
        start_seconds = int(start_sec % 60)
        start_millis = int((start_sec % 1) * 1000)
        
        end_hours = int(end_sec // 3600)
        end_minutes = int((end_sec % 3600) // 60)
        end_seconds = int(end_sec % 60)
        end_millis = int((end_sec % 1) * 1000)
        
        text = segment["text"].strip()
        
        # Add ASS styling tags based on configuration
        # Format: {\fs<size>\b1\c<color>\3c&H000000&\bord<outline>\shad<shadow>\a<alignment>}
        styling = (
            f"{{\\fs{style['font_size']}"
            f"\\b1"
            f"\\c{style['color']}"
            f"\\3c&H000000&"
            f"\\bord{style['outline']}"
            f"\\shad{style['shadow']}"
            f"\\a{style['alignment']}"
            f"\\MarginV={style['margin_v']}}}"
        )
        text = f"{styling}{text}"
        
        sub = pysrt.SubRipItem(
            index=i,
            start={
                "hours": start_hours,
                "minutes": start_minutes,
                "seconds": start_seconds,
                "milliseconds": start_millis,
            },
            end={
                "hours": end_hours,
                "minutes": end_minutes,
                "seconds": end_seconds,
                "milliseconds": end_millis,
            },
            text=text,
        )
        subs.append(sub)
    
    subs.save(output_path, encoding="utf-8")
    print_success(f"Subtitle saved to {output_path}")
    return subs
