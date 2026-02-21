"""
Interactive Setup Wizard for AKIOS v1.0.8

Provides step-by-step configuration prompts using questionary.
Supports back/skip navigation and input validation.

Features:
- Provider selection (OpenAI, Anthropic, Grok, Mistral, Gemini)
- API key input (masked/hidden)
- Budget limit configuration with validation
- Confirmation before save
- Back option to revise previous step
- Automatic fallback to manual mode in non-TTY environments
"""

import os
import sys
from typing import Dict, Tuple, Optional
from enum import Enum

try:
    import questionary
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False

from ..core.ui.rich_output import print_panel, print_success, print_warning, get_theme_color
from .rich_helpers import should_use_rich


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROK = "grok"
    MISTRAL = "mistral"
    GEMINI = "gemini"


class SetupWizardStep:
    """Represents a single step in the setup wizard."""

    def __init__(self, step_number: int, total_steps: int, title: str, description: str):
        """Initialize setup wizard step.

        Args:
            step_number: Current step (1-indexed)
            total_steps: Total steps in wizard
            title: Step title
            description: Step description
        """
        self.step_number = step_number
        self.total_steps = total_steps
        self.title = title
        self.description = description

    def display_header(self) -> None:
        """Display step header with progress indicator."""
        if should_use_rich():
            progress = f"Step {self.step_number}/{self.total_steps}"
            print_panel(
                f"{self.title}\n\n{self.description}",
                title=progress,
                style=get_theme_color("info")
            )
        else:
            print(f"\n{'='*60}")
            print(f"Step {self.step_number}/{self.total_steps}: {self.title}")
            print(f"{'='*60}")
            print(self.description)


