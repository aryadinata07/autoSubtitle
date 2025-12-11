"""UI utilities for terminal display"""
from colorama import Fore, Style, init
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

# Initialize colorama
init(autoreset=True)

console = Console()


def print_header(title):
    """Print styled header"""
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold white]{title.center(60)}[/bold white]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]")


def print_info(label, value):
    """Print info line"""
    console.print(f"[cyan]{label}:[/cyan] [white]{value}[/white]")


def print_step(step, total, message):
    """Print step indicator"""
    console.print(f"\n[bold yellow][{step}/{total}][/bold yellow] [bold white]{message}[/bold white]")


def print_substep(message):
    """Print substep message"""
    console.print(f"      [dim]{message}[/dim]")


def print_success(message):
    """Print success message"""
    console.print(f"      [bold green]✓[/bold green] [green]{message}[/green]")


def print_warning(message):
    """Print warning message"""
    console.print(f"      [bold yellow]⚠[/bold yellow] [yellow]{message}[/yellow]")


def print_error(message):
    """Print error message"""
    console.print(f"      [bold red]❌[/bold red] [red]{message}[/red]")


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
