"""UI utilities for terminal display"""
from colorama import Fore, Style, init
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

# Initialize colorama
init(autoreset=True)

console = Console()

# Import logger
try:
    from core.logger import log
except ImportError:
    # Fallback if core.logger not available yet (during dev)
    import logging
    log = logging.getLogger("AutoSubtitle")


def print_header(title):
    """Print styled header"""
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold white]{title.center(60)}[/bold white]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]")


def print_info(label, value):
    """Print info line"""
    console.print(f"[cyan]{label}:[/cyan] [white]{value}[/white]")
    log.info(f"{label}: {value}")


def print_step(step, total, message):
    """Print step indicator"""
    console.print(f"\n[bold yellow][{step}/{total}][/bold yellow] [bold white]{message}[/bold white]")
    log.info(f"STEP [{step}/{total}] {message}")


def print_substep(message):
    """Print substep message"""
    console.print(f"      [dim]{message}[/dim]")
    log.debug(f"  -> {message}")


def print_success(message):
    """Print success message"""
    console.print(f"      [bold green]✓[/bold green] [green]{message}[/green]")
    log.info(f"SUCCESS: {message}")


def print_warning(message):
    """Print warning message"""
    console.print(f"      [bold yellow]⚠[/bold yellow] [yellow]{message}[/yellow]")
    log.warning(message)


def print_error(message):
    """Print error message"""
    console.print(f"      [bold red]❌[/bold red] [red]{message}[/red]")
    log.error(message)


def print_summary(data):
    """Print final summary"""
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold green]✓ SUBTITLE GENERATION COMPLETE![/bold green]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]")
    
    for key, value in data.items():
        console.print(f"  [cyan]{key}:[/cyan] [white]{value}[/white]")
    
    console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")


