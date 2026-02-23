"""
Docs command for AKIOS CLI.

Display documentation with beautiful Markdown rendering in the terminal.

Usage:
    akios docs                    # Show available docs
    akios docs README             # Show README.md
    akios docs SECURITY           # Show SECURITY.md
    akios docs path/to/file.md    # Show custom file
    akios docs --list             # List all docs
    akios docs --search query     # Search for docs
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    _console = Console()
except ImportError:
    _console = None

from ..markdown_renderer import (
    render_markdown_file,
    get_doc_paths,
    search_docs,
    validate_markdown_file,
    list_available_themes,
)
from ..helpers import CLIError
from ...core.ui.rich_output import print_panel, get_theme_color


def register_docs_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register docs command with argument parser.
    
    Args:
        subparsers: Subparser action from main parser
    """
    parser = subparsers.add_parser(
        "docs",
        help="Display AKIOS documentation with beautiful formatting",
        description="View Markdown documentation files with syntax highlighting and Rich formatting"
    )
    
    parser.add_argument(
        "doc",
        nargs="?",
        help="Documentation file name (README, SECURITY, etc.) or path to .md file"
    )
    
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all available documentation files"
    )
    
    parser.add_argument(
        "--search",
        "-s",
        metavar="QUERY",
        help="Search for documentation files by name"
    )
    
    parser.add_argument(
        "--theme",
        "-t",
        default="monokai",
        help="Syntax highlighting theme (default: monokai)"
    )
    
    parser.add_argument(
        "--width",
        "-w",
        type=int,
        help="Console width override"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    
    parser.set_defaults(func=run_docs_command)


def run_docs_command(args: argparse.Namespace) -> int:
    """
    Execute docs command.
    
    Args:
        args: Parsed command line arguments
    
    Returns:
        Exit code (0 for success)
    """
    try:
        # Handle --list flag
        if args.list:
            return _list_docs(args.json)
        
        # Handle --search flag
        if args.search:
            return _search_docs_command(args.search, args.json)
        
        # Handle no arguments - show available docs
        if not args.doc:
            return _show_available_docs(args.json)
        
        # Show specific doc
        return _display_doc(args.doc, args.theme, args.width, args.json)
        
    except CLIError as e:
        if args.json:
            import json
            print(json.dumps({"error": True, "message": str(e)}))
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        if args.json:
            import json
            print(json.dumps({"error": True, "message": str(e)}))
        else:
            print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def _list_docs(json_mode: bool = False) -> int:
    """List all available documentation files."""
    doc_paths = get_doc_paths()
    
    if json_mode:
        import json
        output = {"docs": [{"name": name, "path": path} for name, path in doc_paths.items()]}
        print(json.dumps(output, indent=2))
        return 0
    
    if not doc_paths:
        print("No documentation files found.")
        return 0
    
    print("📚 Available Documentation:\n")
    for name, path in sorted(doc_paths.items()):
        print(f"  • {name:20} → {path}")
    
    print(f"\n💡 Usage: akios docs <name>")
    print(f"   Example: akios docs README")
    
    return 0


def _search_docs_command(query: str, json_mode: bool = False) -> int:
    """Search for documentation files."""
    results = search_docs(query)
    
    if json_mode:
        import json
        output = {"query": query, "results": [{"path": path, "name": name} for path, name in results]}
        print(json.dumps(output, indent=2))
        return 0
    
    if not results:
        if _console:
            _console.print(f"[{get_theme_color('warning')}]No documentation files found matching:[/{get_theme_color('warning')}] [{get_theme_color('info')}]{query}[/{get_theme_color('info')}]")
        else:
            print(f"No documentation files found matching: {query}")
        return 0
    
    if _console:
        _console.print(f"[bold {get_theme_color('header')}]🔍 Search results for '{query}':[/bold {get_theme_color('header')}]\n")
        for path, name in results:
            _console.print(f"  [{get_theme_color('info')}]•[/{get_theme_color('info')}] [bold]{name:30}[/bold] [dim]→[/dim] [{get_theme_color('info')}]{path}[/{get_theme_color('info')}]")
        _console.print(f"\n[bold {get_theme_color('header')}]💡 View with:[/bold {get_theme_color('header')}] [{get_theme_color('info')}]akios docs <path>[/{get_theme_color('info')}]")
    else:
        print(f"🔍 Search results for '{query}':\n")
        for path, name in results:
            print(f"  • {name:30} → {path}")
        print(f"\n💡 View with: akios docs <path>")
    
    return 0


def _show_available_docs(json_mode: bool = False) -> int:
    """Show available documentation when no doc specified."""
    doc_paths = get_doc_paths()
    
    if json_mode:
        import json
        output = {"docs": [{"name": name, "path": path} for name, path in doc_paths.items()]}
        print(json.dumps(output, indent=2))
        return 0
    
    if not doc_paths:
        if _console:
            _console.print(f"[{get_theme_color('warning')}]No documentation files found in current directory.[/{get_theme_color('warning')}]")
            _console.print(f"\n[bold {get_theme_color('header')}]💡 Tip:[/bold {get_theme_color('header')}] [{get_theme_color('info')}]Run 'akios docs --search README' to search for docs[/{get_theme_color('info')}]")
        else:
            print("No documentation files found in current directory.")
            print("\n💡 Tip: Run 'akios docs --search README' to search for docs")
        return 0
    
    content = "[bold]Available documents:[/bold]\n"
    for name, path in sorted(doc_paths.items()):
        content += f"  • {name}\n"
    
    content += "\n[bold]Usage:[/bold]\n"
    content += "   akios docs README        [dim]# View README.md[/dim]\n"
    content += "   akios docs SECURITY      [dim]# View SECURITY.md[/dim]\n"
    content += "   akios docs --list        [dim]# List all docs[/dim]\n"
    content += "   akios docs path/file.md  [dim]# View custom file[/dim]"
    
    print_panel("AKIOS Documentation", content)
    
    return 0


def _display_doc(
    doc_name: str,
    theme: str,
    width: Optional[int],
    json_mode: bool
) -> int:
    """Display a specific documentation file."""
    # Try to resolve doc name to path
    file_path = _resolve_doc_path(doc_name)
    
    if not file_path:
        if json_mode:
            import json
            print(json.dumps({"error": True, "message": f"Documentation not found: {doc_name}"}))
        else:
            if _console:
                _console.print(f"[bold {get_theme_color('error')}]Error:[/bold {get_theme_color('error')}] [{get_theme_color('error')}]Documentation not found:[/{get_theme_color('error')}] [{get_theme_color('info')}]{doc_name}[/{get_theme_color('info')}]")
                _console.print(f"\n[bold {get_theme_color('header')}]💡 Tip:[/bold {get_theme_color('header')}] [{get_theme_color('info')}]Run 'akios docs --list' to see available documentation[/{get_theme_color('info')}]")
            else:
                print(f"Error: Documentation not found: {doc_name}", file=sys.stderr)
                print(f"\n💡 Tip: Run 'akios docs --list' to see available documentation", file=sys.stderr)
        return 1
    
    # Validate file
    valid, error = validate_markdown_file(file_path)
    if not valid:
        if json_mode:
            import json
            print(json.dumps({"error": True, "message": error}))
        else:
            if _console:
                _console.print(f"[bold {get_theme_color('error')}]Error:[/bold {get_theme_color('error')}] [{get_theme_color('error')}]{error}[/{get_theme_color('error')}]")
            else:
                print(f"Error: {error}", file=sys.stderr)
        return 1
    
    # Handle JSON mode
    if json_mode:
        import json
        try:
            content = Path(file_path).read_text(encoding='utf-8')
            output = {
                "file": file_path,
                "content": content,
                "lines": len(content.splitlines()),
                "size": len(content)
            }
            print(json.dumps(output, indent=2))
            return 0
        except Exception as e:
            print(json.dumps({"error": True, "message": str(e)}))
            return 1
    
    # Render markdown
    success = render_markdown_file(file_path, theme=theme, width=width, show_path=True)
    return 0 if success else 1


def _resolve_doc_path(doc_name: str) -> Optional[str]:
    """
    Resolve documentation name to file path.
    
    Args:
        doc_name: Doc name (README) or file path (docs/file.md)
    
    Returns:
        Resolved file path or None
    """
    # Check if it's a direct file path
    if doc_name.endswith('.md') or doc_name.endswith('.markdown'):
        path = Path(doc_name)
        if path.exists():
            return str(path)
    
    # Try common doc names
    doc_paths = get_doc_paths()
    if doc_name.upper() in doc_paths:
        return doc_paths[doc_name.upper()]
    
    # Try adding .md extension
    path_with_ext = Path(f"{doc_name}.md")
    if path_with_ext.exists():
        return str(path_with_ext)
    
    # Try in docs/ directory
    docs_dir = Path("docs")
    if docs_dir.exists():
        doc_path = docs_dir / f"{doc_name}.md"
        if doc_path.exists():
            return str(doc_path)
    
    # Try case-insensitive match
    for name, path in doc_paths.items():
        if name.lower() == doc_name.lower():
            return path
    
    return None
