# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Interactive Template Picker with Fuzzy Search

Provides interactive selection of workflow templates with:
- Arrow key navigation
- Fuzzy search with '/' trigger
- Live template preview
- Rich UI formatting
"""

import sys
from typing import List, Dict, Optional, Tuple

# Try questionary import (optional dependency)
try:
    import questionary
    from questionary import Choice
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False

# Try fuzzywuzzy import
try:
    from fuzzywuzzy import process as fuzzy_process
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from ..core.ui.rich_output import get_theme_color


class TemplatePickerError(Exception):
    """Raised when template picker encounters an error."""
    pass


class TemplatePicker:
    """
    Interactive template picker with fuzzy search capabilities.
    
    Features:
    - Arrow key navigation
    - Fuzzy search on template name and description
    - Live preview of selected template
    - Rich UI formatting with panels and tables
    
    Example:
        >>> templates = [
        ...     {"name": "hello.yml", "description": "Hello World"},
        ...     {"name": "doc_ingestion.yml", "description": "Document Analysis"}
        ... ]
        >>> picker = TemplatePicker(templates)
        >>> selected = picker.run()
        >>> if selected:
        ...     print(f"Selected: {selected['name']}")
    """
    
    def __init__(self, templates: List[Dict[str, str]], enable_search: bool = True):
        """
        Initialize the template picker.
        
        Args:
            templates: List of template dictionaries with 'name' and 'description'
            enable_search: Enable fuzzy search functionality (requires fuzzywuzzy)
        """
        if not templates:
            raise TemplatePickerError("No templates available")
        
        self.templates = templates
        self.enable_search = enable_search and FUZZYWUZZY_AVAILABLE
        self.console = Console()
        
    def is_interactive_available(self) -> bool:
        """
        Check if interactive mode is available.
        
        Returns:
            True if questionary is available and running in a TTY
        """
        return QUESTIONARY_AVAILABLE and sys.stdin.isatty()
    
    def run(self) -> Optional[Dict[str, str]]:
        """
        Run the interactive template picker.
        
        Returns:
            Selected template dictionary, or None if cancelled
        """
        if not self.is_interactive_available():
            return self._run_non_interactive()
        
        return self._run_interactive()
    
    def _run_interactive(self) -> Optional[Dict[str, str]]:
        """
        Run interactive picker with questionary.
        
        Returns:
            Selected template or None if cancelled
        """
        # Show welcome panel
        self._show_welcome_panel()
        
        # Build choices with descriptions
        choices = []
        for template in self.templates:
            name = template["name"]
            description = template.get("description", "No description")
            network_badge = "🌐" if template.get("network_required", True) else "💾"
            
            # Format: emoji name - description (truncated)
            choice_text = f"{network_badge} {name:<30} {description[:60]}"
            choices.append(Choice(title=choice_text, value=template))
        
        # Use questionary to select
        try:
            if self.enable_search:
                # Fuzzy search enabled
                instruction = "Use arrows to navigate, type to search, Enter to select, ESC to cancel"
            else:
                instruction = "Use arrows to navigate, Enter to select, ESC to cancel"
            
            selected = questionary.select(
                "Select a workflow template:",
                choices=choices,
                instruction=instruction,
                use_shortcuts=False,
                use_arrow_keys=True,
            ).ask()
            
            if selected:
                self._show_template_preview(selected)
                return selected
            
            return None
            
        except KeyboardInterrupt:
            self.console.print(f"\n[{get_theme_color('warning')}]Selection cancelled[/{get_theme_color('warning')}]")
            return None
    
    def _run_non_interactive(self) -> Optional[Dict[str, str]]:
        """
        Fallback non-interactive mode (simple numbered list).
        
        Returns:
            Selected template or None if cancelled
        """
        self.console.print(f"[{get_theme_color('warning')}]Interactive mode not available. Using fallback.[/{get_theme_color('warning')}]\n")
        
        # Display templates
        for idx, template in enumerate(self.templates, 1):
            name = template["name"]
            description = template.get("description", "No description")
            network_badge = "🌐" if template.get("network_required", True) else "💾"
            self.console.print(f"{idx}. {network_badge} {name} - {description}")
        
        self.console.print(f"\n0. Cancel\n")
        
        # Get user input
        try:
            choice = input("Enter template number: ").strip()
            if not choice or choice == "0":
                return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(self.templates):
                return self.templates[idx]
            else:
                self.console.print(f"[{get_theme_color('error')}]Invalid selection: {choice}[/{get_theme_color('error')}]")
                return None
        except (ValueError, KeyboardInterrupt):
            return None
    
    def _show_welcome_panel(self) -> None:
        """Display welcome panel with instructions."""
        instructions = (
            f"[bold {get_theme_color('header')}]Template Selector[/bold {get_theme_color('header')}]\n\n"
            "🔹 Use [bold]↑↓ arrows[/bold] to navigate\n"
            "🔹 Press [bold]Enter[/bold] to select\n"
            "🔹 Press [bold]ESC[/bold] to cancel"
        )
        
        if self.enable_search:
            instructions += "\n🔹 Type to [bold]search[/bold] (fuzzy matching)"
        
        panel = Panel(
            instructions,
            title="[bold]AKIOS Template Picker[/bold]",
            border_style=get_theme_color("header"),
            box=box.ROUNDED
        )
        self.console.print(panel)
        self.console.print()
    
    def _show_template_preview(self, template: Dict[str, str]) -> None:
        """
        Display preview of selected template.
        
        Args:
            template: Template dictionary to preview
        """
        # Create metadata table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Key", style=get_theme_color("info"))
        table.add_column("Value")
        
        table.add_row("Name", f"[bold]{template['name']}[/bold]")
        table.add_row("Description", template.get("description", "N/A"))
        table.add_row("Network", "Required" if template.get("network_required", True) else "Local only")
        
        panel = Panel(
            table,
            title=f"[bold {get_theme_color('success')}]✓ Template Selected[/bold {get_theme_color('success')}]",
            border_style=get_theme_color("success"),
            box=box.ROUNDED
        )
        self.console.print()
        self.console.print(panel)
    
    def fuzzy_search(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Perform fuzzy search on templates.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
        
        Returns:
            List of matching templates sorted by relevance score
        """
        if not FUZZYWUZZY_AVAILABLE:
            # Fallback: simple substring matching
            return [t for t in self.templates 
                    if query.lower() in t["name"].lower() 
                    or query.lower() in t.get("description", "").lower()]
        
        # Build searchable strings (name + description)
        searchable = []
        for template in self.templates:
            text = f"{template['name']} {template.get('description', '')}"
            searchable.append((text, template))
        
        # Perform fuzzy matching
        choices = [text for text, _ in searchable]
        matches = fuzzy_process.extract(query, choices, limit=limit)
        
        # Extract templates from matches (matches are tuples of (text, score))
        result_templates = []
        for match_text, score in matches:
            # Find the template corresponding to this match
            for text, template in searchable:
                if text == match_text:
                    result_templates.append(template)
                    break
        
        return result_templates


def run_template_picker(templates: List[Dict[str, str]], 
                        enable_search: bool = True) -> Optional[Dict[str, str]]:
    """
    Convenience function to run the template picker.
    
    Args:
        templates: List of template dictionaries
        enable_search: Enable fuzzy search functionality
    
    Returns:
        Selected template dictionary, or None if cancelled
    
    Example:
        >>> templates = get_templates_list()  # from templates.py
        >>> selected = run_template_picker(templates)
        >>> if selected:
        ...     print(f"Using template: {selected['name']}")
    """
    try:
        picker = TemplatePicker(templates, enable_search=enable_search)
        return picker.run()
    except TemplatePickerError as e:
        console = Console()
        console.print(f"[{get_theme_color('error')}]Error: {e}[/{get_theme_color('error')}]")
        return None
    except Exception as e:
        console = Console()
        console.print(f"[{get_theme_color('error')}]Unexpected error in template picker: {e}[/{get_theme_color('error')}]")
        return None
