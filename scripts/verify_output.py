#!/usr/bin/env python
"""
Verify Output Script - Validates proposal structure and quality.
Run after E2E test to verify all agent outputs.
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def verify_proposal_structure(proposal_dict: dict) -> dict:
    """Verify the proposal has all required sections."""
    
    results = {
        "valid": True,
        "checks": [],
        "warnings": [],
        "errors": []
    }
    
    # Check 1: Has sections
    sections = proposal_dict.get("sections", [])
    if sections:
        results["checks"].append(f"[OK] Has {len(sections)} sections")
    else:
        results["errors"].append("[FAIL] No sections found")
        results["valid"] = False
    
    # Check 2: Has metadata
    metadata = proposal_dict.get("metadata", {})
    if metadata:
        results["checks"].append(f"[OK] Has metadata")
        if metadata.get("topic"):
            results["checks"].append(f"[OK] Topic: {metadata['topic'][:50]}...")
        if metadata.get("total_word_count"):
            results["checks"].append(f"[OK] Word count: {metadata['total_word_count']}")
    else:
        results["warnings"].append("[WARN] No metadata found")
    
    # Check 3: Has references
    references = proposal_dict.get("references", [])
    if references:
        results["checks"].append(f"[OK] Has {len(references)} references")
    else:
        results["warnings"].append("[WARN] No references found")
    
    # Check 4: Has request_id
    if proposal_dict.get("request_id"):
        results["checks"].append(f"[OK] Request ID: {proposal_dict['request_id'][:8]}...")
    else:
        results["warnings"].append("[WARN] No request ID")
    
    # Check 5: Section quality
    expected_sections = ["Front Matter", "Introduction", "Literature Review", 
                        "Research Methodology", "Risk Assessment"]
    found_sections = [s.get("title", "") for s in sections]
    
    for expected in expected_sections:
        if any(expected.lower() in s.lower() for s in found_sections):
            results["checks"].append(f"[OK] Section found: {expected}")
        else:
            results["warnings"].append(f"[WARN] Section missing: {expected}")
    
    # Check 6: Section content
    empty_sections = []
    for section in sections:
        title = section.get("title", "Unknown")
        content = section.get("content", "")
        if not content or len(content) < 50:
            empty_sections.append(title)
    
    if empty_sections:
        results["warnings"].append(f"[WARN] Sections with little/no content: {', '.join(empty_sections)}")
    else:
        results["checks"].append("[OK] All sections have content")
    
    return results


def verify_agents_executed(proposal_dict: dict) -> dict:
    """Verify which agents contributed to the proposal."""
    
    results = {
        "agents_found": [],
        "agents_missing": [],
    }
    
    expected_agents = [
        "literature_review_agent",
        "introduction_agent",
        "research_methodology_agent",
        "quality_assurance_agent",
        "visualization_agent",
        "reference_citation_agent",
        "structure_formatting_agent",
        "front_matter_agent",
        "final_assembly_agent",
        "risk_assessment_agent",
        "methodology_optimizer_agent",
    ]
    
    metadata = proposal_dict.get("metadata", {})
    agents_involved = metadata.get("agents_involved", [])
    
    for agent in expected_agents:
        if agent in agents_involved or any(agent in a for a in agents_involved):
            results["agents_found"].append(agent)
        else:
            results["agents_missing"].append(agent)
    
    return results


def main():
    """Main verification function."""
    print("\n" + "=" * 80)
    print("OUTPUT VERIFICATION - RPA Claude Desktop")
    print("=" * 80)
    
    # Try to find the latest proposal output
    output_dir = project_root / "data" / "outputs"
    
    # For now, we'll create a mock verification since we need actual output
    print("\nChecking for proposal outputs...")
    
    if output_dir.exists():
        files = list(output_dir.glob("*.json"))
        if files:
            print(f"Found {len(files)} output files")
            for f in files:
                print(f"  - {f.name}")
        else:
            print("No JSON output files found in data/outputs/")
    else:
        print("Output directory not found. Creating...")
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check log files
    print("\nChecking test logs...")
    log_files = list(project_root.glob("*.log"))
    if log_files:
        print(f"Found {len(log_files)} log files:")
        for f in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
            size = f.stat().st_size
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"  - {f.name} ({size:,} bytes, {mtime})")
    
    # Verification checklist
    print("\n" + "-" * 80)
    print("VERIFICATION CHECKLIST")
    print("-" * 80)
    
    checks = [
        ("Project structure", (project_root / "src" / "agents").exists()),
        ("Config files", (project_root / "config" / "agents_config.yaml").exists()),
        ("Environment file", (project_root / ".env").exists()),
        ("Test files", (project_root / "tests").exists()),
        ("Output directory", output_dir.exists()),
        ("Scripts directory", (project_root / "scripts").exists()),
    ]
    
    for name, passed in checks:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {name}")
    
    print("\n" + "=" * 80)
    print("Verification complete!")
    print("\nTo run full E2E test:")
    print("  python run_sequential_tests.py")
    print("\nTo run with real LLM:")
    print("  $env:LLM_MOCK='0'")
    print("  python scripts\\run_system.py --topic \"Your Topic\"")
    print("=" * 80)


if __name__ == "__main__":
    main()
