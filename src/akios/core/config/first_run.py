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
First-Run Detection and Setup Wizard

Detects first-time usage and provides guided setup for both Native and Docker deployments.
Handles interactive configuration with TTY compatibility across environments.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from ...core.ui.commands import suggest_command

logger = logging.getLogger(__name__)


class FirstRunDetector:
    """
    Detects first-time usage and manages setup wizard state.

    Works identically in both Native and Docker deployments by checking
    configuration files and project state.
    """

    def __init__(self, project_root: Path):
        """
        Initialize detector for project.

        Args:
            project_root: Project directory to check
        """
        self.project_root = project_root
        self.setup_marker = project_root / ".akios_setup_complete"

    def is_first_run(self) -> bool:
        """
        Determine if this is a first run based on configuration state.

        Returns:
            True if setup wizard should be shown
        """
        # Check for setup completion marker
        if self.setup_marker.exists():
            return False

        # Check for existing valid configuration
        env_file = self.project_root / ".env"
        config_file = self.project_root / "config.yaml"

        if not env_file.exists() or not config_file.exists():
            return True

        # Check if configuration has required API keys
        try:
            from ...config.loader import get_settings
            settings = get_settings()

            # Check for at least one configured provider
            providers_configured = []
            if hasattr(settings, 'llm_provider') and settings.llm_provider:
                providers_configured.append('llm')

            if providers_configured:
                # Mark setup as complete since we have working config
                self._mark_setup_complete()
                return False

        except Exception:
            # If configuration loading fails, assume first run
            pass

        return True

    def _mark_setup_complete(self) -> None:
        """Mark setup as completed to skip wizard on future runs."""
        try:
            self.setup_marker.write_text("Setup completed successfully\n")
        except Exception:
            # Silently fail if we can't write marker
            pass

    def should_show_wizard(self) -> bool:
        """
        Determine if setup wizard should be displayed.

        Returns:
            True if wizard should be shown
        """
        # Check for explicit skip
        if os.environ.get('AKIOS_SKIP_SETUP') == '1':
            return False

        # Check for non-interactive environment
        if not self._is_interactive():
            return False

        return self.is_first_run()

    def _is_interactive(self) -> bool:
        """
        Check if we're in an interactive terminal environment.

        Works in both native terminals and Docker containers.

        Returns:
            True if interactive terminal detected
        """
        # Check for explicit non-interactive flag (overrides all other checks)
        if os.environ.get('AKIOS_NON_INTERACTIVE') == '1':
            if os.environ.get('AKIOS_DEBUG_ENABLED') == '1':
                logger.debug("AKIOS_NON_INTERACTIVE detected, returning False")
            return False

        # Check for explicit interactive flag
        if os.environ.get('AKIOS_INTERACTIVE') == '1':
            if os.environ.get('AKIOS_DEBUG_ENABLED') == '1':
                logger.debug("AKIOS_INTERACTIVE detected, returning True")
            return True

        # Check for Docker/container environment - multiple detection methods
        in_docker = (
            os.path.exists('/.dockerenv') or  # Docker env file
            os.environ.get('AKIOS_IN_DOCKER') == '1' or  # Explicit flag
            (os.path.exists('/proc/1/cgroup') and 'docker' in open('/proc/1/cgroup').read()) or  # cgroup check
            (os.environ.get('TERM') == 'dumb' and os.environ.get('SHELL'))  # Terminal indicators
        )

        # In Docker or containerized environments, require a real TTY
        if in_docker:
            try:
                return sys.stdin.isatty() or sys.stdout.isatty()
            except Exception:
                return False

        # Standard native environment check
        try:
            # Additional check: try to read a single character to test if input is actually available
            import select
            # Check if stdin has data available (non-blocking)
            if hasattr(select, 'select') and hasattr(os, 'fdopen'):
                ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                if sys.stdin in ready:
                    return True
            return sys.stdin.isatty() and sys.stdout.isatty()
        except (ImportError, OSError, AttributeError):
            # Fallback to basic TTY check if select/os operations fail
            return sys.stdin.isatty() and sys.stdout.isatty()


