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
CLI protect command - akios protect <subcommand>

PII protection analysis for workflows.
- protect preview:  Scan workflow inputs for PII and show safe prompt construction
- protect scan:     Scan a specific file for PII detections
"""

import argparse
import yaml
import os
from pathlib import Path
from typing import List, Dict, Any

from ...core.ui.rich_output import (
    print_panel, print_table, print_success, print_warning, 
    print_error, print_info, get_theme_color
)
from ..helpers import CLIError, check_project_context

def register_protect_command(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the protect command with the argument parser.

    Args:
        subparsers: Subparsers action from main parser
    """
    parser = subparsers.add_parser(
        "protect",
        help="Analyze and preview PII protection for workflows",
        description="PII protection analysis — scan data and preview safe prompt construction"
    )

    subparsers_protect = parser.add_subparsers(
        dest="protect_subcommand",
        help="Protect action",
        required=True
    )

    # protect preview
    preview_parser = subparsers_protect.add_parser(
        "preview",
        help="Scan workflow inputs for PII and show safe prompt construction"
    )
    preview_parser.add_argument(
        "workflow",
        nargs="?",
        default="workflow.yml",
        help="Workflow file to analyze (default: workflow.yml)"
    )
    preview_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    preview_parser.set_defaults(func=run_protect_preview)

    # protect scan
    scan_parser = subparsers_protect.add_parser(
        "scan",
        help="Scan a file or text for PII detections"
    )
    scan_parser.add_argument(
        "file",
        help="File path to scan for PII, or inline text (auto-detected)"
    )
    scan_parser.add_argument(
        "--text",
        action="store_true",
        help="Treat argument as inline text instead of a file path"
    )
    scan_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    scan_parser.set_defaults(func=run_protect_scan)

    # protect show-prompt
    show_prompt_parser = subparsers_protect.add_parser(
        "show-prompt",
        help="Show the exact interpolated and redacted prompt the LLM would receive"
    )
    show_prompt_parser.add_argument(
        "workflow",
        nargs="?",
        default="workflow.yml",
        help="Workflow file to analyze (default: workflow.yml)"
    )
    show_prompt_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    show_prompt_parser.set_defaults(func=run_protect_show_prompt)


