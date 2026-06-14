import os
import sys
import argparse
from faultsnap.capsule import read_capsule, read_manifest, CapsuleCorruptedError
from faultsnap.config import config
from faultsnap.storage import _read_index, clean_old_reports

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree
    from rich.syntax import Syntax
    from rich import print as rprint
except ImportError:
    print("FaultSnap CLI requires the 'rich' library. Please install it using `pip install rich`.")
    sys.exit(1)

def handle_corrupted_error(e, console):
    console.print(f"[bold red]Capsule Error:[/bold red] {e}")
    sys.exit(1)

def cmd_inspect(args):
    console = Console()
    try:
        manifest = read_manifest(args.file)
        crash_data = read_capsule(args.file)
    except CapsuleCorruptedError as e:
        handle_corrupted_error(e, console)
    except Exception as e:
        console.print(f"[red]Error reading capsule:[/red] {e}")
        sys.exit(1)
        
    table = Table(title="FaultSnap Capsule Metadata", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="magenta")
    
    for k, v in manifest.items():
        table.add_row(k.replace('_', ' ').title(), str(v))
        
    console.print(table)
    
    # Also print exception text
    if "exception_text" in crash_data:
        console.print(Panel(crash_data["exception_text"], title="Exception", border_style="red"))

def cmd_stack(args):
    console = Console()
    try:
        crash_data = read_capsule(args.file)
    except CapsuleCorruptedError as e:
        handle_corrupted_error(e, console)
    except Exception as e:
        console.print(f"[red]Error reading capsule:[/red] {e}")
        sys.exit(1)
        
    frames = crash_data.get("frames", [])
    
    tree = Tree(f"[bold red]Crash Call Stack[/bold red]")
    
    for i, frame in enumerate(frames):
        filename = frame.get('filename', 'Unknown')
        lineno = frame.get('lineno', '?')
        name = frame.get('name', '?')
        line_code = frame.get('line', '').strip()
        
        node_label = f"[cyan]{filename}[/cyan]:[yellow]{lineno}[/yellow] in [bold magenta]{name}[/bold magenta]"
        node = tree.add(node_label)
        
        if line_code:
            node.add(f"[green]{line_code}[/green]")
            
    console.print(tree)

def cmd_vars(args):
    console = Console()
    try:
        crash_data = read_capsule(args.file)
    except CapsuleCorruptedError as e:
        handle_corrupted_error(e, console)
    except Exception as e:
        console.print(f"[red]Error reading capsule:[/red] {e}")
        sys.exit(1)
        
    frames = crash_data.get("frames", [])
    
    for i, frame in enumerate(frames):
        filename = frame.get('filename', 'Unknown')
        lineno = frame.get('lineno', '?')
        name = frame.get('name', '?')
        locals_dict = frame.get('locals', {})
        
        if not locals_dict:
            continue
            
        table = Table(title=f"Locals in {name} ({filename}:{lineno})", show_header=True, header_style="bold magenta")
        table.add_column("Variable", style="cyan")
        table.add_column("Value", style="green", overflow="fold")
        
        for k, v in locals_dict.items():
            table.add_row(str(k), str(v))
            
        console.print(table)
        console.print()

def cmd_env(args):
    console = Console()
    try:
        crash_data = read_capsule(args.file)
    except CapsuleCorruptedError as e:
        handle_corrupted_error(e, console)
    except Exception as e:
        console.print(f"[red]Error reading capsule:[/red] {e}")
        sys.exit(1)
        
    env_data = crash_data.get("environment", {})
    if not env_data:
        console.print("[yellow]No environment data captured (or it was empty).[/yellow]")
        return
        
    table = Table(title="Environment Variables", show_header=True, header_style="bold magenta")
    table.add_column("Variable", style="cyan")
    table.add_column("Value", style="green", overflow="fold")
    
    for k, v in env_data.items():
        table.add_row(str(k), str(v))
        
    console.print(table)

def cmd_fingerprint(args):
    console = Console()
    try:
        manifest = read_manifest(args.file)
    except CapsuleCorruptedError as e:
        handle_corrupted_error(e, console)
    except Exception as e:
        console.print(f"[red]Error reading capsule:[/red] {e}")
        sys.exit(1)
    
    fingerprint = manifest.get("fingerprint", "Unknown")
    console.print(f"Fingerprint: [bold cyan]{fingerprint}[/bold cyan]")

def cmd_diff(args):
    console = Console()
    try:
        manifest1 = read_manifest(args.file1)
        manifest2 = read_manifest(args.file2)
    except CapsuleCorruptedError as e:
        handle_corrupted_error(e, console)
    except Exception as e:
        console.print(f"[red]Error reading capsule:[/red] {e}")
        sys.exit(1)
        
    table = Table(title="Crash Comparison", show_header=True, header_style="bold blue")
    table.add_column("Attribute", style="cyan")
    table.add_column("Report 1", style="magenta")
    table.add_column("Report 2", style="magenta")
    
    attrs_to_check = ["fingerprint", "exception_type", "exception_value", "python_version", "platform"]
    for attr in attrs_to_check:
        val1 = manifest1.get(attr, "N/A")
        val2 = manifest2.get(attr, "N/A")
        
        if val1 != val2:
            table.add_row(attr, f"[yellow]{val1}[/yellow]", f"[yellow]{val2}[/yellow]")
        else:
            table.add_row(attr, val1, val2)
            
    console.print(table)

