# Release vs Fix Decision Guide

## When to Do a Full Release vs Quick Fix

### 🚀 **Full Release Required** (Use v2 release scripts)

**When you change:**
- ✅ Source code (Python modules, CLI commands, core functionality)
- ✅ Dependencies (requirements.txt, pyproject.toml changes)
- ✅ Package metadata (version, description, entry points)
- ✅ Security features or configurations
- ✅ New features or breaking changes
- ✅ Bug fixes that affect functionality

**Process:**
1. Update version in `pyproject.toml` and `src/akios/_version.py`
2. Run full v2 release process: `./.github/scripts/release/v2/release.sh --version X.Y.Z`
3. Creates PyPI package + GitHub release + tags

---

### 🔧 **Quick Fix Allowed** (Direct repo updates)

**When you change:**
- ✅ Documentation (README.md, docs/, quickstart.md)
- ✅ Templates (workflow templates, examples)
- ✅ Build scripts (CI/CD, GitHub Actions)
- ✅ Internal scripts (not affecting package contents)
- ✅ Comments, formatting, non-functional changes

**Process:**
1. Update files in private repo
2. Commit changes
3. Sync to public repo manually (no version bump needed)
4. Push directly to public repo main branch

---

### 📦 **Package Management Scenarios**

#### Yank a Release (Mark as deprecated)
```bash
# On PyPI web interface:
# Go to akios → Releases → [version] → "Yank release"
# Or use API: curl -X POST https://pypi.org/manage/project/akios/release/X.Y.Z/yank/
```
**When to yank:**
- ❌ Missing critical files (legal docs, source code)
- ❌ Security vulnerabilities
- ❌ Broken functionality
- ❌ Legal issues

**Yanking effects:**
- Won't install by default (`pip install akios` skips yanked versions)
- Still installable if explicitly requested (`pip install akios==X.Y.Z`)
- Preserves version history
- Better than deletion

#### Delete a Release (Nuclear option)
```bash
# On PyPI web interface:
# Go to akios → Releases → [version] → "Delete release"
# Requires confirmation of all warnings
```
**When to delete:** Only for legal issues or severe security problems
**Effects:** Completely removes from PyPI, breaks existing installs

#### Emergency Hotfix Release
1. Fix the issue in private repo
2. Bump patch version (X.Y.Z → X.Y.Z+1)
3. Run full release process immediately
4. Yank the broken version

---

### 🔄 **Dual Repo Sync Scenarios**

#### Documentation Update (Current case)
```bash
# Private repo
cd akios-dev/
edit docs/quickstart.md
git commit -am "Update installation docs"

# Public repo
cd akios-public/
git pull
cp -r ../akios-dev/docs/ .
git add docs/
git commit -m "Sync documentation updates"
git push origin main
```

#### Code + Docs Update
```bash
# Use full release process - includes docs automatically
./.github/scripts/release/v2/release.sh --version 1.0.3
```

#### Template-Only Update
```bash
# Can do quick sync since templates don't affect package
cd akios-public/
git pull
cp -r ../akios-dev/templates/ .
git add templates/
git commit -m "Update workflow templates"
git push origin main
```

---

### ⚠️ **Decision Checklist**

**Do I need a full release?**
- [ ] Does this change Python code that ships in the package?
- [ ] Does this change dependencies or package metadata?
- [ ] Does this affect functionality for end users?
- [ ] Is this a security fix or critical bug fix?

**If YES to any:** Use full release process
**If NO to all:** Quick fix is acceptable

**Remember:** When in doubt, do a full release. It's safer than breaking existing installations.