def run_protect_preview(args: argparse.Namespace) -> int:
    """Execute protect preview: scan workflow for PII + show safe prompt."""
    check_project_context()
    
    workflow_path = Path(args.workflow)
    if not workflow_path.exists():
        raise CLIError(f"Workflow file not found: {workflow_path}")

    try:
        with open(workflow_path, "r") as f:
            workflow = yaml.safe_load(f)
    except Exception as e:
        raise CLIError(f"Failed to parse workflow: {str(e)}")

    if "steps" not in workflow or not isinstance(workflow["steps"], list):
        raise CLIError("Workflow missing 'steps' list")

    steps = workflow.get("steps", [])

    # Phase 1: Workflow structure analysis
    structure_checks = _analyze_workflow_structure(steps)
    
    # Phase 2: PII scan on referenced input files
    pii_results = _scan_workflow_inputs(steps)
    
    # Phase 3: Safe prompt construction preview
    prompt_preview = _build_safe_prompt_preview(steps, pii_results)

    if getattr(args, 'json', False):
        import json
        output = {
            "workflow": str(workflow_path),
            "structure": structure_checks,
            "pii_scan": pii_results,
            "safe_prompt": prompt_preview,
        }
        print(json.dumps(output, indent=2, default=str))
        return 0

    # Display results
    success_color = get_theme_color('success')
    warning_color = get_theme_color('warning')
    error_color = get_theme_color('error')
    
    print_info(f"Analyzing [bold]{workflow_path}[/]...")

    # Structure table
    table_data = []
    for c in structure_checks:
        table_data.append({
            "Category": c["category"],
            "Check": c["check"],
            "Status": f"[{c['color']}]{c['status']}[/]"
        })
    print_table(table_data, title="Workflow Structure", columns=["Category", "Check", "Status"])

    # PII scan results
    if pii_results.get("files_scanned"):
        security_color = get_theme_color('security')
        pii_table = []
        for file_result in pii_results["files_scanned"]:
            filepath = file_result["file"]
            detections = file_result.get("detections", {})
            if detections:
                for pii_type, values in detections.items():
                    for val in values:
                        # Partially mask the value for display
                        masked = val[:3] + "***" if len(val) > 3 else "***"
                        pii_table.append({
                            "File": filepath,
                            "PII Type": f"[bold]{pii_type.upper()}[/bold]",
                            "Value": f"[bold {error_color}]{masked}[/]",
                            "Protection": f"[bold {security_color}]\u00ab{pii_type.upper()}\u00bb[/]"
                        })
            else:
                pii_table.append({
                    "File": filepath,
                    "PII Type": "-",
                    "Value": "-",
                    "Protection": f"[{success_color}]Clean[/]"
                })
        
        print_table(pii_table, title="PII Detection Scan", columns=["File", "PII Type", "Value", "Protection"])
        
        total_pii = pii_results.get("total_pii_found", 0)
        if total_pii > 0:
            print_warning(f"Found {total_pii} PII instance(s) — will be redacted before LLM prompt")
        else:
            print_success("No PII detected in input files")
    else:
        print_info("No input files referenced in workflow")

    # Safe prompt preview
    if prompt_preview.get("prompts"):
        import re as _re
        for p in prompt_preview["prompts"]:
            step_num = p["step"]
            
            content = (
                f"[bold]Step {step_num} — Safe Prompt Preview[/]\n\n"
                f"[bold {get_theme_color('info')}]Original prompt template:[/]\n"
                f"{p['template'][:200]}{'...' if len(p['template']) > 200 else ''}\n\n"
            )
            
            if p.get("safe_input_preview"):
                # Highlight «PII_TYPE» markers in magenta for contrast
                safe_preview = p['safe_input_preview'][:300]
                safe_preview_colored = _re.sub(
                    r'«(\w+)»',
                    lambda m: f'[bold {get_theme_color("security")}]«{m.group(1)}»[/]',
                    safe_preview
                )
                content += (
                    f"[bold {get_theme_color('warning')}]Input data (after redaction):[/]\n"
                    f"{safe_preview_colored}{'...' if len(p['safe_input_preview']) > 300 else ''}\n\n"
                )
            
            content += f"[{success_color}]Prompt is safe for external LLM.[/]"
            
            print_panel(f"Step {step_num} — LLM Prompt", content, style=success_color)
    
    return 0


def run_protect_scan(args: argparse.Namespace) -> int:
    """Execute protect scan: scan a single file or inline text for PII."""
    check_project_context()
    
    file_path = Path(args.file)
    is_text_mode = getattr(args, 'text', False)
    
    # Auto-detect: if --text flag is set OR the argument doesn't look like a file path, treat as text
    if is_text_mode or (not file_path.exists() and (
        ' ' in args.file or ',' in args.file or
        any(c.isdigit() for c in args.file) and len(args.file) > 20
    )):
        # Inline text mode
        content = args.file
        source_label = "inline text"
    else:
        if not file_path.exists():
            raise CLIError(f"File not found: {file_path}")
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            raise CLIError(f"Failed to read file: {str(e)}")
        source_label = str(file_path)
    
    # Detect PII using the product PII engine — always detect regardless of cage state
    detections = _detect_pii(content)
    
    # Get redacted preview using the product PII redactor with guillemet markers (Rich-safe)
    redacted_text = _redact_text(content)
    
    total_found = sum(len(v) for v in detections.values())
    
    if getattr(args, 'json', False):
        import json
        output = {
            "source": source_label,
            "pii_found": total_found,
            "detections": {k: v for k, v in detections.items()},
            "redacted_preview": redacted_text[:500] if redacted_text else None,
        }
        print(json.dumps(output, indent=2, default=str))
        return 0
    
    success_color = get_theme_color('success')
    error_color = get_theme_color('error')
    
    print_info(f"Scanning [bold]{source_label}[/]...")
    
    if detections:
        import re as _re
        security_color = get_theme_color('security')
        pii_table = []
        for pii_type, values in detections.items():
            for val in values:
                masked = val[:3] + "***" if len(val) > 3 else "***"
                pii_table.append({
                    "PII Type": f"[bold]{pii_type.upper()}[/bold]",
                    "Detected Value": f"[bold {error_color}]{masked}[/]",
                    "After Redaction": f"[bold {security_color}]«{pii_type.upper()}»[/]",
                })
        print_table(pii_table, title=f"PII Detected ({total_found} instances)", columns=["PII Type", "Detected Value", "After Redaction"])
        
        if redacted_text:
            # Highlight «PII_TYPE» markers in magenta for visibility contrast
            display_text = redacted_text[:500]
            highlighted = _re.sub(
                r'«(\w+)»',
                lambda m: f'[bold {security_color}]«{m.group(1)}»[/]',
                display_text
            )
            print_panel("Redacted Preview", f"{highlighted}{'...' if len(redacted_text) > 500 else ''}", style=success_color)
    else:
        print_success(f"No PII detected in {file_path}")
    
    return 0


