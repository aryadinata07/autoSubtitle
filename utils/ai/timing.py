"""
Subtitle Timing Utilities
Consolidates timing adjustment and AI-based structure analysis.
"""
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from utils.system.ui import print_substep, print_warning, print_step

def adjust_subtitle_timing(segments: List[Dict], structure_analysis: Optional[List[str]] = None) -> List[Dict]:
    """
    Smart timing adjustment with Linguistic Bridging.
    """
    load_dotenv()
    
    min_duration = float(os.getenv('SUBTITLE_MIN_DURATION', '1.5'))
    max_duration = float(os.getenv('SUBTITLE_MAX_DURATION', '8.0'))
    gap_settings = float(os.getenv('SUBTITLE_GAP', '0.1'))
    
    min_reading_speed = 15 # chars per second
    adjusted_segments = []
    
    for i, segment in enumerate(segments):
        start = segment['start']
        end = segment['end']
        text = segment['text']
        
        # Calculate minimum duration based on reading speed
        text_length = len(text)
        min_reading_duration = text_length / min_reading_speed
        effective_min_duration = max(min_duration, min_reading_duration)
        
        # Check next subtitle
        if i < len(segments) - 1:
            next_start = segments[i + 1]['start']
            silence_gap = next_start - end
            
            # Sentence incomplete check
            sentence_incomplete = False
            if structure_analysis and i < len(structure_analysis):
                if structure_analysis[i] == 'CONTINUES':
                    sentence_incomplete = True
            else:
                 # Fallback: check punctuation
                 sentence_incomplete = not (text.strip() and text.strip()[-1] in ['.', '?', '!', '"', ')', ']'])
            
            # Logic: Bridge gap if incomplete or gap is small
            if sentence_incomplete and silence_gap < 4.0:
                potential_end = next_start - gap_settings
                if (potential_end - start) <= max_duration:
                    end = potential_end
                else:
                    end = start + max_duration
            elif silence_gap < 1.5:
                potential_end = next_start - gap_settings
                if (potential_end - start) <= max_duration:
                    end = potential_end
                    
            # Overlap check
            if end >= next_start:
                end = next_start - gap_settings
                
        # Ensure min duration
        if (end - start) < effective_min_duration:
             # Try to extend
             potential_end = start + effective_min_duration
             if i < len(segments) - 1:
                 next_start = segments[i+1]['start']
                 if potential_end < next_start - gap_settings:
                     end = potential_end
                 else:
                     end = next_start - gap_settings
             else:
                 end = potential_end

        adjusted_segments.append({
            'start': round(start, 3),
            'end': round(end, 3),
            'text': text
        })
        
    return adjusted_segments

def optimize_subtitle_gaps(segments):
    """Pass-through for backward compatibility"""
    return segments

# --- DeepSeek Timing Analysis ---

def analyze_sentence_structure(segments: List[Dict], api_key: str) -> List[str]:
    """Analyze segments to flag incomplete sentences using DeepSeek."""
    from openai import OpenAI
    import time
    from tqdm import tqdm
    import re

    print_step(3, 3, "Analyzing sentence structure with DeepSeek AI...")
    
    statuses = []
    batch_size = 20
    texts = [s['text'] for s in segments]
    
    with tqdm(total=len(texts), desc="Analyzing", unit="seg", ncols=80) as pbar:
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                if i > 0: time.sleep(0.1)
                
                # ... API Call logic ...
                # Simplified for consolidation to save space but maintaining logic
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=30.0)
                numbered_texts = "\n".join([f"{j+1}. {text}" for j, text in enumerate(batch)])
                
                system_prompt = "You are a Linguistic Structure Analyzer. Output 'COMPLETE' or 'CONTINUES' for each line."
                user_prompt = f"Analyze:\n{numbered_texts}"
                
                response = client.chat.completions.create(
                    model="deepseek-chat", messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ], temperature=0.0
                )
                
                response_text = response.choices[0].message.content.strip()
                batch_statuses = []
                
                for line in response_text.split('\n'):
                    match = re.match(r'^\d+[\.\)\s]+([A-Z]+)', line.upper())
                    if match:
                        status = match.group(1).strip()
                        if status in ['COMPLETE', 'CONTINUES']:
                            batch_statuses.append(status)
                
                # Fill missing
                while len(batch_statuses) < len(batch):
                    batch_statuses.append('COMPLETE')
                
                statuses.extend(batch_statuses)
                pbar.update(len(batch))
                
            except Exception as e:
                print_warning(f"Analysis loop error: {e}")
                statuses.extend(['COMPLETE'] * len(batch))
                pbar.update(len(batch))
                
    return statuses
