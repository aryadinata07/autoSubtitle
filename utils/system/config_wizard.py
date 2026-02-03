"""Interactive Configuration Wizard"""
import os
from utils.system.ui import console, print_success, print_header
from core.config import save_config, load_config

def menu_api_key():
    """Menu for API Key"""
    console.print("\n[bold cyan]🔑 DeepSeek API Key Configuration[/bold cyan]")
    console.print("The API Key is required for high-quality translation.")
    console.print("It will be saved securely in your .env file.")
    
    current_key = load_config().get('DEEPSEEK_API_KEY')
    if current_key:
        console.print(f"\nCurrent Key: [green]{current_key[:6]}...{current_key[-4:]}[/green]")
        console.print("Leave empty to keep current key, or enter 'DELETE' to remove.")
    
    new_key = input("\nEnter API Key: ").strip()
    
    if new_key == "DELETE":
        save_config('DEEPSEEK_API_KEY', '')
        print_success("API Key removed.")
    elif new_key:
        save_config('DEEPSEEK_API_KEY', new_key)
        print_success("API Key saved successfully!")
    else:
        console.print("[yellow]No change made.[/yellow]")

def menu_whisper_model():
    """Menu for Whisper Model"""
    console.print("\n[bold cyan]🧠 Whisper Model Preference[/bold cyan]")
    console.print("Choose the default model size (larger = clearer but slower).")
    
    models = [
        ('tiny', 'Fastest, lowest accuracy'),
        ('base', 'Balanced (Standard)'),
        ('small', 'Good accuracy'),
        ('medium', 'Better accuracy'),
        ('large-v3', 'Best accuracy (Slowest)'),
        ('distil-medium.en', 'Fast & Accurate (English only)'),
        ('distil-large-v3', 'Best & Fast (English only)'),
    ]
    
    for i, (val, desc) in enumerate(models, 1):
        console.print(f"[{i}] {val.ljust(15)} : {desc}")
        
    choice_idx = input("\nChoice (1-7): ").strip()
    
    if choice_idx.isdigit() and 1 <= int(choice_idx) <= len(models):
        selected_model = models[int(choice_idx)-1][0]
        save_config('DEFAULT_MODEL', selected_model)  # Note: logic might use WHISPER_MODE in config.py, syncing key
        # Also saving to WHISPER_MODE to be safe if that's what core/config uses
        save_config('WHISPER_MODE', selected_model)
        print_success(f"Default model set to: {selected_model}")
    else:
        console.print("[yellow]Invalid choice. No change made.[/yellow]")

def menu_turbo_mode():
    """Menu for Turbo Mode"""
    console.print("\n[bold cyan]⚡ Turbo Mode Preference[/bold cyan]")
    console.print("Should Turbo Mode (greedy search) be used by default?")
    
    options = [
        ('true', 'Always ON (Fastest)'),
        ('false', 'Always OFF (Most Accurate)'),
        ('ask', 'Ask Every Time (Flexible)'),
    ]
    
    for i, (val, desc) in enumerate(options, 1):
        console.print(f"[{i}] {desc}")
        
    choice = input("\nChoice: ").strip()
    if choice == '1':
        save_config('TURBO_MODE', 'true')
        print_success("Turbo Mode set to: Always ON")
    elif choice == '2':
        save_config('TURBO_MODE', 'false')
        print_success("Turbo Mode set to: Always OFF")
    elif choice == '3':
        save_config('TURBO_MODE', 'ask')
        print_success("Turbo Mode set to: Ask Every Time")

