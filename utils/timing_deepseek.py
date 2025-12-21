"""DeepSeek AI sentence structure analysis for timing adjustment"""
from openai import OpenAI
from tqdm import tqdm
import time
from .ui import print_substep, print_warning, print_step


def analyze_structure_batch(texts, api_key):
    """
    Analyze sentence structure of a batch of texts.
    Returns a list of status: 'COMPLETE' or 'CONTINUES'
    """
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            timeout=30.0
        )
        
        # Create numbered list
        numbered_texts = "\n".join([f"{i+1}. {text}" for i, text in enumerate(texts)])
        
        system_prompt = f"""You are a Linguistic Structure Analyzer.
Task: Determine if each subtitle segment is a COMPLETE sentence/thought or if it CONTINUES to the next segment.

Input: Numbered list of subtitle segments.
Output: Numbered list of status (COMPLETE or CONTINUES).

RULES:
1. 'COMPLETE' = The sentence ends here (has period, question mark, or clear thought completion).
2. 'CONTINUES' = The sentence is incomplete/hanging and continues to the next segment.
3. OUTPUT FORMAT: "1. [STATUS]"
4. Provide EXACTLY {len(texts)} lines.
5. NO explanations.

Example Input:
1. Hello everyone
2. today we are going to
3. discuss AI.

Example Output:
1. COMPLETE
2. CONTINUES
3. COMPLETE"""

        user_prompt = f"""Analyze these {len(texts)} segments:
{numbered_texts}"""

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=1000
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse output
        statuses = []
        import re
        
        for line in response_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Match "1. COMPLETE" or "1. CONTINUES"
            match = re.match(r'^\d+[\.\)\s]+([A-Z]+)', line.upper())
            if match:
                status = match.group(1).strip()
                if status in ['COMPLETE', 'CONTINUES']:
                    statuses.append(status)
                else:
                    statuses.append('COMPLETE') # Default safe fallback
        
        # Validate count
        if len(statuses) != len(texts):
            # Fallback: fill with COMPLETE (safest)
            while len(statuses) < len(texts):
                statuses.append('COMPLETE')
            statuses = statuses[:len(texts)]
            
        return statuses

    except Exception as e:
        print_warning(f"Batch analysis failed: {str(e)}")
        # Fallback: All COMPLETE (disable bridging for this batch)
        return ['COMPLETE'] * len(texts)


def analyze_sentence_structure(segments, api_key):
    """
    Analyze all segments to flags incomplete sentences.
    Returns: List of statuses corresponding to segments.
    """
    print_step(3, 3, "Analyzing sentence structure with DeepSeek AI...")
    print_substep("This helps prevent subtitles from disappearing too fast...")
    
    statuses = []
    batch_size = 20 # Can be larger since output is short tokens
    
    texts = [s['text'] for s in segments]
    
    with tqdm(total=len(texts), desc="Analyzing", unit="seg", ncols=80) as pbar:
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                if i > 0:
                    time.sleep(0.1)
                
                batch_statuses = analyze_structure_batch(batch, api_key)
                statuses.extend(batch_statuses)
                pbar.update(len(batch))
                
            except Exception as e:
                print_warning(f"Analysis loop error: {str(e)}")
                statuses.extend(['COMPLETE'] * len(batch))
                pbar.update(len(batch))
                
    return statuses