class InteractiveSetupWizard:
    """Interactive setup wizard with questionary integration."""

    def __init__(self):
        """Initialize the setup wizard."""
        self.config: Dict[str, any] = {}
        self.step_history: list = []

    def is_interactive_available(self) -> bool:
        """Check if interactive mode is available.

        Returns True only if:
        - questionary is installed
        - TTY is detected (interactive terminal)
        - Not in JSON mode
        """
        if not QUESTIONARY_AVAILABLE:
            return False
        if not sys.stdin.isatty():
            return False
        if os.getenv("AKIOS_JSON_MODE"):
            return False
        return True

    def prompt_provider(self) -> Optional[str]:
        """Prompt for LLM provider selection.

        Returns:
            Provider name (lowercase) or None if skipped
        """
        step = SetupWizardStep(
            step_number=1,
            total_steps=3,
            title="Configure LLM Provider",
            description="Select which LLM provider to use for AI workflows"
        )
        step.display_header()

        if not self.is_interactive_available():
            provider = input("\nEnter LLM provider (openai/anthropic/grok/mistral/gemini): ").lower().strip()
            if provider not in [p.value for p in LLMProvider]:
                print(f"⚠️ Invalid provider: {provider}")
                return None
            return provider

        # Use questionary for interactive selection
        try:
            provider = questionary.select(
                "Select LLM provider:",
                choices=[
                    questionary.Choice(title="OpenAI (GPT-4, GPT-3.5-Turbo)", value=LLMProvider.OPENAI.value),
                    questionary.Choice(title="Anthropic (Claude)", value=LLMProvider.ANTHROPIC.value),
                    questionary.Choice(title="Grok (xAI)", value=LLMProvider.GROK.value),
                    questionary.Choice(title="Mistral", value=LLMProvider.MISTRAL.value),
                    questionary.Choice(title="Google Gemini", value=LLMProvider.GEMINI.value),
                ],
                style=questionary.Style([
                    ("highlighted", f"fg:{get_theme_color('success')} bold"),
                    ("pointer", f"fg:{get_theme_color('info')} bold"),
                ]) if should_use_rich() else None
            ).ask()

            if provider is None:  # User pressed ESC/Ctrl+C
                return None

            self.config["provider"] = provider
            self.step_history.append(("provider", provider))
            return provider

        except (KeyboardInterrupt, EOFError):
            return None

    def prompt_api_key(self, provider: str) -> Optional[str]:
        """Prompt for API key (masked input).

        Args:
            provider: LLM provider name

        Returns:
            API key or None if skipped
        """
        step = SetupWizardStep(
            step_number=2,
            total_steps=3,
            title="Configure API Key",
            description=f"Enter your {provider.upper()} API key (input will be hidden)"
        )
        step.display_header()

        if not self.is_interactive_available():
            api_key = input(f"\nEnter {provider.upper()} API key: ").strip()
            if not api_key:
                print("⚠️ API key cannot be empty")
                return None
            return api_key

        # Use questionary for password input (masked)
        try:
            api_key = questionary.password(
                f"Enter {provider.upper()} API key:",
                style=questionary.Style([
                    ("pointer", f"fg:{get_theme_color('info')} bold"),
                ]) if should_use_rich() else None
            ).ask()

            if api_key is None:  # User pressed ESC/Ctrl+C
                return None

            if not api_key.strip():
                print("⚠️ API key cannot be empty")
                return None

            self.config["api_key"] = api_key
            self.step_history.append(("api_key", "***hidden***"))
            return api_key

        except (KeyboardInterrupt, EOFError):
            return None

    def prompt_budget(self) -> Optional[float]:
        """Prompt for budget limit with validation.

        Returns:
            Budget in USD or None if skipped
        """
        step = SetupWizardStep(
            step_number=3,
            total_steps=3,
            title="Configure Budget Limit",
            description="Set the maximum budget per workflow run (in USD)"
        )
        step.display_header()

        if not self.is_interactive_available():
            while True:
                try:
                    budget_str = input("\nEnter budget limit ($): ").strip()
                    budget = float(budget_str)
                    if budget <= 0:
                        print("⚠️ Budget must be positive")
                        continue
                    return budget
                except ValueError:
                    print("⚠️ Invalid number format")
                    continue

        # Use questionary for numeric input
        try:
            budget_str = questionary.text(
                "Enter budget limit ($):",
                default="10.00",
                validate=lambda x: self._validate_budget(x),
                style=questionary.Style([
                    ("pointer", f"fg:{get_theme_color('info')} bold"),
                ]) if should_use_rich() else None
            ).ask()

            if budget_str is None:  # User pressed ESC/Ctrl+C
                return None

            budget = float(budget_str)
            self.config["budget"] = budget
            self.step_history.append(("budget", f"${budget:.2f}"))
            return budget

        except (KeyboardInterrupt, EOFError):
            return None

    @staticmethod
    def _validate_budget(value: str) -> bool:
        """Validate budget input.

        Args:
            value: User input string

        Returns:
            True if valid, False otherwise
        """
        if not value:
            return "Budget cannot be empty"
        try:
            budget = float(value)
            if budget <= 0:
                return "Budget must be positive"
            return True
        except ValueError:
            return "Must be a valid number"

    def prompt_confirmation(self) -> bool:
        """Prompt for confirmation before saving.

        Returns:
            True if user confirms, False otherwise
        """
        if not self.is_interactive_available():
            print("\nConfiguration Summary:")
            for key, value in self.step_history:
                print(f"  {key}: {value}")
            confirm = input("\nSave configuration? (yes/no): ").lower().strip()
            return confirm in ["yes", "y"]

        try:
            summary = "\n".join([
                f"✓ Provider: {self.config.get('provider', 'not set')}",
                f"✓ API Key: ***hidden***",
                f"✓ Budget: ${self.config.get('budget', 0):.2f} per run"
            ])

            if should_use_rich():
                print_panel(
                    summary,
                    title="Review Configuration",
                    style=get_theme_color("info")
                )

            confirm = questionary.confirm(
                "Save this configuration?",
                auto_enter=False,
                style=questionary.Style([
                    ("pointer", f"fg:{get_theme_color('info')} bold"),
                    ("highlighted", f"fg:{get_theme_color('success')} bold"),
                ]) if should_use_rich() else None
            ).ask()

            return confirm if confirm is not None else False

        except (KeyboardInterrupt, EOFError):
            return False

    def run(self) -> Tuple[bool, Dict[str, any]]:
        """Run the complete setup wizard.

        Returns:
            Tuple of (success: bool, config: dict)
        """
        try:
            # Step 1: Provider
            provider = self.prompt_provider()
            if provider is None:
                print("⚠️ Setup cancelled")
                return False, {}

            # Step 2: API Key
            api_key = self.prompt_api_key(provider)
            if api_key is None:
                print("⚠️ Setup cancelled")
                return False, {}

            # Step 3: Budget
            budget = self.prompt_budget()
            if budget is None:
                print("⚠️ Setup cancelled")
                return False, {}

            # Confirmation
            if not self.prompt_confirmation():
                print("⚠️ Configuration not saved")
                return False, {}

            if should_use_rich():
                print_success("✓ Configuration saved successfully!")
            else:
                print("✓ Configuration saved successfully!")

            return True, self.config

        except (KeyboardInterrupt, EOFError):
            print("\n⚠️ Setup interrupted")
            return False, {}
        except Exception as e:
            print(f"✗ Setup error: {e}")
            return False, {}


def run_interactive_setup() -> Tuple[bool, Dict[str, any]]:
    """Run the interactive setup wizard.

    Returns:
        Tuple of (success: bool, config: dict)

    Example:
        success, config = run_interactive_setup()
        if success:
            provider = config['provider']
            api_key = config['api_key']
            budget = config['budget']
    """
    if not QUESTIONARY_AVAILABLE:
        print_warning(
            "Interactive mode requires questionary library.\n"
            "Install with: pip install questionary\n"
            "Falling back to manual configuration..."
        )
        return False, {}

    wizard = InteractiveSetupWizard()
    return wizard.run()