def create_progress():
    """Create rich progress bar"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console
    )


def ask_question(question):
    """Ask user a question with styled prompt"""
    while True:
        console.print(f"\n[bold yellow]?[/bold yellow] [white]{question}[/white] ", end="")
        response = input().strip().lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print_warning("Please enter 'y' or 'n'")


def ask_turbo_mode():
    """Ask user if they want to use turbo mode"""
    console.print("\n[bold cyan]Choose Transcription Mode:[/bold cyan]")
    
    console.print("\n[bold green]1. Standard Mode (Default - Accurate)[/bold green]")
    console.print("   [green]Pros:[/green]")
    console.print("   [dim]✓ Maximum accuracy (beam search)[/dim]")
    console.print("   [dim]✓ Best for noisy/challenging audio[/dim]")
    console.print("   [dim]✓ Explores 5 possible transcriptions[/dim]")
    console.print("   [red]Cons:[/red]")
    console.print("   [dim]✗ Slower processing time[/dim]")
    
    console.print("\n[bold yellow]2. Turbo Mode (Recommended for Clear Audio)[/bold yellow]")
    console.print("   [green]Pros:[/green]")
    console.print("   [dim]✓ 3-6x faster transcription[/dim]")
    console.print("   [dim]✓ Greedy search (instant decisions)[/dim]")
    console.print("   [dim]✓ 99% same accuracy for clear audio[/dim]")
    console.print("   [dim]✓ Perfect for YouTube/Podcast/TEDx[/dim]")
    console.print("   [red]Cons:[/red]")
    console.print("   [dim]✗ Slightly less accurate for very noisy audio[/dim]")
    
    console.print("\n[dim italic]💡 Tip: You can set a permanent default for this in the config wizard.[/dim italic]")
    console.print("[dim italic]   Run: python generate_subtitle.py --configure[/dim italic]")
    
    while True:
        console.print("\n[bold yellow]?[/bold yellow] [white]Choose option (1 or 2, default=1):[/white] ", end="")
        choice = input().strip()
        if choice == "" or choice == "1":
            return False
        elif choice == "2":
            return True
        else:
            console.print("[yellow]Please enter 1 or 2 (or press Enter for default)[/yellow]")


def ask_deepseek():
    """Ask user if they want to use DeepSeek for translation"""
    console.print("\n[bold cyan]Choose Translation Method:[/bold cyan]")
    
    console.print("\n[bold green]1. DeepSeek AI (Default - Recommended)[/bold green]")
    console.print("   [green]Pros:[/green]")
    console.print("   [dim]✓ More natural and conversational[/dim]")
    console.print("   [dim]✓ Context-aware (understands video topic)[/dim]")
    console.print("   [dim]✓ Batch processing (10x faster)[/dim]")
    console.print("   [dim]✓ Better translation quality[/dim]")
    console.print("   [red]Cons:[/red]")
    console.print("   [dim]✗ Requires API key (but very cheap)[/dim]")
    
    console.print("\n[bold yellow]2. Google Translate (Free Fallback)[/bold yellow]")
    console.print("   [green]Pros:[/green]")
    console.print("   [dim]✓ Free, no API key required[/dim]")
    console.print("   [dim]✓ Fast and reliable[/dim]")
    console.print("   [dim]✓ Good for basic translation[/dim]")
    console.print("   [red]Cons:[/red]")
    console.print("   [dim]✗ Sometimes too literal/stiff[/dim]")
    console.print("   [dim]✗ Not context-aware[/dim]")
    
    while True:
        console.print("\n[bold yellow]?[/bold yellow] [white]Choose option (1 or 2, default=1):[/white] ", end="")
        choice = input().strip()
        if choice == "" or choice == "1":
            return True
        elif choice == "2":
            return False
        else:
            console.print("[yellow]Please enter 1 or 2 (or press Enter for default)[/yellow]")


def ask_embedding_method():
    """Ask user for embedding method"""
    from utils.media.media import check_gpu_available
    
    # Check GPU availability once
    gpu_available = check_gpu_available()
    
    # Check GPU availability once
    gpu_available = check_gpu_available()
    
    while True:
        console.print("\n[bold cyan]Choose Embedding Method:[/bold cyan]")
        console.print("[dim italic]💡 Tip: Set default via 'python generate_subtitle.py --configure'[/dim italic]")
        
        console.print("\n[bold green]1. Soft Subtitle - INSTANT ⚡ (Default - Recommended)[/bold green]")
        console.print("   [green]Pros:[/green]")
        console.print("   [dim]✓ INSTANT (1-5 seconds only!)[/dim]")
        console.print("   [dim]✓ No quality loss (stream copy)[/dim]")
        console.print("   [dim]✓ Subtitle can be toggled On/Off[/dim]")
        console.print("   [dim]✓ Perfect for YouTube, PC playback[/dim]")
        console.print("   [red]Cons:[/red]")
        console.print("   [dim]✗ Need to enable in player (VLC: press V)[/dim]")
        console.print("   [dim]✗ Not visible on Instagram/TikTok[/dim]")
        
        console.print("\n[bold yellow]2. Hardsub - Fast Encoding[/bold yellow]")
        console.print("   [green]Pros:[/green]")
        console.print("   [dim]✓ 3-4x faster (~3-5 min for 17 min video)[/dim]")
        console.print("   [dim]✓ Works on all platforms (Instagram, TikTok)[/dim]")
        console.print("   [dim]✓ Good quality[/dim]")
        console.print("   [dim]✓ Always visible (no need to enable)[/dim]")
        console.print("   [red]Cons:[/red]")
        console.print("   [dim]✗ Requires re-encoding (takes time)[/dim]")
        
        # Show GPU option only if available
        if gpu_available:
            console.print("\n[bold magenta]3. Hardsub - GPU Accelerated ✓[/bold magenta]")
            console.print("   [green]Pros:[/green]")
            console.print("   [dim]✓ Fastest hardsub (~2-3 min for 17 min video)[/dim]")
            console.print("   [dim]✓ Works on all platforms[/dim]")
            console.print("   [dim]✓ Good quality[/dim]")
            console.print("   [red]Cons:[/red]")
            console.print("   [dim]✗ Requires NVIDIA GPU[/dim]")
            
            console.print("\n[bold yellow]?[/bold yellow] [white]Choose option (1, 2, or 3, default=1):[/white] ", end="")
        else:
            console.print("\n[bold yellow]?[/bold yellow] [white]Choose option (1 or 2, default=1):[/white] ", end="")
        
        choice = input().strip()
        
        if choice == "" or choice == "1":
            return 'soft'
        elif choice == "2":
            return 'fast'
        elif choice == "3" and gpu_available:
            return 'gpu'
        else:
            if gpu_available:
                console.print("[yellow]Please enter 1, 2, or 3 (or press Enter for default)[/yellow]")
            else:
                console.print("[yellow]Please enter 1 or 2 (or press Enter for default)[/yellow]")


def ask_video_source():
    """Ask user for video source with Smart Resume"""
    from utils.system.checkpoint import list_checkpoints
    
    # Check for unfinished sessions
    checkpoints = list_checkpoints()
    has_checkpoints = len(checkpoints) > 0
    
    console.print("\n[bold cyan]Choose Video Source:[/bold cyan]")
    console.print("\n[bold yellow]1. Local File[/bold yellow]")
    console.print("   [dim]Video file from your computer[/dim]")
    
    console.print("\n[bold green]2. YouTube URL[/bold green]")
    console.print("   [dim]Download video from YouTube[/dim]")
    
    if has_checkpoints:
        if len(checkpoints) == 1:
            cp = checkpoints[0]
            name = cp.get('video_name', 'Unknown')
            step = cp.get('step', 'Unknown').title()
            console.print(f"\n[bold magenta]3. Resume: {name}[/bold magenta]")
            console.print(f"   [dim]Continue from {step}[/dim]")
        else:
            console.print(f"\n[bold magenta]3. Resume Session... ({len(checkpoints)} found)[/bold magenta]")
            console.print("   [dim]Select from unfinished projects[/dim]")

    while True:
        console.print("\n[bold yellow]?[/bold yellow] [white]Choose option:[/white] ", end="")
        choice = input().strip()
        
        if choice == "1":
            return "local"
        elif choice == "2":
            return "youtube"
        elif choice == "3" and has_checkpoints:
            if len(checkpoints) == 1:
                return f"resume:{checkpoints[0]['video_path']}"
            else:
                return _ask_resume_session(checkpoints)
        else:
            console.print("[yellow]Invalid option. Please try again.[/yellow]")


def _ask_resume_session(checkpoints):
    """Sub-menu for selecting session to resume"""
    console.print("\n[bold cyan]Select Session to Resume:[/bold cyan]")
    
    for i, cp in enumerate(checkpoints, 1):
        name = cp.get('video_name', 'Unknown')
        step = cp.get('step', 'Unknown').title()
        time_str = cp.get('timestamp', '').split('T')[0]
        console.print(f"[bold magenta]{i}. {name}[/bold magenta]")
        console.print(f"   [dim]Step: {step} • Date: {time_str}[/dim]")
    
    console.print(f"[bold yellow]{len(checkpoints) + 1}. Cancel (Go Back)[/bold yellow]")
    
    while True:
        console.print("\n[bold yellow]?[/bold yellow] [white]Select number:[/white] ", end="")
        choice = input().strip()
        
        if not choice.isdigit():
            console.print("[yellow]Please enter a number[/yellow]")
            continue
            
        idx = int(choice) - 1
        
        if 0 <= idx < len(checkpoints):
            return f"resume:{checkpoints[idx]['video_path']}"
        elif idx == len(checkpoints):
            # User chose Cancel/Back, restart generic ask
            return ask_video_source()
        else:
            console.print("[yellow]Invalid choice[/yellow]")


def get_youtube_url():
    """Get YouTube URL from user"""
    while True:
        console.print("\n[bold yellow]?[/bold yellow] [white]Enter YouTube URL:[/white] ", end="")
        url = input().strip()
        
        if url:
            from utils.media.youtube_downloader import is_youtube_url
            if is_youtube_url(url):
                return url
            else:
                console.print("[yellow]Invalid YouTube URL. Please try again.[/yellow]")
        else:
            console.print("[yellow]URL cannot be empty[/yellow]")


VALID_VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm', '.m4v'}


def get_local_file():
    """Get local file path from user"""
    import os
    
    while True:
        console.print("\n[bold yellow]?[/bold yellow] [white]Enter video file path:[/white] ", end="")
        file_path = input().strip()
        
        # Remove quotes if user dragged and dropped file
        if file_path.startswith('"') and file_path.endswith('"'):
            file_path = file_path[1:-1]
        
        if file_path:
            if os.path.exists(file_path):
                # Validation 1: Check extension
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in VALID_VIDEO_EXTENSIONS:
                    console.print(f"[red]Invalid file type: {ext}[/red]")
                    console.print(f"[yellow]Allowed types: {', '.join(sorted(VALID_VIDEO_EXTENSIONS))}[/yellow]")
                    continue
                
                # Validation 2: Check file size
                if os.path.getsize(file_path) == 0:
                    console.print("[red]File is empty (0 bytes)![/red]")
                    continue
                    
                return file_path
            else:
                console.print(f"[yellow]File not found: {file_path}[/yellow]")
                console.print("[yellow]Please enter a valid file path[/yellow]")
        else:
            console.print("[yellow]File path cannot be empty[/yellow]")
