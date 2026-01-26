"""
Output Manager - Enhanced output organization and accessibility

Provides user-friendly output directory management and human-readable directory naming
for AKIOS workflows.
"""

import time
from pathlib import Path
from typing import Optional, Dict, List, Any


class OutputManager:
    """
    Manages workflow output organization and accessibility.

    Features:
    - Human-readable directory naming
    - Output summary generation
    - Cross-platform compatibility
    """

    def __init__(self, base_output_dir: str = "./data/output"):
        """
        Initialize the output manager.

        Args:
            base_output_dir: Base directory for outputs (default: ./data/output)
        """
        self.base_output_dir = Path(base_output_dir)
    def create_output_directory(self, workflow_id: Optional[str] = None) -> Path:
        """
        Create a new output directory with human-readable naming and security hardening.

        SECURITY: Creates directories with restrictive permissions (0700) to prevent
        unauthorized access to workflow outputs.

        Args:
            workflow_id: Optional workflow ID to extract timestamp from

        Returns:
            Path to the created output directory
        """
        # Generate human-readable timestamp
        timestamp = self._extract_timestamp(workflow_id)
        human_readable = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(timestamp))

        # Create directory name
        dir_name = f"run_{human_readable}"
        output_dir = self.base_output_dir / dir_name

        # Ensure directory exists with restrictive permissions
        output_dir.mkdir(parents=True, exist_ok=True)

        # SECURITY: Set restrictive permissions (0700 - owner read/write/execute only)
        try:
            output_dir.chmod(0o700)
        except OSError:
            # Silently fail if chmod not supported (e.g., some Windows environments)
            pass

        return output_dir

    def _extract_timestamp(self, workflow_id: Optional[str] = None) -> float:
        """
        Extract timestamp from workflow ID or use current time.

        Args:
            workflow_id: Workflow ID in format "name_timestamp"

        Returns:
            Unix timestamp
        """
        if workflow_id:
            try:
                # Extract timestamp from workflow_id (format: "name_timestamp")
                timestamp_part = workflow_id.split('_')[-1]
                return float(timestamp_part)
            except (ValueError, IndexError):
                pass

        # Fallback to current time
        return time.time()

    def generate_output_summary(self, output_dir: Path, workflow_name: str = "workflow") -> str:
        """
        Generate a user-friendly summary of workflow outputs.

        Args:
            output_dir: Directory containing the outputs
            workflow_name: Name of the workflow for context

        Returns:
            Formatted summary string
        """
        summary_lines = []
        summary_lines.append(f"📄 {workflow_name.title()} results generated!")
        summary_lines.append("")
        summary_lines.append("📂 Output Locations:")

        try:
            # List all output files
            files_found = False
            for item in sorted(output_dir.iterdir()):
                if item.is_file():
                    size = self._format_file_size(item.stat().st_size)
                    summary_lines.append(f"  • {item.name} ({size})")
                    files_found = True

            if not files_found:
                summary_lines.append("  • No output files generated")

        except Exception:
            summary_lines.append("  • Unable to read output directory")

        return "\n".join(summary_lines)

    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Human-readable size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def cleanup_old_outputs(self, max_age_days: int = 30, max_directories: int = 50) -> None:
        """
        Clean up old output directories to prevent disk space issues.

        Args:
            max_age_days: Remove directories older than this many days
            max_directories: Keep at most this many recent directories
        """
        try:
            # Get all run directories
            run_dirs = []
            for item in self.base_output_dir.iterdir():
                if item.is_dir() and item.name.startswith('run_'):
                    try:
                        # Extract timestamp from directory name
                        timestamp_str = item.name.replace('run_', '')
                        timestamp = time.mktime(time.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S'))
                        run_dirs.append((timestamp, item))
                    except (ValueError, OSError):
                        continue

            # Sort by timestamp (newest first)
            run_dirs.sort(key=lambda x: x[0], reverse=True)

            # Remove old directories
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60

            to_remove = []
            for timestamp, directory in run_dirs[max_directories:]:  # Keep only newest N
                to_remove.append(directory)

            for timestamp, directory in run_dirs:
                if current_time - timestamp > max_age_seconds:  # Older than max age
                    to_remove.append(directory)

            # Remove duplicates and delete
            to_remove = list(set(to_remove))
            for directory in to_remove:
                try:
                    import shutil
                    shutil.rmtree(directory)
                except OSError:
                    pass  # Silently fail if deletion fails

        except Exception:
            # Silently fail if cleanup fails
            pass

    def get_all_outputs(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all workflow outputs organized by workflow name.

        Returns:
            Dictionary mapping workflow names to lists of output metadata
        """
        try:
            outputs = {}
            
            # Scan all run directories
            for item in self.base_output_dir.iterdir():
                if item.is_dir() and item.name.startswith('run_'):
                    try:
                        # Extract workflow name from directory contents
                        workflow_name = self._extract_workflow_from_output_dir(item)
                        if workflow_name:
                            if workflow_name not in outputs:
                                outputs[workflow_name] = []
                            
                            # Get output metadata
                            metadata = self._get_output_metadata(item)
                            if metadata:
                                outputs[workflow_name].append(metadata)
                    except Exception:
                        continue
            
            # Sort outputs by timestamp (newest first)
            for workflow in outputs:
                outputs[workflow].sort(key=lambda x: x['timestamp'], reverse=True)
            
            return outputs
            
        except Exception:
            return {}

    def get_workflow_outputs(self, workflow_name: str) -> List[Dict[str, Any]]:
        """
        Get outputs for a specific workflow.

        Args:
            workflow_name: Name of the workflow

        Returns:
            List of output metadata dictionaries
        """
        all_outputs = self.get_all_outputs()
        return all_outputs.get(workflow_name, [])

    def clean_workflow_outputs(self, workflow_name: str, max_age_days: int = 30, 
                             max_count: int = 50, dry_run: bool = False) -> Dict[str, Any]:
        """
        Clean old outputs for a specific workflow.

        Args:
            workflow_name: Name of the workflow to clean
            max_age_days: Maximum age in days
            max_count: Maximum number of executions to keep
            dry_run: If True, only report what would be cleaned

        Returns:
            Dictionary with cleanup results
        """
        try:
            workflow_outputs = self.get_workflow_outputs(workflow_name)
            if not workflow_outputs:
                return {
                    'scanned': 0,
                    'cleaned': 0,
                    'size_freed': 0,
                    'dry_run': dry_run
                }
            
            # Sort by timestamp (newest first)
            workflow_outputs.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Determine which outputs to remove
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            to_remove = []
            
            # Keep only max_count most recent
            for output in workflow_outputs[max_count:]:
                to_remove.append(output)
            
            # Remove outputs older than max_age_days
            for output in workflow_outputs:
                if current_time - output['timestamp'] > max_age_seconds:
                    if output not in to_remove:
                        to_remove.append(output)
            
            # Perform cleanup
            cleaned = 0
            size_freed = 0
            
            for output in to_remove:
                try:
                    output_dir = self.base_output_dir / f"run_{output['execution_id']}"
                    if output_dir.exists():
                        if not dry_run:
                            import shutil
                            shutil.rmtree(output_dir)
                        cleaned += 1
                        size_freed += output['total_size']
                except Exception:
                    continue
            
            return {
                'scanned': len(workflow_outputs),
                'cleaned': cleaned,
                'size_freed': size_freed,
                'dry_run': dry_run
            }
            
        except Exception:
            return {
                'scanned': 0,
                'cleaned': 0,
                'size_freed': 0,
                'dry_run': dry_run,
                'error': 'Failed to clean outputs'
            }

    def _extract_workflow_from_output_dir(self, output_dir: Path) -> Optional[str]:
        """
        Extract workflow name from output directory contents.
        
        Args:
            output_dir: Path to output directory
            
        Returns:
            Workflow name or None if cannot determine
        """
        try:
            # Look for workflow metadata files or naming patterns
            # For now, try to infer from directory contents
            for item in output_dir.iterdir():
                if item.is_file() and item.name.endswith('.json'):
                    # Could be workflow metadata
                    try:
                        import json
                        with open(item, 'r') as f:
                            data = json.load(f)
                            if 'workflow' in data:
                                return data['workflow']
                    except Exception:
                        continue
            
            # Fallback: use a generic name
            return "workflow"
            
        except Exception:
            return None

    def _get_output_metadata(self, output_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an output directory.
        
        Args:
            output_dir: Path to output directory
            
        Returns:
            Metadata dictionary or None if invalid
        """
        try:
            # Extract timestamp from directory name
            timestamp_str = output_dir.name.replace('run_', '')
            timestamp = time.mktime(time.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S'))
            
            # Count files and calculate total size
            file_count = 0
            total_size = 0
            
            for item in output_dir.rglob('*'):
                if item.is_file():
                    file_count += 1
                    total_size += item.stat().st_size
            
            return {
                'execution_id': output_dir.name,
                'timestamp': timestamp,
                'file_count': file_count,
                'total_size': total_size,
                'directory': str(output_dir)
            }
            
        except Exception:
            return None


# Global instance for easy access
output_manager = OutputManager()


def get_output_manager() -> OutputManager:
    """
    Get the global output manager instance.

    Returns:
        OutputManager: The global output manager
    """
    return output_manager


def create_output_directory(workflow_id: Optional[str] = None) -> Path:
    """
    Convenience function to create an output directory.

    Args:
        workflow_id: Optional workflow ID

    Returns:
        Path to the created directory
    """
    return output_manager.create_output_directory(workflow_id)


def generate_output_summary(output_dir: Path, workflow_name: str = "workflow") -> str:
    """
    Convenience function to generate output summary.

    Args:
        output_dir: Output directory
        workflow_name: Workflow name

    Returns:
        Formatted summary string
    """
    return output_manager.generate_output_summary(output_dir, workflow_name)
