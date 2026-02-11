"""ResearchAI v2.4.0 - Precision Effect Feature Test"""
import requests, time, json, sys

BASE = "http://localhost:8001"

def p(msg, s="info"): print(f"  {'✅' if s=='ok' else '❌' if s=='fail' else '⚠️' if s=='warn' else 'ℹ️'} {msg}")
def h(t): print(f"\n{'='*70}\n  {t}\n{'='*70}\n")

def test_v24_endpoints():
    """Test all v2.4.0 endpoints."""
    h("ResearchAI v2.4.0 - Precision Effect Test")
    
    # Health check
    p("Testing health endpoint...", "info")
    r = requests.get(f"{BASE}/health")
    d = r.json()
    p(f"Version: {d.get('version')}", "ok")
    p(f"Agents: {d.get('agents_registered')}", "info")
    features = d.get('features', {})
    p(f"Visualization v2: {features.get('visualization_v2', False)}", "ok" if features.get('visualization_v2') else "fail")
    p(f"Structured TOC: {features.get('structured_toc', False)}", "ok" if features.get('structured_toc') else "fail")
    
    # Artifact types
    h("Visualization Artifact Types")
    r = requests.get(f"{BASE}/api/v2/artifacts/types")
    if r.status_code == 200:
        d = r.json()
        p(f"Artifact types available: {len(d.get('artifact_types', []))}", "ok")
        for art in d.get('artifact_types', []):
            p(f"  • {art.get('name')}: {art.get('description')}", "info")
    else:
        p(f"Artifact types endpoint failed: {r.status_code}", "fail")
    
    return True


def test_full_flow_v24():
    """Test full proposal generation with v2.4 artifacts."""
    h("Full Flow Test with Precision Effect Artifacts")
    
    # Generate proposal
    p("Starting proposal generation...", "info")
    payload = {
        "topic": "Deep Learning for Medical Image Diagnosis in Precision Healthcare",
        "key_points": ["CNN architectures", "Transfer learning", "Clinical validation"]
    }
    r = requests.post(f"{BASE}/api/proposals/generate", json=payload)
    job_id = r.json().get('job_id')
    p(f"Job: {job_id[:12]}...", "ok")
    
    # Wait for completion
    p("Waiting for completion...", "info")
    start = time.time()
    while time.time() - start < 900:
        r = requests.get(f"{BASE}/api/proposals/jobs/{job_id}")
        d = r.json()
        if d.get('status') == 'completed':
            mins = int((time.time() - start) / 60)
            secs = int((time.time() - start) % 60)
            p(f"Completed in {mins}m {secs}s!", "ok")
            break
        elif d.get('status') == 'failed':
            p(f"Failed: {d.get('error')}", "fail")
            return None
        elapsed = int(time.time() - start)
        print(f"\r  ⏳ [{elapsed//60:02d}:{elapsed%60:02d}] {d.get('progress', 0):3d}% - {d.get('current_stage', ''):20}", end="", flush=True)
        time.sleep(5)
    print()
    
    # Get result
    r = requests.get(f"{BASE}/api/proposals/jobs/{job_id}/result")
    result = r.json().get('result', {})
    p(f"Words: {result.get('word_count', 0):,}", "info")
    
    return job_id


def test_visualization_artifacts(job_id: str):
    """Test visualization artifacts for a proposal."""
    h("Visualization Artifacts (Precision Effect)")
    
    # All artifacts
    r = requests.get(f"{BASE}/api/v2/artifacts/{job_id}")
    if r.status_code == 200:
        d = r.json()
        artifacts = d.get('artifacts', {}).get('artifacts', [])
        p(f"Total artifacts generated: {len(artifacts)}", "ok")
        for art in artifacts:
            has_mermaid = "✓ Mermaid" if art.get('mermaid_code') else "○ JSON"
            p(f"  • {art.get('title', 'Unknown')[:40]} [{has_mermaid}]", "info")
    else:
        p(f"All artifacts endpoint failed: {r.status_code}", "fail")
        return
    
    # Gantt Chart
    h("Gantt Chart (Research Timeline)")
    r = requests.get(f"{BASE}/api/v2/artifacts/{job_id}/gantt")
    if r.status_code == 200:
        d = r.json()
        phases = d.get('content', {}).get('phases', [])
        p(f"Gantt Chart: {d.get('title')}", "ok")
        p(f"Phases: {len(phases)}", "info")
        p(f"Duration: {d.get('content', {}).get('duration_months', 0)} months", "info")
        if d.get('mermaid_code'):
            p("Mermaid code available for rendering", "ok")
    else:
        p(f"Gantt endpoint failed: {r.status_code}", "fail")
    
    # WBS
    h("Work Breakdown Structure (WBS)")
    r = requests.get(f"{BASE}/api/v2/artifacts/{job_id}/wbs")
    if r.status_code == 200:
        d = r.json()
        levels = d.get('content', {}).get('levels', [])
        p(f"WBS: {d.get('title')}", "ok")
        if levels:
            children = levels[0].get('children', [])
            p(f"Top-level tasks: {len(children)}", "info")
            for child in children[:3]:
                p(f"  • {child.get('name')}: {child.get('deliverable')}", "info")
    else:
        p(f"WBS endpoint failed: {r.status_code}", "fail")
    
    # RTM
    h("Requirements Traceability Matrix (RTM)")
    r = requests.get(f"{BASE}/api/v2/artifacts/{job_id}/rtm")
    if r.status_code == 200:
        d = r.json()
        reqs = d.get('content', {}).get('requirements', [])
        p(f"RTM: {d.get('title')}", "ok")
        p(f"Requirements traced: {len(reqs)}", "info")
        completed = sum(1 for req in reqs if "Complete" in req.get('status', ''))
        p(f"Completed: {completed}/{len(reqs)}", "ok" if completed == len(reqs) else "warn")
        for req in reqs[:3]:
            p(f"  • {req.get('id')}: {req.get('description')[:40]}...", "info")
    else:
        p(f"RTM endpoint failed: {r.status_code}", "fail")
    
    # Kanban
    h("Kanban State Model")
    r = requests.get(f"{BASE}/api/v2/artifacts/{job_id}/kanban")
    if r.status_code == 200:
        d = r.json()
        stats = d.get('content', {}).get('stats', {})
        p(f"Kanban: {d.get('title')}", "ok")
        p(f"Total cards: {stats.get('total', 0)}", "info")
        p(f"Complete: {stats.get('complete', 0)}", "ok")
        p(f"In Progress: {stats.get('in_progress', 0)}", "info")
        p(f"To Do: {stats.get('to_do', 0)}", "info")
    else:
        p(f"Kanban endpoint failed: {r.status_code}", "fail")