def menu_embedding_method():
    """Menu for Embedding Method"""
    console.print("\n[bold cyan]🎞️ Embedding Method Preference[/bold cyan]")
    console.print("Choose how subtitles should be added to the video.")
    
    options = [
        ('soft', 'Soft Subtitle (Instant, Toggleable)'),
        ('fast', 'Hardsub (Fast CPU Encoding)'),
        ('gpu',  'Hardsub (GPU Accelerated)'),
        ('ask',  'Ask Every Time (Flexible)'),
    ]
    
    for i, (val, desc) in enumerate(options, 1):
        console.print(f"[{i}] {desc}")
        
    choice = input("\nChoice: ").strip()
    if choice == '1':
        save_config('EMBEDDING_METHOD', 'soft')
        print_success("Embedding set to: Soft Subtitle")
    elif choice == '2':
        save_config('EMBEDDING_METHOD', 'fast')
        print_success("Embedding set to: Hardsub (Fast)")
    elif choice == '3':
        save_config('EMBEDDING_METHOD', 'gpu')
        print_success("Embedding set to: Hardsub (GPU)")
    elif choice == '4':
        save_config('EMBEDDING_METHOD', 'ask')
        print_success("Embedding set to: Ask Every Time")
    else:
        console.print("[yellow]Invalid choice. No change made.[/yellow]")

def menu_subtitle_style():
    """Menu for Subtitle Styling"""
    console.print("\n[bold cyan]🎨 Subtitle Style Configuration[/bold cyan]")
    
    current_style = load_config().get('STYLE_PRESET', 'custom').upper()
    console.print(f"Current Preset: [green]{current_style}[/green]")
    
    console.print("\n[bold white]Select Style Preset:[/bold white]")
    console.print("[1] Default (Balanced, Size 20, White)")
    console.print("[2] Cinematic (Small, Size 14, Yellow)")
    console.print("[3] YouTuber (Large, Size 24, White, Thick Outline)")
    console.print("[4] Custom (Configure manually)")
    
    choice = input("\nChoice: ").strip()
    
    if choice == '1':
        save_config('STYLE_PRESET', 'default')
        save_config('SUB_FONT_SIZE', '20')
        save_config('SUB_FONT_COLOR', '&HFFFFFF')
        save_config('SUB_OUTLINE_WIDTH', '2')
        save_config('SUB_POSITION', 'bottom')
        print_success("Style set to: Default")
        
    elif choice == '2':
        save_config('STYLE_PRESET', 'cinematic')
        save_config('SUB_FONT_SIZE', '14')
        save_config('SUB_FONT_COLOR', '&H00FFFF') # Yellowish
        save_config('SUB_OUTLINE_WIDTH', '1')
        save_config('SUB_POSITION', 'bottom')
        print_success("Style set to: Cinematic")
        
    elif choice == '3':
        save_config('STYLE_PRESET', 'youtuber')
        save_config('SUB_FONT_SIZE', '24')
        save_config('SUB_FONT_COLOR', '&HFFFFFF')
        save_config('SUB_OUTLINE_WIDTH', '4')
        save_config('SUB_POSITION', 'bottom')
        print_success("Style set to: YouTuber")
        
    elif choice == '4':
        save_config('STYLE_PRESET', 'custom')
        console.print("\n[bold cyan]🔧 Custom Configuration:[/bold cyan]")
        
        # Font Size
        size = input("Font Size (default 20): ").strip()
        if size.isdigit(): save_config('SUB_FONT_SIZE', size)
        
        # Color
        console.print("Color format: &HBBGGRR (Hex Blue-Green-Red)")
        console.print("Examples: White=&HFFFFFF, Yellow=&H00FFFF, Red=&H0000FF")
        color = input("Font Color (default &HFFFFFF): ").strip()
        if color.startswith('&H'): save_config('SUB_FONT_COLOR', color)
        
        # Outline
        outline = input("Outline Width (default 2): ").strip()
        if outline.isdigit(): save_config('SUB_OUTLINE_WIDTH', outline)
        
        print_success("Custom style saved!")
        
    else:
        console.print("[yellow]Invalid choice.[/yellow]")

