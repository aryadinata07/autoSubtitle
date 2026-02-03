"""
Subtitle translation utilities - Main interface
Consolidates Google Translate and DeepSeek AI implementations.
"""
from typing import Optional, Tuple, Any, List
import time
from tqdm import tqdm

from utils.system.ui import print_step, print_substep, print_success, print_warning

def translate_subtitles(
    subs: Any, 
    source_lang: str, 
    target_lang: str, 
    use_deepseek: bool = False, 
    deepseek_api_key: Optional[str] = None, 
    video_title: Optional[str] = None
) -> Any:
    """
    Translate subtitle entries using selected translator.
    """
    translator_name = "DeepSeek AI" if use_deepseek else "Google Translate"
    print_step(3, 3, f"Translating subtitles ({source_lang.upper()} -> {target_lang.upper()})")
    print_substep(f"Using: {translator_name}")
    
    if use_deepseek:
        if not deepseek_api_key:
            print_warning("DeepSeek API key not found, falling back to Google Translate")
            use_deepseek = False
    
    if use_deepseek:
        return _translate_with_deepseek(subs, source_lang, target_lang, deepseek_api_key, video_title)
    else:
        return _translate_with_google(subs, source_lang, target_lang)


def determine_translation_direction(detected_lang: str) -> Tuple[str, str]:
    """Determine translation direction based on detected language."""
    if detected_lang in ["en", "english"]:
        return "en", "id"
    elif detected_lang in ["id", "indonesian"]:
        return "id", "en"
    else:
        return "en", "id"

# --- Google Translate Implementation ---

def _translate_with_google(subs, source_lang, target_lang):
    """
    Translate using Google Translate with Smart Batching.
    Combines lines to preserve context and speed up process.
    """
    from deep_translator import GoogleTranslator
    import time
    
    translator = GoogleTranslator(source=source_lang, target=target_lang)
    
    # Configuration
    BATCH_SIZE = 25  # Subtitles per batch
    DELIMITER = " ||| " # Distinct separator
    
    print_substep(f"Smart Batching: {BATCH_SIZE} lines/chunk")
    
    total_subs = len(subs)
    
    with tqdm(total=total_subs, desc="      Translating (Smart)", unit="sub", ncols=80) as pbar:
        for i in range(0, total_subs, BATCH_SIZE):
            batch = subs[i:i+BATCH_SIZE]
            if not batch: continue
            
            # Prepare Batch
            original_texts = [s.text for s in batch]
            combined_text = DELIMITER.join(original_texts)
            
            try:
                # Translate as one big block
                translated_combined = translator.translate(combined_text)
                
                # Split back
                translated_parts = translated_combined.split(DELIMITER)
                
                # Validation: Did AI mess up the delimiters?
                if len(translated_parts) == len(batch):
                    # Success! Assign back
                    for j, sub in enumerate(batch):
                        sub.text = translated_parts[j].strip()
                    pbar.update(len(batch))
                else:
                    # Mismatch! Fallback to line-by-line for this batch only
                    # print_warning(f"Batch {i//BATCH_SIZE} mismatch (Got {len(translated_parts)}, Expected {len(batch)}). Fallback to line-by-line.")
                    for sub in batch:
                        try:
                            sub.text = translator.translate(sub.text)
                        except:
                            pass
                        pbar.update(1)
                        
            except Exception as e:
                 # Network error or other crash -> Fallback safe mode
                 # print_warning(f"Batch failed: {str(e)}")
                 for sub in batch:
                    try:
                        sub.text = translator.translate(sub.text)
                    except:
                        pass
                    pbar.update(1)
            
            # Gentle delay to respect free API limits
            time.sleep(0.5)
            
    return subs

# --- DeepSeek Implementation ---