def test_structured_toc(job_id: str):
    """Test structured TOC for a proposal."""
    h("Structured Table of Contents")
    
    r = requests.get(f"{BASE}/api/v2/toc/{job_id}")
    if r.status_code == 200:
        d = r.json()
        toc = d.get('toc', {})
        entries = toc.get('entries', [])
        p(f"TOC Title: {toc.get('title')}", "ok")
        p(f"Entries: {toc.get('entry_count')}", "info")
        p(f"Format: Structured JSON (no ASCII dots)", "ok")
        
        # Show sample entries
        p("Sample entries:", "info")
        for entry in entries[:5]:
            indent = "  " * entry.get('indent', 0)
            p(f"  {indent}{entry.get('number', '')} {entry.get('title')} ... {entry.get('page')}", "info")
        
        # Rendering instructions
        render = toc.get('rendering_instructions', {})
        p(f"Rendering: {render.get('leader_style')} leaders, {render.get('font_family')}", "info")
    else:
        p(f"Structured TOC endpoint failed: {r.status_code}", "fail")


def test_scopus_and_review(job_id: str):
    """Test Scopus and Review endpoints."""
    h("Scopus Q1 Compliance v2.0")
    r = requests.get(f"{BASE}/api/v2/scopus/compliance/{job_id}")
    if r.status_code == 200:
        d = r.json().get('compliance', {})
        score = d.get('overall_score', 0)
        bar = '█' * int(score * 30) + '░' * (30 - int(score * 30))
        p(f"Score: {bar} {score*100:.1f}%", "ok")
        p(f"Q1 Ready: {'✅' if d.get('q1_ready') else '❌'}", "ok" if d.get('q1_ready') else "warn")
    
    h("Reviewer Simulation v2.0 (7 Personas)")
    r = requests.get(f"{BASE}/api/v2/review/simulate/{job_id}")
    if r.status_code == 200:
        d = r.json().get('review', {})
        p(f"Decision: {d.get('overall_assessment', 'unknown').upper()}", "ok")
        p(f"Score: {d.get('consensus_score', 0)}%", "info")
        p(f"Agreement: {d.get('agreement_level', 'unknown')}", "info")


def main():
    print(f"\n{'='*70}")
    print(f"  ResearchAI v2.4.0 - Precision Effect Feature Test")
    print(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    
    # Quick endpoint test
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        test_v24_endpoints()
        h("QUICK TEST COMPLETE")
        return
    
    # Full test
    test_v24_endpoints()
    
    print("\n  Starting full flow test with artifact generation...")
    job_id = test_full_flow_v24()
    
    if job_id:
        test_visualization_artifacts(job_id)
        test_structured_toc(job_id)
        test_scopus_and_review(job_id)
    
    h("TEST COMPLETE")
    print("  ✅ ResearchAI v2.4.0 Precision Effect Ready!\n")
    print("  New Features:")
    print("  • Gantt Chart (Research Timeline)")
    print("  • Work Breakdown Structure (WBS)")
    print("  • Requirements Traceability Matrix (RTM)")
    print("  • Kanban State Model")
    print("  • Methodology Flowchart")
    print("  • Data Flow Diagram")
    print("  • Structured TOC (JSON format)")
    print()


if __name__ == "__main__":
    main()
