"""
Markdown rendering with Rich for AKIOS.

Provides beautiful terminal rendering of Markdown documentation with:
- Syntax highlighting for code blocks
- Styled headers, lists, and blockquotes
- Tables with Rich formatting
- Links with URLs
- Fallback to plain text for non-TTY environments

Usage:
    from akios.cli.markdown_renderer import render_markdown
    
    render_markdown("# Hello\nThis is **bold** text")
    
    # Or from file
    render_markdown_file("README.md")
"""

import sys
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def render_markdown(
    markdown_content: str,
    theme: Optional[str] = None,
    width: Optional[int] = None
) -> None:
    """
    Render Markdown content to terminal with Rich formatting.
    
    Args:
        markdown_content: Markdown text to render
        theme: Syntax highlighting theme (default: monokai)
        width: Console width override (default: auto-detect)
    
    Example:
        >>> content = "# Hello\\n\\nThis is **bold** and *italic*."
        >>> render_markdown(content)
    """
    if not RICH_AVAILABLE or not sys.stdout.isatty():
        # Fallback to plain text
        _render_plain_text(markdown_content)
        return
    
    try:
        console = Console(width=width) if width else Console()
        
        # Create Markdown object with Rich
        md = Markdown(
            markdown_content,
            code_theme=theme or "monokai",
            hyperlinks=True,  # Show URLs for links
            inline_code_theme="monokai",
        )
        
        console.print(md)
        
    except Exception as e:
        # Fallback on any error
        print(f"Warning: Markdown rendering failed ({e}), falling back to plain text", file=sys.stderr)
        _render_plain_text(markdown_content)


def render_markdown_file(
    file_path: str,
    theme: Optional[str] = None,
    width: Optional[int] = None,
    show_path: bool = True
) -> bool:
    """
    Render Markdown file to terminal.
    
    Args:
        file_path: Path to Markdown file
        theme: Syntax highlighting theme
        width: Console width override
        show_path: Show file path header (default: True)
    
    Returns:
        True if successful, False if file not found
    
    Example:
        >>> render_markdown_file("README.md")
        True
    """
    # Handle GitHub fallback for missing files
    if file_path == "Remote (GitHub)":
        if RICH_AVAILABLE and sys.stdout.isatty():
            from rich.panel import Panel
            console = Console(width=width) if width else Console()
            console.print(Panel(
                "[yellow]This document is not available locally.[/yellow]\n\n"
                "Please view it on GitHub:\n"
                "[link=https://github.com/akioudai/akios]https://github.com/akioudai/akios[/link]",
                title="Documentation",
                border_style="yellow"
            ))
        else:
            print("This document is not available locally.")
            print("Please view it on GitHub: https://github.com/akioudai/akios")
        return True

    path = Path(file_path)
    
    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return False
    
    if not path.is_file():
        print(f"Error: Not a file: {file_path}", file=sys.stderr)
        return False
    
    try:
        content = path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return False
    
    # Show file path header
    if show_path:
        if RICH_AVAILABLE and sys.stdout.isatty():
            from rich.panel import Panel
            from ..core.ui.rich_output import get_theme_color
            console = Console(width=width) if width else Console()
            console.print(Panel(
                f"📄 [bold {get_theme_color('header')}]{file_path}[/bold {get_theme_color('header')}]",
                title="AKIOS Documentation",
                border_style=get_theme_color("header")
            ))
            print()  # Spacing
        else:
            print(f"=== {file_path} ===\n")
    
    # Render content
    render_markdown(content, theme=theme, width=width)
    return True


def render_code_block(
    code: str,
    language: str = "python",
    theme: str = "monokai",
    line_numbers: bool = True
) -> None:
    """
    Render code block with syntax highlighting.
    
    Args:
        code: Code content to render
        language: Programming language for syntax highlighting
        theme: Color theme for highlighting
        line_numbers: Show line numbers
    
    Example:
        >>> render_code_block("def hello():\\n    print('world')", "python")
    """
    if not RICH_AVAILABLE or not sys.stdout.isatty():
        # Fallback: plain text with language label
        print(f"```{language}")
        print(code)
        print("```")
        return
    
    try:
        console = Console()
        syntax = Syntax(
            code,
            language,
            theme=theme,
            line_numbers=line_numbers,
            word_wrap=True
        )
        console.print(syntax)
    except Exception:
        # Fallback
        print(f"```{language}")
        print(code)
        print("```")


def list_available_themes() -> list:
    """
    List available syntax highlighting themes.
    
    Returns:
        List of theme names
    
    Example:
        >>> themes = list_available_themes()
        >>> "monokai" in themes
        True
    """
    if not RICH_AVAILABLE:
        return ["monokai"]  # Default
    
    try:
        from rich.syntax import Syntax
        # Common Rich/Pygments themes
        return [
            "monokai",
            "github-dark",
            "dracula",
            "nord",
            "material",
            "one-dark",
            "solarized-dark",
            "solarized-light",
            "default",
        ]
    except Exception:
        return ["monokai"]