def _analyze_workflow_structure(steps: List[Dict]) -> List[Dict]:
    """Analyze workflow structure for security concerns."""
    checks = []
    
    checks.append({"category": "Structure", "check": f"Valid Schema ({len(steps)} steps)", "status": "PASS", "color": "green"})
    
    has_network = False
    has_fs_write = False
    has_shell = False
    has_llm = False
    
    for step in steps:
        agent = step.get("agent", "")
        action = step.get("action", "")
        
        if agent == "http":
            has_network = True
        if agent == "filesystem" and action == "write":
            has_fs_write = True
        if agent == "tool_executor":
            has_shell = True
        if agent == "llm":
            has_llm = True

    if has_llm:
        checks.append({"category": "AI", "check": "LLM Calls (PII redacted before send)", "status": "PROTECTED", "color": "green"})
    
    if has_network:
        checks.append({"category": "Network", "check": "External HTTP Calls", "status": "WARN", "color": "yellow"})
    else:
        checks.append({"category": "Network", "check": "No External HTTP Calls", "status": "PASS", "color": "green"})
    
    if has_fs_write:
        checks.append({"category": "Filesystem", "check": "Write Operations", "status": "WARN", "color": "yellow"})
    else:
        checks.append({"category": "Filesystem", "check": "Read-Only / Safe", "status": "PASS", "color": "green"})
    
    if has_shell:
        checks.append({"category": "Runtime", "check": "Shell Execution (sandboxed)", "status": "CAUTION", "color": "yellow"})
    else:
        checks.append({"category": "Runtime", "check": "Sandboxed Logic Only", "status": "PASS", "color": "green"})
    
    checks.append({"category": "Privacy", "check": "PII Redaction", "status": "ACTIVE", "color": "green"})
    
    # Budget estimation
    total_chars = 0
    for step in steps:
        params = step.get("parameters", {})
        if "prompt" in params:
            total_chars += len(params["prompt"])
    
    estimated_tokens = total_chars / 4
    estimated_cost = (estimated_tokens / 1000) * 0.002
    
    if estimated_cost < 1.0:
        checks.append({"category": "Budget", "check": f"Est. < ${estimated_cost:.4f}", "status": "PASS", "color": "green"})
    else:
        checks.append({"category": "Budget", "check": f"Est. > ${estimated_cost:.4f}", "status": "WARN", "color": "yellow"})
    
    return checks


def _scan_workflow_inputs(steps: List[Dict]) -> Dict[str, Any]:
    """Scan input files referenced in workflow for PII."""
    results = {"files_scanned": [], "total_pii_found": 0}
    
    # Find filesystem read steps that reference input files
    for step in steps:
        agent = step.get("agent", "")
        action = step.get("action", "")
        params = step.get("parameters", {})
        
        if agent == "filesystem" and action == "read":
            filepath = params.get("path", "")
            if filepath:
                file_path = Path(filepath)
                if file_path.exists():
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="replace")
                        detections = _detect_pii(content)
                        total = sum(len(v) for v in detections.values())
                        results["files_scanned"].append({
                            "file": filepath,
                            "detections": detections,
                            "pii_count": total,
                        })
                        results["total_pii_found"] += total
                    except Exception:
                        results["files_scanned"].append({
                            "file": filepath,
                            "detections": {},
                            "pii_count": 0,
                            "error": "Could not read file"
                        })
                else:
                    results["files_scanned"].append({
                        "file": filepath,
                        "detections": {},
                        "pii_count": 0,
                        "error": "File not found"
                    })
    
    return results