def cmd_html(args):
    console = Console()
    try:
        from faultsnap.html import generate_html_report
        out_path = generate_html_report(args.file)
        console.print(f"[green]Successfully generated HTML report at:[/green] {out_path}")
    except CapsuleCorruptedError as e:
        handle_corrupted_error(e, console)
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error generating HTML report:[/red] {e}")
        sys.exit(1)

def print_crash_table(crashes, title="Stored Crashes"):
    console = Console()
    if not crashes:
        console.print("[yellow]No crashes found.[/yellow]")
        return
        
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Timestamp", style="white")
    table.add_column("Exception", style="red")
    table.add_column("Fingerprint", style="magenta")
    
    for crash in crashes:
        ts = crash.get("timestamp", "Unknown")
        # format timestamp slightly better if possible
        if "T" in ts:
            ts = ts.replace("T", " ")
        if "." in ts:
            ts = ts.split(".")[0]
        exc = crash.get("exception", "Unknown")
        fp = crash.get("fingerprint", "Unknown")[:8]
        table.add_row(ts, exc, fp)
        
    console.print(table)

def cmd_list(args):
    index = _read_index()
    print_crash_table(index)

def cmd_latest(args):
    console = Console()
    latest_file = os.path.join(config.repository_dir, "latest", "latest.faultsnap")
    if not os.path.exists(latest_file):
        console.print("[yellow]No latest crash found.[/yellow]")
        return
    args.file = latest_file
    cmd_inspect(args)

def cmd_search(args):
    index = _read_index()
    term = args.term.lower()
    
    results = []
    for crash in index:
        if term in crash.get("exception", "").lower() or term in crash.get("fingerprint", "").lower():
            results.append(crash)
            
    print_crash_table(results, title=f"Search Results for '{args.term}'")

def cmd_stats(args):
    console = Console()
    index = _read_index()
    
    if not index:
        console.print("[yellow]No crashes found in repository.[/yellow]")
        return
        
    total_crashes = len(index)
    unique_fingerprints = len(set([c.get("fingerprint") for c in index]))
    
    exc_counts = {}
    for c in index:
        exc = c.get("exception", "Unknown")
        exc_counts[exc] = exc_counts.get(exc, 0) + 1
        
    most_common = max(exc_counts, key=exc_counts.get) if exc_counts else "None"
    
    dates = [c.get("timestamp") for c in index if c.get("timestamp")]
    dates.sort()
    
    oldest = dates[0].split("T")[0] if dates else "Unknown"
    newest = dates[-1].split("T")[0] if dates else "Unknown"
    
    console.print(f"Total Crashes: [bold cyan]{total_crashes}[/bold cyan]")
    console.print(f"Unique Fingerprints: [bold cyan]{unique_fingerprints}[/bold cyan]")
    console.print(f"Most Common Error: [bold red]{most_common}[/bold red]")
    console.print(f"Oldest Crash: [yellow]{oldest}[/yellow]")
    console.print(f"Newest Crash: [yellow]{newest}[/yellow]")

def cmd_clean(args):
    console = Console()
    try:
        clean_old_reports()
        console.print("[green]Successfully cleaned old reports according to retention policy.[/green]")
    except Exception as e:
        console.print(f"[red]Error cleaning reports:[/red] {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="FaultSnap CLI Inspector")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    parser_inspect = subparsers.add_parser("inspect", help="Inspect high-level metadata and exception")
    parser_inspect.add_argument("file", help="Path to .faultsnap file")
    
    parser_stack = subparsers.add_parser("stack", help="View the crash call stack")
    parser_stack.add_argument("file", help="Path to .faultsnap file")
    
    parser_vars = subparsers.add_parser("vars", help="View local variables for each frame")
    parser_vars.add_argument("file", help="Path to .faultsnap file")
    
    parser_env = subparsers.add_parser("env", help="View captured environment variables")
    parser_env.add_argument("file", help="Path to .faultsnap file")

    parser_fingerprint = subparsers.add_parser("fingerprint", help="Print the crash fingerprint hash")
    parser_fingerprint.add_argument("file", help="Path to .faultsnap file")
    
    parser_diff = subparsers.add_parser("diff", help="Compare two crash reports")
    parser_diff.add_argument("file1", help="Path to first .faultsnap file")
    parser_diff.add_argument("file2", help="Path to second .faultsnap file")

    parser_html = subparsers.add_parser("html", help="Generate a standalone HTML report")
    parser_html.add_argument("file", help="Path to .faultsnap file")
    
    # New commands
    parser_list = subparsers.add_parser("list", help="Shows all stored crashes")
    parser_latest = subparsers.add_parser("latest", help="Inspect the most recent crash")
    
    parser_search = subparsers.add_parser("search", help="Search by exception type or fingerprint")
    parser_search.add_argument("term", help="Search term")
    
    parser_stats = subparsers.add_parser("stats", help="Display repository statistics")
    parser_clean = subparsers.add_parser("clean", help="Remove expired reports based on retention policy")
    
    args = parser.parse_args()
    
    if args.command == "inspect":
        cmd_inspect(args)
    elif args.command == "stack":
        cmd_stack(args)
    elif args.command == "vars":
        cmd_vars(args)
    elif args.command == "env":
        cmd_env(args)
    elif args.command == "fingerprint":
        cmd_fingerprint(args)
    elif args.command == "diff":
        cmd_diff(args)
    elif args.command == "html":
        cmd_html(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "latest":
        cmd_latest(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "clean":
        cmd_clean(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