def menu_target_language():
    """Menu for Default Target Language"""
    console.print("\n[bold cyan]🌐 Target Language Configuration[/bold cyan]")
    
    current = load_config().get('TARGET_LANGUAGE', 'ask')
    if current == 'ask': current_display = "Ask every time (Interactive)"
    else: current_display = current.upper()
    
    console.print(f"Current Setting: [green]{current_display}[/green]")
    
    console.print("\n[bold white]Options:[/bold white]")
    console.print("[1] Ask for each video (Default)")
    console.print("[2] Indonesian (id)")
    console.print("[3] English (en)")
    console.print("[4] Japanese (ja)")
    console.print("[5] Korean (ko)")
    console.print("[6] Spanish (es)")
    console.print("[7] French (fr)")
    console.print("[8] German (de)")
    console.print("[9] Custom Code (e.g. ru, zh, it)")
    
    choice = input("\nChoice: ").strip()
    
    if choice == '1':
        save_config('TARGET_LANGUAGE', 'ask')
        print_success("Mode set to: Ask every time")
    elif choice == '2': save_config('TARGET_LANGUAGE', 'id'); print_success("Target set to: Indonesian")
    elif choice == '3': save_config('TARGET_LANGUAGE', 'en'); print_success("Target set to: English")
    elif choice == '4': save_config('TARGET_LANGUAGE', 'ja'); print_success("Target set to: Japanese")
    elif choice == '5': save_config('TARGET_LANGUAGE', 'ko'); print_success("Target set to: Korean")
    elif choice == '6': save_config('TARGET_LANGUAGE', 'es'); print_success("Target set to: Spanish")
    elif choice == '7': save_config('TARGET_LANGUAGE', 'fr'); print_success("Target set to: French")
    elif choice == '8': save_config('TARGET_LANGUAGE', 'de'); print_success("Target set to: German")
    elif choice == '9':
        code = input("Enter 2-letter language code (e.g. ru): ").strip().lower()
        if len(code) == 2:
            save_config('TARGET_LANGUAGE', code)
            print_success(f"Target set to: {code}")
        else:
            console.print("[red]Invalid code format.[/red]")
    else:
        console.print("[yellow]Invalid choice.[/yellow]")

def menu_translation_method():
    """Menu for Translation Method (Provider)"""
    console.print("\n[bold cyan]🌐 Translation Service Provider[/bold cyan]")
    
    current = load_config().get('TRANSLATION_METHOD', 'deepseek').upper()
    console.print(f"Current Provider: [green]{current}[/green]")
    
    console.print("\n[bold white]Options:[/bold white]")
    console.print("[1] DeepSeek AI (Recommended)")
    console.print("    [dim]- Best quality, Context-aware, Supports Glossary[/dim]")
    console.print("    [dim]- Requires API Key (Paid)[/dim]")
    
    console.print("\n[2] Google Translate (Free)")
    console.print("    [dim]- Completely Free, No Setup required[/dim]")
    console.print("    [dim]- Good speed, but translation can be literal/stiff[/dim]")
    console.print("    [dim]- Does NOT support Context or Glossary[/dim]")
    
    choice = input("\nChoice: ").strip()
    
    if choice == '1':
        save_config('TRANSLATION_METHOD', 'deepseek')
        print_success("Provider set to: DeepSeek AI")
        # Check if key needs to be set
        if not load_config().get('DEEPSEEK_API_KEY'):
            console.print("[yellow]Tip: Don't forget to configure your API Key![/yellow]")
            
    elif choice == '2':
        save_config('TRANSLATION_METHOD', 'google')
        print_success("Provider set to: Google Translate (Free)")
    else:
        console.print("[yellow]Invalid choice.[/yellow]")

