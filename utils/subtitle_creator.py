"""Subtitle creation utilities"""
import os
import pysrt
from tqdm import tqdm
from .ui import print_step, print_success


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
    """Get subtitle styling from environment variables with auto-detection"""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get preset
    preset = os.getenv('SUBTITLE_PRESET', 'auto').lower()
    position = os.getenv('SUBTITLE_POSITION', 'bottom').lower()
    
    # Auto-detect if preset is 'auto' and video path is provided
    if preset == 'auto' and video_path:
        orientation = detect_video_orientation(video_path)
        if orientation == 'vertical':
            preset = 'reels'
            from .ui import print_substep
            print_substep("Auto-detected vertical video, using 'reels' preset")
        else:
            preset = 'minimal'
            from .ui import print_substep
            print_substep("Auto-detected horizontal video, using 'minimal' preset")
    
    # Preset configurations
    presets = {
        'minimal': {
            'font_size': 14,
            'outline': 1,
            'margin': 10,
            'shadow': 0
        },
        'standard': {
            'font_size': 16,
            'outline': 1,
            'margin': 15,
            'shadow': 1
        },
        'bold': {
            'font_size': 20,
            'outline': 2,
            'margin': 20,
            'shadow': 1
        },
        'reels': {
            'font_size': 11,  # Lebih kecil untuk layar vertikal
            'outline': 1,
            'margin': 8,      # Margin lebih kecil
            'shadow': 0
        },
        'reels-bold': {
            'font_size': 13,  # Sedikit lebih besar tapi tetap compact
            'outline': 1.5,
            'margin': 10,
            'shadow': 1
        }
    }
    
    # Get preset values or default to minimal
    style = presets.get(preset, presets['minimal'])
    
    # Override with custom values if provided
    custom_font_size = os.getenv('SUBTITLE_FONT_SIZE')
    custom_outline = os.getenv('SUBTITLE_OUTLINE')
    custom_margin = os.getenv('SUBTITLE_MARGIN')
    
    if custom_font_size:
        style['font_size'] = int(custom_font_size)
    if custom_outline:
        style['outline'] = int(custom_outline)
    if custom_margin:
        style['margin'] = int(custom_margin)
    
    # Adjust margin based on position
    if position == 'top':
        # MarginV for top position (negative or small value)
        style['margin_v'] = style['margin']
        style['alignment'] = 8  # Top center
    elif position == 'center':
        style['margin_v'] = 0
        style['alignment'] = 5  # Center
    else:  # bottom (default)
        style['margin_v'] = style['margin']
        style['alignment'] = 2  # Bottom center
    
    return style


def create_srt(segments, output_path, video_path=None):
    """Create SRT subtitle file from segments with styling"""
    print_step(3, 3, "Creating subtitle file")
    subs = pysrt.SubRipFile()
    
    # Get styling configuration with auto-detection
    style = get_subtitle_styling(video_path)
    
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
        # Format: {\fs<size>\b0\c&HFFFFFF&\3c&H000000&\bord<outline>\shad<shadow>\a<alignment>}
        styling = (
            f"{{\\fs{style['font_size']}"
            f"\\b0"
            f"\\c&HFFFFFF&"
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