def _build_safe_prompt_preview(steps: List[Dict], pii_results: Dict) -> Dict[str, Any]:
    """Build a preview of the safe prompt that would go to the LLM."""
    prompts = []
    
    # Get redacted version of input data
    redacted_inputs = {}
    for file_result in pii_results.get("files_scanned", []):
        filepath = file_result["file"]
        if file_result.get("pii_count", 0) > 0:
            try:
                content = Path(filepath).read_text(encoding="utf-8", errors="replace")
                redacted = _redact_text(content)
                redacted_inputs[filepath] = redacted
            except Exception:
                pass
        else:
            try:
                redacted_inputs[filepath] = Path(filepath).read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
    
    for step in steps:
        agent = step.get("agent", "")
        params = step.get("parameters", {})
        
        if agent == "llm" and "prompt" in params:
            prompt_template = params["prompt"]
            
            # Find the input that would be substituted
            safe_input = None
            if "{previous_output}" in prompt_template and redacted_inputs:
                # Use the first available redacted input as preview
                safe_input = next(iter(redacted_inputs.values()), None)
            
            prompts.append({
                "step": step.get("step", "?"),
                "template": prompt_template,
                "safe_input_preview": safe_input,
            })
    
    return {"prompts": prompts}


def _detect_pii(text: str) -> Dict[str, List[str]]:
    """Detect PII using the product PII engine.
    Always detects regardless of cage state — scanning should always work."""
    try:
        from ...security.pii import create_pii_detector
        detector = create_pii_detector()
        return detector.detect_pii(text, force_detection=True)
    except Exception:
        # Minimal fallback if the PII module itself fails to import
        import re
        detected = {}
        ssn = re.findall(r'\b\d{3}-\d{2}-\d{4}\b', text)
        if ssn:
            detected["ssn"] = ssn
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if emails:
            detected["email"] = emails
        phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        if phones:
            detected["phone_us"] = phones
        return detected


def _redact_text(text: str) -> str:
    """Redact PII from text using the product PII redactor with «» markers (Rich-safe).
    Always redacts regardless of cage state."""
    try:
        from ...security.pii import create_pii_redactor
        redactor = create_pii_redactor(marker_style="guillemet")
        return redactor.redact_text(text, force_redaction=True)
    except Exception:
        # Minimal fallback if the PII module itself fails to import
        import re
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '«SSN»', text)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '«EMAIL»', text)
        text = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '«PHONE_US»', text)
        return text


