#!/usr/bin/env python3
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
AKIOS Sample Data Copy Utility

Helps users copy sample data to their project directories for testing.
Run this script from your AKIOS project root directory.
"""

import os
import sys
import shutil
from pathlib import Path


def copy_samples(target_template=None):
    """
    Copy sample data for specified template or all templates.

    Args:
        target_template: Specific template name, or None for all
    """
    script_dir = Path(__file__).parent
    project_root = Path.cwd()

    # Verify we're in an AKIOS project
    if not (project_root / "config.yaml").exists():
        print("❌ Error: Not in an AKIOS project directory")
        print("   Run this script from your project root (where config.yaml is located)")
        return False

    # Ensure input directory exists
    input_dir = project_root / "data" / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    print("📋 AKIOS Sample Data Copy Utility")
    print(f"   Project: {project_root}")
    print(f"   Target: {input_dir}")
    print()

    # Template mappings
    template_samples = {
        "hello-workflow": ["hello-world/sample_input.txt"],
        "document_ingestion": ["document-analysis/sample_document.txt"],
        "batch_processing": ["batch-processing/sample_data.json"],
        "file_analysis": ["file-security/analysis_target.txt"]
    }

    copied_files = []

    if target_template:
        # Copy specific template samples
        if target_template not in template_samples:
            print(f"❌ Unknown template: {target_template}")
            print(f"   Available: {', '.join(template_samples.keys())}")
            return False

        samples = template_samples[target_template]
        print(f"📁 Copying samples for: {target_template}")

    else:
        # Copy all samples
        samples = []
        for template_samples_list in template_samples.values():
            samples.extend(template_samples_list)
        print("📁 Copying all template samples")

    # Copy each sample
    for sample_path in samples:
        source = script_dir / sample_path
        if not source.exists():
            print(f"⚠️  Sample not found: {sample_path}")
            continue

        # Determine destination filename
        dest_filename = Path(sample_path).name
        destination = input_dir / dest_filename

        # Copy file
        try:
            shutil.copy2(source, destination)
            copied_files.append(str(destination.relative_to(project_root)))
            print(f"✅ {sample_path} → {destination.relative_to(project_root)}")
        except Exception as e:
            print(f"❌ Failed to copy {sample_path}: {e}")

    print()
    if copied_files:
        print(f"🎉 Successfully copied {len(copied_files)} sample files!")
        print("   Files ready for testing in data/input/:")
        for file in copied_files:
            print(f"   • {file}")
        print()
        print("💡 Next steps:")
        print("   1. Update your workflow.yml to use these sample files")
        print("   2. Run: akios run workflow.yml")
        print("   3. Check results in data/output/")
    else:
        print("❌ No files were copied")

    return len(copied_files) > 0


def main():
    """Main entry point"""
    if len(sys.argv) > 2:
        print("Usage: python copy_samples.py [template-name]")
        print("   template-name: hello-workflow, document_ingestion, batch_processing, or file_analysis")
        print("   (omit for all templates)")
        sys.exit(1)

    target_template = sys.argv[1] if len(sys.argv) == 2 else None

    success = copy_samples(target_template)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
