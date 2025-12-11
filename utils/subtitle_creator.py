"""Subtitle creation utilities"""
import pysrt
from tqdm import tqdm
from .ui import print_step, print_success


def create_srt(segments, output_path):
    """Create SRT subtitle file from segments with styling"""
    print_step(3, 3, "Creating subtitle file")
    subs = pysrt.SubRipFile()
    
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
        # Add ASS styling tags for better appearance
        text = f"{{\\fs18\\b0\\c&HFFFFFF&\\3c&H000000&\\bord2\\shad1}}{text}"
        
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
