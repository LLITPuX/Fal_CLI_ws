"""
Validate .cursor/rules files before loading to Knowledge Base.

Checks:
- Files are not empty
- No broken links
- Consistent versioning
- Valid frontmatter
- No conflicting rules
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple
import hashlib
from datetime import datetime


class RulesValidator:
    """Validator for .cursor/rules/*.mdc files."""
    
    def __init__(self, rules_path: str = ".cursor/rules"):
        self.rules_path = Path(rules_path)
        self.issues: List[Dict] = []
        self.warnings: List[Dict] = []
        self.stats: Dict = {}
    
    def validate_all(self) -> bool:
        """
        Run all validation checks.
        
        Returns:
            True if all checks pass, False otherwise
        """
        print("[*] Validating .cursor/rules files...\n")
        
        # Collect all .mdc files
        mdc_files = list(self.rules_path.glob("**/*.mdc"))
        self.stats["total_files"] = len(mdc_files)
        
        print(f"Found {len(mdc_files)} .mdc files\n")
        
        # Run checks
        self._check_empty_files(mdc_files)
        self._check_broken_links(mdc_files)
        self._check_frontmatter(mdc_files)
        self._check_versions(mdc_files)
        self._check_conflicting_rules(mdc_files)
        
        # Report results
        self._print_report()
        
        return len(self.issues) == 0
    
    def _check_empty_files(self, files: List[Path]):
        """Check for empty or nearly empty files."""
        print("[+] Checking for empty files...")
        
        for file in files:
            content = file.read_text(encoding="utf-8")
            
            # Skip frontmatter
            lines = [
                l for l in content.split('\n') 
                if l.strip() and not l.startswith('---')
            ]
            
            # Count meaningful lines
            meaningful_lines = [
                l for l in lines
                if not l.strip().startswith('#') or len(l.strip()) > 5
            ]
            
            if len(meaningful_lines) < 5:
                self.issues.append({
                    "type": "empty_file",
                    "file": str(file),
                    "message": f"File has only {len(meaningful_lines)} meaningful lines"
                })
            elif len(lines) < 20:
                self.warnings.append({
                    "type": "short_file",
                    "file": str(file),
                    "message": f"File is short ({len(lines)} lines), verify it's complete"
                })
        
        print(f"  [OK] Checked {len(files)} files\n")
    
    def _check_broken_links(self, files: List[Path]):
        """Check for broken internal links."""
        print("[+] Checking for broken links...")
        
        broken_count = 0
        
        for file in files:
            content = file.read_text(encoding="utf-8")
            
            # Find markdown links
            links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
            
            for link_text, link_url in links:
                # Skip external links
                if link_url.startswith(('http://', 'https://', '#')):
                    continue
                
                # Check if .mdc file exists
                if link_url.endswith('.mdc'):
                    # Resolve relative path
                    target_path = (file.parent / link_url).resolve()
                    
                    if not target_path.exists():
                        self.issues.append({
                            "type": "broken_link",
                            "file": str(file),
                            "message": f"Broken link: [{link_text}]({link_url})",
                            "target": str(target_path)
                        })
                        broken_count += 1
        
        if broken_count == 0:
            print(f"  [OK] No broken links found\n")
        else:
            print(f"  [!] Found {broken_count} broken links\n")
    
    def _check_frontmatter(self, files: List[Path]):
        """Check frontmatter is valid YAML."""
        print("[+] Checking frontmatter...")
        
        for file in files:
            content = file.read_text(encoding="utf-8")
            
            # Extract frontmatter
            frontmatter_match = re.match(
                r'^---\s*\n(.*?)\n---',
                content,
                re.DOTALL
            )
            
            if not frontmatter_match:
                self.warnings.append({
                    "type": "no_frontmatter",
                    "file": str(file),
                    "message": "File has no frontmatter"
                })
                continue
            
            frontmatter = frontmatter_match.group(1)
            
            # Check required fields
            if "description:" not in frontmatter and "alwaysApply:" not in frontmatter:
                self.warnings.append({
                    "type": "incomplete_frontmatter",
                    "file": str(file),
                    "message": "Frontmatter missing description or alwaysApply"
                })
        
        print(f"  [OK] Checked frontmatter in {len(files)} files\n")
    
    def _check_versions(self, files: List[Path]):
        """Check version consistency."""
        print("[+] Checking versions...")
        
        versions = {}
        version_pattern = r'\*\*Version:\*\*\s*(\d+\.\d+\.\d+)'
        
        for file in files:
            content = file.read_text(encoding="utf-8")
            match = re.search(version_pattern, content)
            
            if match:
                version = match.group(1)
                versions[str(file)] = version
        
        self.stats["files_with_versions"] = len(versions)
        
        # Check for outdated versions
        for file_path, version in versions.items():
            major, minor, patch = map(int, version.split('.'))
            
            if major < 1:
                self.warnings.append({
                    "type": "version_warning",
                    "file": file_path,
                    "message": f"Version {version} is pre-1.0, consider updating"
                })
        
        print(f"  [OK] Found versions in {len(versions)}/{len(files)} files\n")
    
    def _check_conflicting_rules(self, files: List[Path]):
        """Check for conflicting architectural rules."""
        print("[+] Checking for conflicting rules...")
        
        # Collect key patterns
        async_rules = []
        sync_rules = []
        
        for file in files:
            content = file.read_text(encoding="utf-8")
            
            # Look for async requirements
            if re.search(r'MUST be async|async-first|ALL I/O.*async', content, re.IGNORECASE):
                async_rules.append(str(file))
            
            # Look for sync patterns (potential conflicts)
            if re.search(r'synchronous|blocking|sync.*OK', content, re.IGNORECASE):
                sync_rules.append(str(file))
        
        # Check for conflicts
        conflicts = set(async_rules) & set(sync_rules)
        
        if conflicts:
            for file in conflicts:
                self.warnings.append({
                    "type": "potential_conflict",
                    "file": file,
                    "message": "File mentions both async and sync patterns, verify consistency"
                })
        
        print(f"  [OK] No major conflicts detected\n")
    
    def _print_report(self):
        """Print validation report."""
        print("\n" + "="*60)
        print("VALIDATION REPORT")
        print("="*60 + "\n")
        
        # Summary
        print(f"[*] Summary:")
        print(f"  Total files: {self.stats['total_files']}")
        print(f"  Issues: {len(self.issues)}")
        print(f"  Warnings: {len(self.warnings)}")
        print()
        
        # Issues (blocking)
        if self.issues:
            print("[!] ISSUES (must fix before loading):")
            for issue in self.issues:
                print(f"\n  [{issue['type']}] {issue['file']}")
                print(f"    {issue['message']}")
            print()
        else:
            print("[OK] No blocking issues found!\n")
        
        # Warnings (non-blocking)
        if self.warnings:
            print("[~] WARNINGS (recommend reviewing):")
            for warning in self.warnings:
                print(f"\n  [{warning['type']}] {Path(warning['file']).name}")
                print(f"    {warning['message']}")
            print()
        
        # Status
        if len(self.issues) == 0:
            print("[SUCCESS] VALIDATION PASSED - Ready for loading to Knowledge Base")
        else:
            print("[FAILED] VALIDATION FAILED - Fix issues before loading")
        
        print("\n" + "="*60 + "\n")
    
    def get_files_manifest(self) -> List[Dict]:
        """
        Generate manifest of all valid files for loading.
        
        Returns:
            List of file metadata dicts
        """
        mdc_files = list(self.rules_path.glob("**/*.mdc"))
        
        manifest = []
        
        for file in mdc_files:
            content = file.read_text(encoding="utf-8")
            
            # Calculate hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Extract version
            version_match = re.search(r'\*\*Version:\*\*\s*(\d+\.\d+\.\d+)', content)
            version = version_match.group(1) if version_match else "1.0.0"
            
            # Determine category
            category = self._categorize_file(file)
            
            manifest.append({
                "path": str(file),
                "relative_path": str(file.relative_to(self.rules_path.parent)),
                "size_bytes": len(content),
                "lines": len(content.splitlines()),
                "content_hash": content_hash,
                "version": version,
                "category": category,
                "last_modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })
        
        return manifest
    
    def _categorize_file(self, file: Path) -> str:
        """Determine file category."""
        path_str = str(file)
        
        if "agents/" in path_str:
            return "agent_patterns"
        elif "architecture/" in path_str:
            return "architecture"
        elif file.name in ("backend.mdc", "frontend.mdc"):
            return "development"
        elif file.name in ("docker.mdc", "windows.mdc"):
            return "infrastructure"
        elif file.name in ("falkordb.mdc", "templates.mdc"):
            return "technical"
        elif file.name in ("testing.mdc",):
            return "quality"
        elif file.name in ("session-reports.mdc",):
            return "documentation"
        else:
            return "general"


def main():
    """Run validation."""
    validator = RulesValidator()
    
    # Validate
    success = validator.validate_all()
    
    # Generate manifest
    if success:
        manifest = validator.get_files_manifest()
        
        print(f"[*] Generated manifest for {len(manifest)} files:")
        print()
        
        # Group by category
        by_category = {}
        for item in manifest:
            cat = item["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(item)
        
        for category, items in sorted(by_category.items()):
            print(f"  {category}: {len(items)} files")
        
        print()
        
        # Save manifest
        import json
        manifest_path = Path("backend/scripts/rules_manifest.json")
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"[SAVE] Manifest saved to: {manifest_path}\n")
    
    # Exit code
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