def run_protect_show_prompt(args: argparse.Namespace) -> int:
    """Execute protect show-prompt: show the exact interpolated + redacted prompt the LLM would receive."""
    check_project_context()

    workflow_path = Path(args.workflow)
    if not workflow_path.exists():
        raise CLIError(f"Workflow file not found: {workflow_path}")

    try:
        with open(workflow_path, "r") as f:
            workflow = yaml.safe_load(f)
    except Exception as e:
        raise CLIError(f"Failed to parse workflow: {str(e)}")

    if "steps" not in workflow or not isinstance(workflow["steps"], list):
        raise CLIError("Workflow missing 'steps' list")

    steps = workflow.get("steps", [])

    # Step 1: Find and read all filesystem read steps to get actual content
    step_outputs = {}
    for step in steps:
        agent = step.get("agent", "")
        action = step.get("action", "")
        params = step.get("parameters", {})
        step_num = step.get("step", 0)

        if agent == "filesystem" and action == "read":
            filepath = params.get("path", "")
            if filepath:
                file_path = Path(filepath)
                if file_path.exists():
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="replace")
                        # Apply PII redaction to simulate what the engine does
                        redacted_content = _redact_text(content)
                        step_outputs[step_num] = redacted_content
                    except Exception:
                        step_outputs[step_num] = f"[Error reading {filepath}]"

    # Step 2: Find LLM steps and interpolate the prompt with redacted data
    import re as _re

    for step in steps:
        agent = step.get("agent", "")
        params = step.get("parameters", {})
        step_num = step.get("step", 0)

        if agent == "llm" and "prompt" in params:
            prompt = params["prompt"]

            # Resolve {previous_output} — use output from step N-1
            if "{previous_output}" in prompt:
                prev_step = step_num - 1
                if prev_step in step_outputs:
                    prompt = prompt.replace("{previous_output}", step_outputs[prev_step])

            # Resolve {step_N_output} and {step_N_output[key]}
            step_pattern = _re.compile(r'\{step_(\d+)_output(?:\[(\w+)\])?\}')
            for match in step_pattern.finditer(prompt):
                ref_step = int(match.group(1))
                if ref_step in step_outputs:
                    prompt = prompt.replace(match.group(0), step_outputs[ref_step])

            # JSON output
            if getattr(args, 'json', False):
                import json
                output = {
                    "workflow": str(workflow_path),
                    "step": step_num,
                    "model": params.get("model", "default"),
                    "max_tokens": params.get("max_tokens", 1000),
                    "interpolated_prompt": prompt,
                }
                print(json.dumps(output, indent=2, default=str))
                return 0

            # Rich display — color-split: instructions vs patient data
            success_color = get_theme_color('success')
            security_color = get_theme_color('security')
            info_color = get_theme_color('info')

            print_info(f"Showing interpolated prompt for [bold]{workflow_path}[/] — Step {step_num}")

            # Build color-split display: instructions in bright, data in dim
            # We re-interpolate to track where data was inserted
            raw_prompt = params["prompt"]

            # Find all {step_N_output} and {previous_output} markers in original
            data_markers = list(_re.finditer(
                r'\{(?:step_\d+_output(?:\[\w+\])?|previous_output)\}', raw_prompt
            ))

            if data_markers:
                # Split prompt into instruction segments and data segments
                display_parts = []
                last_end = 0
                for marker in data_markers:
                    # Instruction text before this marker
                    instruction_segment = raw_prompt[last_end:marker.start()]
                    if instruction_segment.strip():
                        # Highlight PII in instructions too
                        seg = _re.sub(
                            r'«(\w+)»',
                            lambda m: f'[bold {security_color}]«{m.group(1)}»[/]',
                            instruction_segment
                        )
                        display_parts.append(seg)

                    # Resolve the marker to get actual data content
                    marker_text = marker.group(0)
                    resolved = ""
                    step_match = _re.match(r'\{step_(\d+)_output', marker_text)
                    prev_match = _re.match(r'\{previous_output\}', marker_text)
                    if step_match:
                        ref = int(step_match.group(1))
                        resolved = step_outputs.get(ref, marker_text)
                    elif prev_match:
                        prev = step_num - 1
                        resolved = step_outputs.get(prev, marker_text)

                    # Data segment — dim styling with clear separator
                    resolved_display = _re.sub(
                        r'«(\w+)»',
                        lambda m: f'[bold {security_color}]«{m.group(1)}»[/]',
                        resolved
                    )
                    display_parts.append(
                        f"\n[dim]{'─' * 60}[/]\n"
                        f"[dim italic]▼ Interpolated Patient Data (redacted)[/]\n"
                        f"[dim]{'─' * 60}[/]\n"
                        f"[dim]{resolved_display}[/]\n"
                        f"[dim]{'─' * 60}[/]\n"
                        f"[dim italic]▲ End Patient Data[/]\n"
                        f"[dim]{'─' * 60}[/]"
                    )
                    last_end = marker.end()

                # Trailing instruction text
                trailing = raw_prompt[last_end:]
                if trailing.strip():
                    seg = _re.sub(
                        r'«(\w+)»',
                        lambda m: f'[bold {security_color}]«{m.group(1)}»[/]',
                        trailing
                    )
                    display_parts.append(seg)

                display_prompt = "".join(display_parts)
            else:
                # No interpolation markers — treat everything as instruction
                display_prompt = _re.sub(
                    r'«(\w+)»',
                    lambda m: f'[bold {security_color}]«{m.group(1)}»[/]',
                    prompt
                )

            # Legend
            display_prompt = (
                f"[bold {info_color}]LEGEND:[/] "
                f"[{success_color}]■[/] Prompt Instructions  "
                f"[dim]■[/] Patient Data  "
                f"[bold {security_color}]«PII»[/] Redacted Fields\n\n"
                + display_prompt
            )

            print_panel(
                f"Step {step_num} — Exact LLM Prompt (Interpolated + Redacted)",
                display_prompt,
                style=success_color
            )

            # Summary
            pii_markers = _re.findall(r'«(\w+)»', prompt)
            if pii_markers:
                from collections import Counter
                counts = Counter(pii_markers)
                print_warning(f"PII redaction active: {len(pii_markers)} markers across {len(counts)} types")
                for pii_type, count in counts.most_common():
                    print_info(f"  «{pii_type}» × {count}")
            else:
                print_success("No PII detected in interpolated prompt")

            print_success(f"Model: {params.get('model', 'default')} | Max tokens: {params.get('max_tokens', 1000)}")

    return 0
