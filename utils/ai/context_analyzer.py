"""
AI Context Analyzer
Analyzes video filename and initial transcription to determine context, tone, and glossary.
"""
import os
from openai import OpenAI
from utils.system.ui import print_substep, print_info
from core.logger import log

def analyze_video_context(filename, sample_text, api_key):
    """
    Analyze video context using AI.
    
    Args:
        filename (str): Name of the video file
        sample_text (str): First 60-100 seconds of transcription
        api_key (str): DeepSeek API Key
        
    Returns:
        dict: Context analysis (Topic, Tone, Keywords)
        or None if failed
    """
    if not api_key:
        return None
        
    print_substep("🔍 Analyzing video context (Premium)...")
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    system_prompt = (
        "You are an expert content strategist and linguist. "
        "Analyze the provided video filename and transcription sample. "
        "Identify the following:\n"
        "1. TOPIC: What is the video about? (Specific niche)\n"
        "2. TONE: What is the speaking style? (Formal, Casual, Humorous, FAST, Educational)\n"
        "3. GLOSSARY: List 3-10 specific technical terms, names, or slang found.\n"
        "   Format: Term=Definition/Translation constraint\n\n"
        "Output strictly in this format:\n"
        "TOPIC: ...\n"
        "TONE: ...\n"
        "GLOSSARY:\n"
        "- Term1=Definition1\n"
        "- Term2=Definition2"
    )
    
    user_prompt = f"Filename: {filename}\nSample Text: {sample_text[:1500]}"
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        result = response.choices[0].message.content
        
        # Parse result
        lines = result.split('\n')
        context = {'raw': result, 'glossary': {}}
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if line.startswith("TOPIC:"):
                context['topic'] = line.replace("TOPIC:", "").strip()
            elif line.startswith("TONE:"):
                context['tone'] = line.replace("TONE:", "").strip()
            elif line.startswith("GLOSSARY:"):
                current_section = "glossary"
            elif line.startswith("-") and "=" in line and current_section == "glossary":
                # Parse glossary item
                parts = line.replace("-", "", 1).split("=", 1)
                if len(parts) == 2:
                    term = parts[0].strip()
                    definition = parts[1].strip()
                    context['glossary'][term] = definition
                
        log.info(f"Context Analysis: {context}")
        print_info("Topic", context.get('topic', 'Unknown'))
        print_info("Tone", context.get('tone', 'Unknown'))
        if context['glossary']:
            print_substep(f"Auto-Glossary: Found {len(context['glossary'])} terms")
            for k, v in list(context['glossary'].items())[:3]: # Show top 3
                print_substep(f"   • {k} = {v}")
        
        return context
        
    except Exception as e:
        log.error(f"Context analysis failed: {e}")
        return None