def menu_fidelity_mode():
    """Menu for Fidelity Mode (Economy vs Premium)"""
    console.print("\n[bold cyan]💎 Quality & Fidelity Configuration[/bold cyan]")
    console.print("Choose the balance between Cost (Credits) and Quality.")
    
    current = load_config().get('FIDELITY_MODE', 'economy').upper()
    console.print(f"Current Mode: [green]{current}[/green]")
    
    console.print("\n[bold white]Options:[/bold white]")
    console.print("[1] Economy (Default)")
    console.print("    [dim]- Fast, Single-Pass Translation[/dim]")
    console.print("    [dim]- Best for Vlogs, Gaming, Casual content[/dim]")
    console.print("    [dim]- Low Token Usage (Cheaper)[/dim]")
    
    console.print("\n[2] Premium (High Quality)")
    console.print("    [dim]- 2-Pass Translation (Context Analysis + Grammar Refine)[/dim]")
    console.print("    [dim]- Learns context from video topic first[/dim]")
    console.print("    [dim]- Best for Education, Professional, Complex topics[/dim]")
    console.print("    [dim]- Uses ~2x Token Credits[/dim]")
    
    choice = input("\nChoice: ").strip()
    
    if choice == '1':
        save_config('FIDELITY_MODE', 'economy')
        print_success("Mode set to: Economy")
    elif choice == '2':
        save_config('FIDELITY_MODE', 'premium')
        print_success("Mode set to: Premium (Context Aware)")
    else:
        console.print("[yellow]Invalid choice.[/yellow]")

def run_wizard():
    """Run the main wizard loop"""
    while True:
        # refresh config
        config = load_config()
        
        print_header("⚙️  Configuration Wizard")
        
        # Status Summary
        console.print("[bold white]Current Settings:[/bold white]")
        
        key_status = "[green]Set[/green]" if config.get('DEEPSEEK_API_KEY') else "[red]Not Set[/red]"
        console.print(f"1. DeepSeek API Key : {key_status}")
        
        def_model = config.get('WHISPER_MODE', 'base')
        console.print(f"2. Default Model    : [cyan]{def_model}[/cyan]")
        
        turbo = config.get('TURBO_MODE', 'ask')
        turbo_display = "Ask" if turbo == 'ask' else ("ON" if turbo == 'true' else "OFF")
        console.print(f"3. Turbo Mode       : [cyan]{turbo_display}[/cyan]")
        
        embed = config.get('EMBEDDING_METHOD', 'ask')
        console.print(f"4. Embedding Method : [cyan]{embed.upper()}[/cyan]")
        
        style = config.get('STYLE_PRESET', 'default')
        console.print(f"5. Subtitle Style   : [cyan]{style.upper()}[/cyan]")
        
        fidelity = config.get('FIDELITY_MODE', 'economy')
        console.print(f"6. Quality Mode     : [cyan]{fidelity.upper()}[/cyan]")
        
        provider = config.get('TRANSLATION_METHOD', 'DeepSeek' if config.get('DEEPSEEK_API_KEY') else 'Google')
        console.print(f"7. Provider         : [cyan]{provider.upper()}[/cyan]")
        
        target_lang = config.get('TARGET_LANGUAGE', 'ask')
        console.print(f"8. Target Language  : [cyan]{target_lang.upper() if target_lang != 'ask' else 'Interactive'}[/cyan]")
        
        console.print("\n[bold white]Actions:[/bold white]")
        console.print("[1] Configure API Key")
        console.print("[2] Configure Model")
        console.print("[3] Configure Turbo Mode")
        console.print("[4] Configure Embedding Method")
        console.print("[5] Configure Subtitle Style")
        console.print("[6] Configure Quality (Economy/Premium)")
        console.print("[7] Configure Translation Provider (Google/DeepSeek)")
        console.print("[8] Configure Default Target Language")
        console.print("[9] Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            menu_api_key()
        elif choice == '2':
            menu_whisper_model()
        elif choice == '3':
            menu_turbo_mode()
        elif choice == '4':
            menu_embedding_method()
        elif choice == '5':
            menu_subtitle_style()
        elif choice == '6':
            menu_fidelity_mode()
        elif choice == '7':
            menu_translation_method()
        elif choice == '8':
            menu_target_language()
        elif choice == '9':
            console.print("\n[green]Configuration saved. Exiting wizard.[/green]")
            break
        else:
            console.print("\n[red]Invalid option.[/red]")

if __name__ == "__main__":
    run_wizard()