def _render_plain_text(markdown_content: str) -> None:
    """
    Fallback plain text renderer for non-TTY or when Rich unavailable.
    
    Args:
        markdown_content: Markdown content to display
    """
    # Simple plain text output
    # Could add basic Markdown stripping here if needed
    print(markdown_content)


def search_docs(
    query: str,
    docs_dir: Optional[str] = None
) -> list[tuple[str, str]]:
    """
    Search for documentation files matching query.
    
    Args:
        query: Search query (file name or keyword)
        docs_dir: Documentation directory (default: ./docs)
    
    Returns:
        List of (file_path, file_name) tuples
    
    Example:
        >>> results = search_docs("README")
        >>> len(results) > 0
        True
    """
    if docs_dir is None:
        docs_dir = "docs"
    
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        # Try alternative locations
        for alt in [".", "src/akios", ".."]:
            alt_path = Path(alt)
            if alt_path.exists():
                docs_path = alt_path
                break
    
    results = []
    query_lower = query.lower()
    
    # Search for .md files
    try:
        for md_file in docs_path.rglob("*.md"):
            if query_lower in md_file.name.lower():
                results.append((str(md_file), md_file.name))
    except Exception:
        pass
    
    return results


def get_doc_paths() -> dict[str, str]:
    """
    Get common documentation paths in AKIOS project.
    
    Returns:
        Dict mapping doc names to file paths
    
    Example:
        >>> paths = get_doc_paths()
        >>> "README" in paths
        True
    """
    common_docs = {
        "README": "README.md",
        "SECURITY": "SECURITY.md",
        "GETTING_STARTED": "GETTING_STARTED.md",
        "TROUBLESHOOTING": "TROUBLESHOOTING.md",
        "AGENTS": "AGENTS.md",
        "ROADMAP": "ROADMAP.md",
        "CHANGELOG": "CHANGELOG.md",
        "LEGAL": "LEGAL.md",
        "LICENSE": "LICENSE",
        "NOTICE": "NOTICE",
        "CONTRIBUTING": "CONTRIBUTING.md",
        "CODE_OF_CONDUCT": "CODE_OF_CONDUCT.md",
        "DCO": "DCO.md",
        "GOVERNANCE": "GOVERNANCE.md",
        "SUPPORT": "SUPPORT.md",
        "TRADEMARKS": "TRADEMARKS.md",
        "THIRD_PARTY_LICENSES": "THIRD_PARTY_LICENSES.md",
    }
    
    existing_docs = {}
    
    # Check multiple locations for documentation
    # 1. Current directory (user's project)
    # 2. System install location (Docker image)
    # 3. Python package location (pip install)
    search_paths = [
        Path("."),
        Path("/usr/share/akios/legal"),
        Path(sys.prefix) / "share/akios/legal"
    ]
    
    # Only check current directory (no dependency on package/repo root)
    for name, filename in common_docs.items():
        found = False
        for search_path in search_paths:
            file_path = search_path / filename
            if file_path.exists():
                existing_docs[name] = str(file_path.absolute())
                found = True
                break
    
    # If key docs are missing, we still want to list them so we can show the GitHub link
    for name in common_docs:
        if name not in existing_docs:
            existing_docs[name] = "Remote (GitHub)"
            
    return existing_docs


def format_markdown_table(
    headers: list[str],
    rows: list[list[str]]
) -> str:
    """
    Format data as Markdown table.
    
    Args:
        headers: Column headers
        rows: Data rows
    
    Returns:
        Markdown table string
    
    Example:
        >>> table = format_markdown_table(["Name", "Age"], [["Alice", "30"], ["Bob", "25"]])
        >>> "|" in table
        True
    """
    if not headers or not rows:
        return ""
    
    # Header row
    md = "| " + " | ".join(headers) + " |\n"
    # Separator
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    # Data rows
    for row in rows:
        md += "| " + " | ".join(str(cell) for cell in row) + " |\n"
    
    return md


def validate_markdown_file(file_path: str) -> tuple[bool, Optional[str]]:
    """
    Validate markdown file exists and is readable.
    
    Args:
        file_path: Path to markdown file
    
    Returns:
        (is_valid, error_message)
    
    Example:
        >>> valid, error = validate_markdown_file("README.md")
        >>> valid
        True
    """
    path = Path(file_path)
    
    if not path.exists():
        return False, f"File not found: {file_path}"
    
    if not path.is_file():
        return False, f"Not a file: {file_path}"
    
    # Allow known non-markdown files like LICENSE/NOTICE or specific extensions
    known_files = ['LICENSE', 'NOTICE']
    if path.name not in known_files and not path.suffix.lower() in ['.md', '.markdown']:
        return False, f"Not a Markdown file: {file_path}"
    
    try:
        path.read_text(encoding='utf-8')
    except Exception as e:
        return False, f"Cannot read file: {e}"
    
    return True, None