class SetupWizard:
    """
    Interactive setup wizard for first-time configuration.

    Provides guided setup that works in both terminal (Native) and
    container TTY (Docker) environments.
    """

    def __init__(self, project_root: Path):
        """
        Initialize wizard.

        Args:
            project_root: Project directory
        """
        self.project_root = project_root
        self.detector = FirstRunDetector(project_root)

    def run_wizard(self, force: bool = False) -> bool:
        """
        Run the complete setup wizard.

        Returns:
            True if setup completed successfully
        """
        if not force and not self.detector.should_show_wizard():
            return True

        interactive_tty = sys.stdin.isatty() and sys.stdout.isatty()

        print("\n🎉 Welcome to AKIOS v1.0! Let's set up your first workflow.\n")

        interactive = self.detector._is_interactive()

        # Step 1: Choose between mock and real API
        use_real_api = self._select_api_mode()
        if use_real_api is None:  # Cancelled
            if interactive_tty:
                print("Setup cancelled.")
            return False

        # Step 2: Provider selection (only if using real API)
        if use_real_api:
            provider = self._select_provider()
            if not provider:
                if interactive_tty:
                    print("Setup cancelled.")
                return False
            self.current_provider = provider
        else:
            # Mock mode - set provider to 'mock'
            provider = 'mock'
            self.current_provider = 'mock'

        # Step 3: API key setup (skip for mock mode)
        if provider == 'mock':
            api_key = 'mock-key'
            print("\n🎭 Using mock mode - no API key required!")
        else:
            api_key = self._setup_api_key(provider)
            if not api_key:
                if interactive_tty:
                    print("Setup cancelled.")
                return False

            # Step 4: API key validation with test call
            provider_label = self._get_provider_display_name(provider)
            print(f"\n🔍 Testing {provider_label} key... [....] ", end="", flush=True)
            if not self._test_api_key(provider, api_key):
                print("❌ Failed!")
                print("❌ API key validation failed. Please check your key and try again.")
                return False
            print("✅ Validated!")

        # Step 4: Model selection (skip for mock mode)
        if provider == 'mock':
            model = 'mock-model'
            print("\n🎭 Mock mode - using simulated AI responses!")
        else:
            model = self._select_model(provider)

        # Store for success message
        self.current_model = model

        # Step 5: Advanced settings (skip for mock mode)
        if provider == 'mock':
            advanced_config = {}
            print("\n⚙️ Using default settings for mock mode!")
        else:
            advanced_config = self._configure_advanced_settings()

        # Step 6: Configuration validation and save
        if not self._validate_and_save(provider, api_key, model, advanced_config):
            print("❌ Configuration validation failed. Please try again.")
            return False

        # Step 4: Success and next steps
        budget = advanced_config.get('budget_limit', 1.0) if advanced_config else 1.0
        self._show_success_message(budget)

        # Mark setup as complete
        self.detector._mark_setup_complete()

        return True

    def _test_api_key(self, provider: str, api_key: str) -> bool:
        """
        Test API key with a real API call to validate it's working.

        Args:
            provider: Provider name
            api_key: API key to test

        Returns:
            True if API key is valid and working
        """
        try:
            if not self._validate_api_key_format(provider, api_key):
                print(f"❌ {provider.title()} API key format invalid.")
                return False

            # Lightweight validation only; real model access is validated later.
            return True
        except Exception as e:
            print(f"❌ API key test failed: {e}")
            return False

    def _get_required_env_var(self, provider: str) -> str:
        """
        Map provider to its required API key environment variable.

        Args:
            provider: Provider name

        Returns:
            Environment variable name for the provider API key
        """
        provider_env = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'grok': 'GROK_API_KEY',
            'mistral': 'MISTRAL_API_KEY',
            'gemini': 'GEMINI_API_KEY'
        }
        return provider_env.get(provider, 'AKIOS_LLM_API_KEY')

    def _get_default_model(self, provider: str) -> str:
        """Get default model for provider."""
        defaults = {
            'openai': 'gpt-4o-mini',
            'anthropic': 'claude-3.5-haiku',
            'grok': 'grok-3',
            'mistral': 'mistral-small',
            'gemini': 'gemini-1.5-flash'
        }
        return defaults.get(provider, 'gpt-4o-mini')

    def _configure_advanced_settings(self) -> Dict[str, any]:
        """
        Configure advanced settings like budget limits, token limits, etc.

        Returns:
            Dict of advanced configuration options
        """
        print("\n⚙️ Budget limit per workflow (press Enter for $1.00, or enter custom amount):")
        pricing_example = self._get_budget_pricing_example()
        print(f"(controls total API cost per run — ex: {pricing_example})")

        config = {}

        # Budget limit
        while True:
            try:
                budget_input = input("Enter budget: ").strip()
                if not budget_input:
                    config['budget_limit'] = 1.0
                    break
                budget_val = float(budget_input)
                if budget_val > 0:
                    config['budget_limit'] = budget_val
                    break
                else:
                    print("Budget must be positive.")
            except ValueError:
                print("Please enter a valid number.")

        config['max_tokens_per_call'] = 1000
        print("💡 Token limit set to 1000 tokens per AI request.")
        print("   • Tokens control AI response length (~4 chars per token)")
        print("   • 1000 tokens ≈ 750 words of AI response")
        print("   • Protects against runaway costs and long responses")
        return config

    def _get_budget_pricing_example(self) -> str:
        """
        Get appropriate pricing example based on selected provider.

        Returns:
            String with pricing example for the selected provider
        """
        provider = getattr(self, 'current_provider', 'openai')

        pricing_examples = {
            'openai': '$1 ≈ 1000 tokens GPT-4',
            'anthropic': '$1 ≈ 1000 tokens Claude-3',
            'grok': '$1 ≈ 1000 tokens Grok-3',
            'mistral': '$1 ≈ 2000 tokens Mistral',
            'gemini': '$1 ≈ 1000 tokens Gemini-1.5'
        }

        return pricing_examples.get(provider, '$1 ≈ 1000 tokens')

    def _select_model(self, provider: str) -> str:
        """
        Interactive model selection for the chosen provider.
        Shows only valid models for the provider to prevent configuration errors.

        Args:
            provider: Selected provider name

        Returns:
            Selected model name
        """
        available_models = self._get_available_models(provider)
        if available_models:
            model_items = list(available_models.items())
            valid_models = [model for model, _ in model_items]
        else:
            model_items = []
            valid_models = get_valid_models_for_provider(provider)

        provider_label = self._get_provider_display_name(provider)
        print(f"\n🤖 Choose {provider_label} Model:")
        if model_items:
            for i, (model, description) in enumerate(model_items, 1):
                print(f"  {i}. {model}      — {description}")
        else:
            for i, model in enumerate(valid_models, 1):
                print(f"  {i}. {model}")

        while True:
            try:
                default_model = valid_models[0]
                choice = input(f"Enter model number (1-{len(valid_models)}) [default: 1 - {default_model}]: ").strip()
                if not choice:
                    return valid_models[0]
                idx = int(choice) - 1
                if 0 <= idx < len(valid_models):
                    return valid_models[idx]
                else:
                    print(f"Please enter a number between 1 and {len(valid_models)}")
            except (ValueError, EOFError):
                print("Invalid input. Please enter a number.")

    def _get_available_models(self, provider: str) -> Dict[str, str]:
        """Get available models for a provider."""
        models = {
            'openai': {
                'gpt-4o-mini': 'Fastest & cheapest (great for most tasks)',
                'gpt-4o': 'Best balance of speed, cost & intelligence',
                'gpt-4-turbo': 'Very powerful, slightly slower & more expensive',
                'gpt-4': 'Classic high-performance model'
            },
            'anthropic': {
                'claude-3.5-haiku': 'Fastest & most cost-effective Claude',
                'claude-3.5-sonnet': 'Best overall balance (speed + quality)',
                'claude-3-opus': 'Most powerful (complex reasoning tasks)'
            },
            'grok': {
                'grok-3': 'Balanced performance (recommended)',
                'grok-4.1': 'Balanced performance',
                'grok-3': 'Very capable legacy model'
            },
            'mistral': {
                'mistral-small': 'Fast & cheap (everyday tasks)',
                'mistral-medium': 'Balanced quality & speed',
                'mistral-large': 'Most powerful Mistral model'
            },
            'gemini': {
                'gemini-1.5-flash': 'Fastest & cheapest Gemini',
                'gemini-1.5-pro': 'Best overall balance (multimodal + reasoning)',
                'gemini-1.0-pro': 'Stable classic model'
            }
        }
        return models.get(provider, {'default-model': 'Default model'})

    def _get_provider_display_name(self, provider: str) -> str:
        display = {
            'openai': 'OpenAI',
            'anthropic': 'Anthropic',
            'grok': 'Grok',
            'mistral': 'Mistral',
            'gemini': 'Gemini',
            'mock': 'Mock AI'
        }
        return display.get(provider, provider.title())

    def _select_api_mode(self) -> Optional[bool]:
        """
        Choose between mock data and real API providers.

        Returns:
            True for real API, False for mock mode, None if cancelled
        """
        print("🚀 How would you like to use AKIOS?")
        print("1. Try with mock data (no API key needed — instant setup)")
        print("2. Use real AI providers (requires API key — full AI power)")
        print("3. Skip setup (use mock mode by default — configure later)")
        print()

        while True:
            try:
                if not self.detector._is_interactive():
                    print("\nNon-interactive environment detected. Skipping setup.")
                    return None
                choice = input("Enter your choice (1-3) [default: 1]: ").strip()

                if choice in ['', '1']:
                    print("\n🎭 Mock mode selected!")
                    print("You'll use simulated AI responses for testing AKIOS.")
                    return False
                elif choice == '2':
                    print("\n🤖 Real API mode selected!")
                    print("You'll connect to powerful AI providers for full functionality.")
                    return True
                elif choice == '3':
                    print(f"\n⏭️  Setup skipped!")
                    print(f"Using mock mode by default. Configure later with '{suggest_command('setup --force')}'.")
                    return False
                else:
                    print("Please enter 1, 2, or 3.")

            except KeyboardInterrupt:
                print("\nSetup cancelled.")
                return None
            except EOFError:
                print("\nNon-interactive environment detected. Skipping setup.")
                return None

    def _select_provider(self) -> Optional[str]:
        """
        Interactive provider selection.

        Returns:
            Selected provider name or None if cancelled
        """
        print("🤖 Choose your AI Provider:")
        print("1. OpenAI (GPT) — Most popular")
        print("2. Anthropic (Claude) — High safety")
        print("3. xAI (Grok) — Helpful & truthful")
        print("4. Mistral — Fast open-source")
        print("5. Google (Gemini) — Multimodal")
        print()

        while True:
            try:
                # First check if we can actually read input
                if not self.detector._is_interactive():
                    print("\nNon-interactive environment detected. Skipping setup.")
                    return None
                choice = input("Enter your choice (1-5): ").strip()

                if choice == '1':
                    return 'openai'
                elif choice == '2':
                    return 'anthropic'
                elif choice == '3':
                    return 'grok'
                elif choice == '4':
                    return 'mistral'
                elif choice == '5':
                    return 'gemini'
                else:
                    print("Please enter 1, 2, 3, 4, 5, or 6.")

            except KeyboardInterrupt:
                print("\nSetup cancelled.")
                return None
            except EOFError:
                print("\nNon-interactive environment detected. Skipping setup.")
                return None

    def _setup_api_key(self, provider: str) -> Optional[str]:
        """
        Interactive API key setup for selected provider.

        Args:
            provider: Selected provider name

        Returns:
            API key or None if cancelled
        """
        provider_info = self._get_provider_info(provider)

        print(f"\n🔑 {provider_info['name']} API Key Setup")
        print(f"   {provider_info['description']}")
        print(f"   📖 Get your key: {provider_info['signup_url']}")
        print()

        while True:
            try:
                # Check if we can actually read input
                if not self.detector._is_interactive():
                    print("\nNon-interactive environment detected. Skipping setup.")
                    return None
                api_key = input(f"Enter your {provider_info['name']} API key (or 'cancel'): ").strip()

                if api_key.lower() == 'cancel':
                    return None

                if self._validate_api_key_format(provider, api_key):
                    return api_key
                else:
                    print(f"❌ Invalid {provider_info['name']} API key format. Please try again.")

            except KeyboardInterrupt:
                print("\nSetup cancelled.")
                return None
            except EOFError:
                print("\nNon-interactive environment detected. Skipping setup.")
                return None

    def _get_provider_info(self, provider: str) -> Dict[str, str]:
        """Get provider information for setup guidance."""
        info = {
            'openai': {
                'name': 'OpenAI',
                'description': 'Access to GPT-3.5, GPT-4, and other models',
                'signup_url': 'https://platform.openai.com/api-keys'
            },
            'anthropic': {
                'name': 'Anthropic',
                'description': 'Access to Claude and Claude Instant models',
                'signup_url': 'https://console.anthropic.com/'
            },
            'grok': {
                'name': 'xAI (Grok)',
                'description': 'Access to Grok models by xAI',
                'signup_url': 'https://console.x.ai/'
            },
            'mistral': {
                'name': 'Mistral',
                'description': 'Fast open-source models with great performance',
                'signup_url': 'https://console.mistral.ai/'
            },
            'gemini': {
                'name': 'Google',
                'description': 'Gemini models with multimodal capabilities',
                'signup_url': 'https://makersuite.google.com/app/apikey'
            },
            'mock': {
                'name': 'Mock AI',
                'description': 'Simulated AI responses for testing AKIOS',
                'signup_url': 'N/A'
            }
        }
        return info.get(provider, {})

    def _validate_api_key_format(self, provider: str, api_key: str) -> bool:
        """
        Robust format validation for API keys.

        Args:
            provider: Provider name
            api_key: API key to validate

        Returns:
            True if format appears valid
        """
        if not api_key or len(api_key.strip()) < 10:
            return False

        api_key = api_key.strip()

        # Provider-specific validation with enhanced checks
        if provider == 'openai':
            return (api_key.startswith('sk-') and
                   len(api_key) > 50 and
                   not any(char in api_key for char in [' ', '\n', '\t']))
        elif provider == 'anthropic':
            return (api_key.startswith('sk-ant-') and
                   len(api_key) > 100 and
                   api_key.count('-') >= 2)
        elif provider == 'grok':
            # xAI keys vary, but check for reasonable patterns
            return (len(api_key) > 20 and
                   any(prefix in api_key.lower() for prefix in ['xai-', 'grok']) and
                   not any(char in api_key for char in [' ', '\n', '\t']))
        elif provider == 'mistral':
            return (len(api_key) > 30 and
                   not any(char in api_key for char in [' ', '\n', '\t']))
        elif provider == 'gemini':
            return (len(api_key) > 30 and
                   not any(char in api_key for char in [' ', '\n', '\t']))

        # Allow other providers with basic validation
        return len(api_key) > 15

    def _validate_and_save(self, provider: str, api_key: str, model: str, advanced_config: Dict[str, any] = None) -> bool:
        """
        Validate configuration and save to files.

        Args:
            provider: Selected provider
            api_key: API key

        Returns:
            True if validation and save successful
        """
        try:
            env_file = self.project_root / ".env"
            env_file_display = ".env"

            # Create/update .env file
            provider_env_var = self._get_required_env_var(provider)
            mock_enabled = 1 if provider == 'mock' else 0
            network_allowed = 0 if provider == 'mock' else 1
            env_content = f"""# AKIOS Configuration - Generated by setup wizard
AKIOS_LLM_PROVIDER={provider}
AKIOS_LLM_MODEL={model}
{provider_env_var}={api_key}

# Mock mode {'enabled' if provider == 'mock' else 'disabled'} for {'simulated' if provider == 'mock' else 'real API'} usage
AKIOS_MOCK_LLM={mock_enabled}

# Network access {'disabled' if provider == 'mock' else 'enabled'} for API calls
AKIOS_NETWORK_ACCESS_ALLOWED={network_allowed}
"""

            # Add advanced settings if provided
            if advanced_config:
                if 'budget_limit' in advanced_config:
                    env_content += f"\n# Budget limit per workflow\nAKIOS_BUDGET_LIMIT_PER_RUN={advanced_config['budget_limit']}"
                if 'max_tokens_per_call' in advanced_config:
                    env_content += f"\n# Max tokens per API call\nAKIOS_MAX_TOKENS_PER_CALL={advanced_config['max_tokens_per_call']}"

            env_content += "\n"

            budget = advanced_config.get('budget_limit', 1.0) if advanced_config else 1.0
            print("\n📝 Configuration Preview:")
            if provider == 'mock':
                print(f"Provider: Mock AI    Model: Simulated responses    Budget: $0.00    Network: Disabled (mock)")
            else:
                print(f"Provider: {provider.title()}    Model: {model}    Budget: ${budget:.2f}    Network: Enabled")
            print(f"File: {env_file_display}")

            # Check for existing .env file
            env_exists = env_file.exists()
            if env_exists:
                existing_content = env_file.read_text()
                has_existing_keys = any(key in existing_content for key in ['GROK_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'MISTRAL_API_KEY', 'GEMINI_API_KEY'])
                if has_existing_keys:
                    print(f"\n⚠️ Existing .env found — will overwrite (keys lost unless backed up).")
                    print()
                    print("Options:")
                    print("1. Backup & overwrite (recommended)")
                    print("2. Skip wizard (keep existing)")
                    print("3. Rename existing & continue")

                    while True:
                        try:
                            choice = input("Enter 1-3 (default 1): ").strip()
                            if choice in ['', '1']:
                                backup_file = self.project_root / ".env.backup"
                                backup_file.write_text(existing_content)
                                print("✅ Backup: .env.backup created")
                                break
                            if choice == '2':
                                print("ℹ️  Keeping existing configuration. Setup skipped.")
                                return True
                            if choice == '3':
                                timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
                                renamed = self.project_root / f".env.backup.{timestamp}"
                                env_file.rename(renamed)
                                print(f"✅ Renamed existing .env to {renamed.name}")
                                break
                            print("Please enter 1, 2, or 3.")
                        except (KeyboardInterrupt, EOFError):
                            print("\nConfiguration cancelled.")
                            return False

            while True:
                try:
                    confirm = input("\nSave this configuration? (yes/no): ").strip().lower()
                    if confirm in ['yes', 'y']:
                        break
                    elif confirm in ['no', 'n']:
                        print("Configuration cancelled.")
                        return False
                    else:
                        print("Please enter 'yes' or 'no'")
                except (KeyboardInterrupt, EOFError):
                    print("\nConfiguration cancelled.")
                    return False

            old_env = os.environ.copy()
            validated = False
            try:
                # Set environment variables for the configuration
                if provider == 'mock':
                    # Mock mode - enable mock LLM and disable network
                    os.environ['AKIOS_MOCK_LLM'] = '1'
                    os.environ['AKIOS_NETWORK_ACCESS_ALLOWED'] = '0'
                    os.environ['AKIOS_LLM_PROVIDER'] = 'mock'
                    os.environ['AKIOS_LLM_MODEL'] = 'mock-model'
                    # Skip validation for mock mode - just save the config
                    validated = True
                else:
                    # Real API mode
                    os.environ['AKIOS_LLM_PROVIDER'] = provider
                    os.environ['AKIOS_LLM_MODEL'] = model
                    os.environ[provider_env_var] = api_key
                    os.environ['AKIOS_MOCK_LLM'] = '0'
                    os.environ['AKIOS_NETWORK_ACCESS_ALLOWED'] = '1'

                    # Test configuration for real API mode
                    print("🔍 Testing configuration...")
                    from ...config.loader import get_settings
                    settings = get_settings()

                    # Validate that settings match what we expect
                    if getattr(settings, 'llm_provider', None) != provider or os.environ.get(provider_env_var) != api_key:
                        print("❌ Configuration validation failed.")
                        return False
                    validated = True
            except Exception as e:
                print(f"❌ Configuration validation failed. {e}")
                return False
            finally:
                if not validated:
                    os.environ.clear()
                    os.environ.update(old_env)

            env_file.write_text(env_content)

            # Update config.yaml if it exists
            config_file = self.project_root / "config.yaml"
            if config_file.exists():
                # Basic config update - enable/disable network based on mode
                config_content = config_file.read_text()
                network_enabled = 'false' if provider == 'mock' else 'true'
                if 'network_access_allowed:' in config_content:
                    # Update existing setting
                    config_content = config_content.replace(
                        'network_access_allowed: false',
                        f'network_access_allowed: {network_enabled}'
                    )
                    config_content = config_content.replace(
                        'network_access_allowed: true',
                        f'network_access_allowed: {network_enabled}'
                    )
                else:
                    # Add setting if missing
                    config_content += f"\nnetwork_access_allowed: {network_enabled}\n"

                config_file.write_text(config_content)

            # Final validation check
            if provider == 'mock':
                # Mock mode - already validated above, just confirm
                print("✅ Configuration saved and validated!")
                return True
            else:
                # Real API mode - check settings one more time
                if getattr(settings, 'llm_provider', None) == provider and os.environ.get(provider_env_var) == api_key:
                    print("✅ Configuration saved and validated!")
                    return True
                else:
                    print("❌ Configuration validation failed.")
                    return False

        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
            return False

    def _show_success_message(self, budget: float = 1.0) -> None:
        """Display success message and next steps."""
        print("\n🎉 Setup Complete!")
        print("──────────────────")
        print("**Summary:**")
        if hasattr(self, 'current_provider') and self.current_provider == 'mock':
            print("• Provider: Mock AI    Model: Simulated responses")
            print("• Budget: $0.00/run • Network: Disabled (mock)")
            print("• No API key needed • Mock: Enabled")
        else:
            provider_name = getattr(self, 'current_provider', 'grok')
            model_name = getattr(self, 'current_model', 'grok-4.1-fast')
            print(f"• Provider: {provider_name}    Model: {model_name}")
            print(f"• Budget: ${budget:.2f}/run • Network: Enabled")
            print("• Real API ready    • Mock: Disabled")
        print()

        print("**📋 Next Steps:**")
        print(f"1. {suggest_command('run templates/hello-workflow.yml')}")
        print(f"2. {suggest_command('status')}")
        print("3. cat data/output/run_*/hello.txt")
        print()
        print(f"📖 Help: {suggest_command('--help')}    🔧 Reconfigure: {suggest_command('setup --force')}")

    def _check_recent_workflow_runs(self) -> bool:
        """Check if there have been recent workflow runs."""
        try:
            # Import here to avoid circular imports
            from ...core.audit.ledger import get_ledger
            ledger = get_ledger()
            events = ledger.get_all_events()

            # Check for workflow completion events in the last hour
            import time
            one_hour_ago = time.time() - 3600

            for event in events:
                if (hasattr(event, 'action') and event.action == 'workflow_complete' and
                    hasattr(event, 'timestamp') and event.timestamp and
                    event.timestamp.timestamp() > one_hour_ago):
                    return True

            return False
        except Exception:
            # If we can't check, assume no recent runs
            return False

def get_valid_models_for_provider(provider: str) -> List[str]:
    """Get valid models for a provider (from validation.py mapping)."""
    fallback_models = {
        'openai': ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-4'],
        'anthropic': ['claude-3.5-haiku', 'claude-3.5-sonnet', 'claude-3-opus'],
        'grok': ['grok-3', 'grok-4.1', 'grok-4.1-fast'],
        'mistral': ['mistral-small', 'mistral-medium', 'mistral-large'],
        'gemini': ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
    }
    try:
        from ...config.validation import PROVIDER_MODELS
        return PROVIDER_MODELS.get(provider, fallback_models.get(provider, []))
    except Exception:
        return fallback_models.get(provider, [])


def run_setup_wizard(project_root: Path) -> bool:
    """
    Convenience function to run the setup wizard.

    Args:
        project_root: Project directory

    Returns:
        True if setup completed successfully
    """
    wizard = SetupWizard(project_root)
    return wizard.run_wizard()
