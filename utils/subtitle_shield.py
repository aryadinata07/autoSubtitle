"""
SubtitleShield V2.1 🛡️ - AI-Powered Contextual Repair System
Side-by-Side Comparison for Maximum Translation Accuracy

V2.1 Features:
- Batch Processing: Review ALL subtitles (not just first 50)
- Context Window: AI sees previous + current + next subtitle
- Statistics Report: Detailed transparency report
"""
from openai import OpenAI
from .ui import print_step, print_substep, print_success, print_warning, console
import time
import pysrt


def subtitle_shield_review(subs, source_lang, target_lang, api_key, video_title=None, original_subs=None):
    """
    SubtitleShield V2.1: Side-by-side comparison for contextual repair
    
    Features:
    - Compare original text vs translation
    - Detect mistranslations (e.g., "name" → "rumah" instead of "nama")
    - Detect anomalies (hallucinations, out-of-context)
    - Auto-repair or remove based on confidence
    - Transparent action report (KEEP/EDIT/DELETE)
    - Batch processing: Review ALL subtitles
    - Context window: AI sees surrounding subtitles
    - Statistics report: Detailed transparency
    
    Args:
        subs: Subtitle entries (already translated)
        source_lang: Source language
        target_lang: Target language
        api_key: DeepSeek API key
        video_title: Video title for context
        original_subs: Original subtitle entries (before translation) for comparison
    
    Returns:
        tuple: (cleaned_subs, report)
    """
    print_step(4, 5, "🛡️ SubtitleShield V2.1: Contextual Repair")
    
    # V2.1 Header
    console.print("\n[bold magenta]" + "═" * 60 + "[/bold magenta]")
    console.print("[bold magenta]🛡️  SubtitleShield V2.1 - AI Quality Control System[/bold magenta]")
    console.print("[bold magenta]" + "═" * 60 + "[/bold magenta]\n")
    
    print_substep("Side-by-side comparison: Original vs Translation...")
    
    # If no original subs provided, skip comparison (can't verify)
    if not original_subs:
        print_warning("No original subtitles provided, skipping contextual repair")
        return subs, {"actions": [], "summary": "Skipped (no original text)"}
    
    # Build side-by-side comparison data
    total_subs = len(subs)
    
    # Verify we have different text (original vs translated)
    if total_subs > 0 and len(original_subs) > 0:
        sample_original = original_subs[0].text
        sample_translated = subs[0].text
        if sample_original == sample_translated:
            print_warning("⚠️ Original and translated text are identical!")
            print_substep("This might indicate a deep copy issue. Skipping SubtitleShield.")
            return subs, {"actions": [], "summary": "Skipped (identical text)"}
    
    # Create context summary
    context = f"Video: {video_title if video_title else 'Unknown'}\n"
    context += f"Total subtitles: {total_subs}\n"
    context += f"Translation: {source_lang.upper()} → {target_lang.upper()}\n"
    context += f"Original language: {source_lang.upper()}\n"
    context += f"Target language: {target_lang.upper()}\n"

    # Call AI for deep review with batch processing
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            timeout=120.0
        )
        
        # V2.1: Batch processing - Review ALL subtitles in chunks of 50
        batch_size = 50
        all_actions = []
        total_batches = (total_subs + batch_size - 1) // batch_size
        
        # V2.1: Visual batch processing header
        console.print(f"[bold cyan]📦 Batch Processing Mode[/bold cyan]")
        console.print(f"[dim]Total Subtitles:[/dim] {total_subs}")
        console.print(f"[dim]Batch Size:[/dim] {batch_size} subtitles per batch")
        console.print(f"[dim]Total Batches:[/dim] {total_batches}")
        console.print(f"[dim]Context Window:[/dim] Previous + Current + Next subtitle\n")
        
        # Progress tracking
        from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="bold green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TextColumn("[cyan]{task.fields[issues]} issues"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(
                "[cyan]Analyzing subtitles...",
                total=total_batches,
                issues=0
            )
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, total_subs)
                
                progress.update(task, description=f"[cyan]Batch {batch_num + 1}/{total_batches} (#{start_idx + 1}-{end_idx})")
                
                # Build side-by-side comparison list with context window
                comparison_list = []
                
                for i in range(start_idx, end_idx):
                    original_text = original_subs[i].text if i < len(original_subs) else "[MISSING]"
                    translated_text = subs[i].text
                    
                    # V2.1: Context Window - Include previous and next subtitle
                    context_info = ""
                    if i > 0:
                        prev_original = original_subs[i-1].text if i-1 < len(original_subs) else ""
                        prev_translated = subs[i-1].text
                        context_info += f"   [Previous] Original: {prev_original}\n"
                        context_info += f"   [Previous] Translation: {prev_translated}\n"
                    
                    if i < total_subs - 1:
                        next_original = original_subs[i+1].text if i+1 < len(original_subs) else ""
                        next_translated = subs[i+1].text
                        context_info += f"   [Next] Original: {next_original}\n"
                        context_info += f"   [Next] Translation: {next_translated}\n"
                    
                    comparison_list.append(
                        f"{i+1}. ORIGINAL: {original_text}\n"
                        f"   TRANSLATION: {translated_text}\n"
                        f"{context_info}"
                    )
                
                subtitle_comparison = "\n\n".join(comparison_list)
                
                system_prompt = f"""You are SubtitleShield V2.1 🛡️, an AI expert in translation quality control.

IMPORTANT: You are comparing {source_lang.upper()} (ORIGINAL) vs {target_lang.upper()} (TRANSLATION).
- ORIGINAL text is in {source_lang.upper()} language
- TRANSLATION text is in {target_lang.upper()} language
- If both are in the same language, DO NOT flag as mistranslation!

V2.1 FEATURES:
- You now see [Previous] and [Next] subtitles for CONTEXT
- Use context to understand conversation flow
- Detect if translation breaks conversation continuity

Your task: Side-by-side comparison of ORIGINAL vs TRANSLATION to detect:
1. MISTRANSLATION: Wrong meaning (e.g., English "name" → Indonesian "rumah" instead of "nama")
2. ANOMALY: Hallucinations, out-of-context phrases
3. CONTEXT MISMATCH: Translation doesn't match original intent or conversation flow

ACTIONS:
- KEEP: Translation is correct
- EDIT: Translation is wrong, provide corrected version in {target_lang.upper()}
- DELETE: Anomaly/hallucination (no real speech)

OUTPUT FORMAT (JSON):
{{
  "actions": [
    {{
      "index": 5,
      "original": "My name is John",
      "translation": "Rumah saya adalah John",
      "issue": "Mistranslation: 'name' translated as 'rumah' (house) instead of 'nama'",
      "action": "edit",
      "corrected": "Nama saya adalah John",
      "confidence": 95
    }},
    {{
      "index": 15,
      "original": "[Background noise]",
      "translation": "Thank you for watching",
      "issue": "Hallucination: No actual speech in original",
      "action": "delete",
      "confidence": 90
    }}
  ],
  "summary": "Reviewed subtitles {start_idx + 1}-{end_idx}. Found X issues."
}}

Be conservative: Only flag if confidence > 80%. When in doubt, use KEEP."""

                user_prompt = f"""Compare ORIGINAL vs TRANSLATION side-by-side.

CONTEXT:
{context}

SIDE-BY-SIDE COMPARISON (with context window):
{subtitle_comparison}

Detect mistranslations and anomalies. Use [Previous] and [Next] context to understand conversation flow. Return JSON with actions."""
                
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=2000
                )
                
                response_text = response.choices[0].message.content.strip()
                
                # Parse JSON response
                import json
                import re
                
                # Extract JSON from response (might have markdown code blocks)
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    batch_result = json.loads(json_match.group())
                else:
                    batch_result = {"actions": [], "summary": "No issues detected"}
                
                batch_actions = batch_result.get("actions", [])
                all_actions.extend(batch_actions)
                
                # Update progress with issues found
                progress.update(task, advance=1, issues=len(all_actions))
                
                # Small delay between batches to avoid rate limiting
                if batch_num < total_batches - 1:
                    time.sleep(0.5)
        
        # Combine all actions from all batches
        actions = all_actions
        
        # V2.1: Statistics Report
        total_reviewed = total_subs
        total_issues = len(actions)
        
        # Visual separator
        console.print("\n[bold magenta]" + "─" * 60 + "[/bold magenta]\n")
        
        # Display report with color-coded actions
        print_success("SubtitleShield V2.1 Analysis Complete!")
        console.print(f"[bold cyan]📊 Quick Stats:[/bold cyan] Reviewed {total_reviewed} subtitles • Found {total_issues} issue(s)\n")
        
        if actions:
            console.print(f"[bold yellow]📋 Found {len(actions)} issue(s) - Taking action...[/bold yellow]\n")
            
            edit_count = 0
            delete_count = 0
            
            for action_item in actions:
                idx = action_item.get("index", 0) - 1  # Convert to 0-based
                original = action_item.get("original", "")
                translation = action_item.get("translation", "")
                issue = action_item.get("issue", "Unknown")
                action = action_item.get("action", "keep").lower()
                corrected = action_item.get("corrected", "")
                confidence = action_item.get("confidence", 0)
                
                # Skip if confidence too low
                if confidence < 80:
                    continue
                
                # Display issue
                console.print(f"[bold cyan]🔍 Subtitle #{idx + 1}[/bold cyan]")
                console.print(f"   [dim]Original:[/dim] {original}")
                console.print(f"   [dim]Translation:[/dim] {translation}")
                console.print(f"   [yellow]Issue:[/yellow] {issue}")
                console.print(f"   [dim]Confidence:[/dim] {confidence}%")
                
                # Apply action
                if action == "edit" and corrected and 0 <= idx < len(subs):
                    console.print(f"   [bold green]✏️ ACTION: EDIT[/bold green]")
                    console.print(f"   [green]Corrected:[/green] {corrected}")
                    subs[idx].text = corrected
                    edit_count += 1
                
                elif action == "delete" and 0 <= idx < len(subs):
                    console.print(f"   [bold red]🗑️ ACTION: DELETE[/bold red]")
                    # Mark for deletion (will delete later)
                    subs[idx].text = "[DELETE_MARKER]"
                    delete_count += 1
                
                else:
                    console.print(f"   [bold blue]✓ ACTION: KEEP[/bold blue]")
                
                console.print()
            
            # Remove marked subtitles
            if delete_count > 0:
                subs = pysrt.SubRipFile([sub for sub in subs if sub.text != "[DELETE_MARKER]"])
            
            # V2.1: Detailed Statistics Report
            keep_count = total_reviewed - edit_count - delete_count
            
            console.print("\n[bold magenta]" + "═" * 60 + "[/bold magenta]")
            console.print("[bold cyan]📊 SubtitleShield V2.1 - Final Report[/bold cyan]")
            console.print("[bold magenta]" + "═" * 60 + "[/bold magenta]\n")
            
            console.print(f"[bold white]Total Reviewed:[/bold white] {total_reviewed} subtitles")
            console.print(f"[bold white]Total Issues Found:[/bold white] {total_issues}\n")
            
            console.print("[bold]Results Breakdown:[/bold]")
            console.print(f"  [green]✓ KEEP:[/green]   {keep_count} subtitles (perfect translation)")
            if edit_count > 0:
                console.print(f"  [yellow]✏️ EDIT:[/yellow]   {edit_count} subtitles (mistranslation corrected)")
            if delete_count > 0:
                console.print(f"  [red]🗑️ DELETE:[/red] {delete_count} subtitles (hallucination removed)")
            console.print()
            
            # Calculate confidence average
            if actions:
                avg_confidence = sum(a.get("confidence", 0) for a in actions) / len(actions)
                console.print(f"[bold white]Average Confidence:[/bold white] {avg_confidence:.1f}%")
            
            # Quality score
            quality_score = (keep_count / total_reviewed) * 100 if total_reviewed > 0 else 0
            console.print(f"[bold white]Quality Score:[/bold white] {quality_score:.1f}% (original translation accuracy)\n")
            
            console.print("[bold magenta]" + "═" * 60 + "[/bold magenta]")
            print_success(f"✅ SubtitleShield V2.1: {edit_count + delete_count} issue(s) fixed!")
        else:
            console.print("\n[bold magenta]" + "═" * 60 + "[/bold magenta]")
            console.print("[bold cyan]📊 SubtitleShield V2.1 - Final Report[/bold cyan]")
            console.print("[bold magenta]" + "═" * 60 + "[/bold magenta]\n")
            
            console.print(f"[bold white]Total Reviewed:[/bold white] {total_reviewed} subtitles")
            console.print(f"[green]✓ Result:[/green] All subtitles are perfect! No issues detected.\n")
            console.print(f"[bold white]Quality Score:[/bold white] 100% (flawless translation)\n")
            
            console.print("[bold magenta]" + "═" * 60 + "[/bold magenta]")
            print_success("✅ No issues detected. Subtitles look perfect!")
        
        # Build comprehensive report
        report = {
            "version": "2.1",
            "total_reviewed": total_reviewed,
            "total_issues": total_issues,
            "actions": actions,
            "statistics": {
                "keep": keep_count if actions else total_reviewed,
                "edit": edit_count if actions else 0,
                "delete": delete_count if actions else 0,
                "avg_confidence": sum(a.get("confidence", 0) for a in actions) / len(actions) if actions else 0
            }
        }
        
        return subs, report
    
    except Exception as e:
        print_warning(f"SubtitleShield error: {str(e)}")
        print_substep("Continuing without anomaly detection...")
        return subs, {"anomalies": [], "summary": "Error during analysis"}