def _translate_with_deepseek(subs, source_lang, target_lang, api_key, video_title=None):
    """Translate using DeepSeek AI with context"""
    import pysrt
    from utils.ai.context_analyzer import analyze_video_context
    from core.config import load_config
    
    config = load_config()
    fidelity_mode = config.get('FIDELITY_MODE', 'economy')
    
    # Deep copy for SubtitleShield comparison
    original_subs = pysrt.SubRipFile()
    for sub in subs:
        new_sub = pysrt.SubRipItem(
            index=sub.index, start=sub.start, end=sub.end, text=sub.text
        )
        original_subs.append(new_sub)
        
    # --- Context Analysis (Premium Only) ---
    ai_context = None
    if fidelity_mode == 'premium':
        print_step(3, 4, "Analyzing video context (Premium Mode)")
        
        # Get sample text (first 60s approx)
        sample_text = " ".join([s.text for s in subs[:20]])
        filename = video_title if video_title else "Unknown Video"
        
        ai_context = analyze_video_context(filename, sample_text, api_key)
    
    # --- Translation Loop ---
    print_step(4 if fidelity_mode == 'premium' else 3, 5 if fidelity_mode == 'premium' else 3, 
              f"Translating subtitles ({source_lang.upper()} -> {target_lang.upper()})")
    print_substep(f"Mode: {fidelity_mode.upper()}")
    
    # Build System Prompt Context
    system_context = ""
    glossary_text = ""
    
    if ai_context:
        system_context = (
            f"VIDEO CONTEXT:\n"
            f"- TOPIC: {ai_context.get('topic')}\n"
            f"- TONE: {ai_context.get('tone')}\n"
        )
        # Build Glossary Section
        if ai_context.get('glossary'):
            glossary_text = "\n[MANDATORY GLOSSARY - DO NOT TRANSLATE THESE TERMS]:\n"
            for term, definition in ai_context['glossary'].items():
                glossary_text += f"- {term} = {definition}\n"
                
    elif video_title:
        system_context = f"Video Context: Title is '{video_title}'."
        
    print_substep(f"Context loaded: {len(system_context) if system_context else 0} chars")
    if glossary_text: print_substep(f"Glossary loaded: {len(ai_context['glossary'])} terms")
    
    batch_size = 8
    last_sentence_context = ""
    
    with tqdm(total=len(subs), desc="Translating", unit="sub", ncols=80) as pbar:
        for i in range(0, len(subs), batch_size):
            batch = subs[i:i + batch_size]
            texts = [sub.text for sub in batch]
            
            try:
                if i > 0: time.sleep(0.2)
                
                # Premium: 2-Pass (Translate -> Refine)
                # Economy: 1-Pass
                translations = _translate_batch_deepseek(
                    texts, source_lang, target_lang, api_key, 
                    global_context=system_context + glossary_text, 
                    prev_context=last_sentence_context,
                    is_premium=(fidelity_mode == 'premium')
                )
                
                for j, sub in enumerate(batch):
                    if j < len(translations):
                        sub.text = translations[j]
                    pbar.update(1)
                    
                if translations:
                    last_sentence_context = translations[-1]
                    
            except Exception as e:
                print_warning(f"Batch failed: {str(e)}")
                pbar.update(len(batch))
                
    # SubtitleShield Logic (AI Quality Control)
    from .subtitle_shield import subtitle_shield_review
    print()
    subs, _ = subtitle_shield_review(
        subs, source_lang, target_lang, api_key,
        video_title=video_title, original_subs=original_subs,
        ai_context=ai_context
    )
    
    return subs

def _get_video_context(subs, sample_size=5):
    """Get summarized context"""
    sample_texts = []
    total = len(subs)
    indices = [i for i in range(min(sample_size, total))]
    if total > 20: indices.extend([total // 2, (total // 2) + 1])
    
    for i in indices:
        if i < total: sample_texts.append(subs[i].text)
    return " ".join(sample_texts)

def _translate_batch_deepseek(texts, source_lang, target_lang, api_key, global_context="", prev_context="", is_premium=False):
    """Request batch translation from DeepSeek (1-Pass Economy or 2-Pass Premium)"""
    from openai import OpenAI
    import re
    
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=90.0)
        
        numbered_texts = "\n".join([f"{i+1}. {text}" for i, text in enumerate(texts)])
        context_instruction = ""
        if global_context: context_instruction += f"\n[Global Video Context]: {global_context}"
        if prev_context: context_instruction += f"\n[Previous Sentence]: ...{prev_context}"
        
        # --- PASS 1: Initial Translation ---
        system_prompt = f"""You are a professional subtitle translator.
Target: {target_lang}. Style: Natural, conversational.
RULES:
1. Translate LINE-BY-LINE.
2. Output numbered list exactly like input.
3. No explanations.
4. If you detect anomalies (hallucinations/spam), output: [SKIP]"""

        user_prompt = f"""Translate {len(texts)} lines.
{context_instruction}
Input:
{numbered_texts}
"""
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1, max_tokens=4000
        )
        
        raw_translation = response.choices[0].message.content.strip()
        
        # --- PASS 2: Critical Refinement (Premium Only) ---
        if is_premium:
            refine_system = (
                f"You are a Quality Assurance Editor for subtitles ({target_lang}).\n"
                f"Your job: Fix grammar, improve flow, and ensure consistent tone.\n"
                f"Context: {global_context}\n"
                f"RULES:\n1. Output ONLY the refined numbered list.\n2. Do NOT change line count."
            )
            
            refine_user = (
                f"Original Source:\n{numbered_texts}\n\n"
                f"Draft Translation:\n{raw_translation}\n\n"
                f"Task: Polish and refine the translation to be perfect native {target_lang}."
            )
            
            try:
                response_refine = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": refine_system},
                        {"role": "user", "content": refine_user}
                    ],
                    temperature=0.1, max_tokens=4000
                )
                raw_translation = response_refine.choices[0].message.content.strip()
            except Exception:
                pass # Fallback to draft if refinement fails

        # --- Parse Result ---
        translations = []
        for line in raw_translation.split('\n'):
            line = line.strip()
            if not line: continue
            
            match = re.match(r'^\d+[\.\)\s]+(.*)', line)
            if match:
                translation = match.group(1).strip()
                if translation.upper() not in ["[SKIP]", "SKIP"]:
                    translations.append(translation)
                else:
                    translations.append("") # Mark as empty to preserve index
                    
        # Handling count mismatches
        if len(translations) == 0: return texts
        
        return translations
        
    except Exception:
        return texts
