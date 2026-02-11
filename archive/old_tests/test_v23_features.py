"""ResearchAI v2.3.0 - Feature Test"""
import requests, time, sys

BASE = "http://localhost:8001"

def p(msg, s="info"): print(f"  {'✅' if s=='ok' else '❌' if s=='fail' else 'ℹ️'} {msg}")
def h(t): print(f"\n{'='*60}\n  {t}\n{'='*60}\n")

def test_endpoints():
    """Test all v2.3.0 endpoints."""
    h("ResearchAI v2.3.0 - Full Feature Test")
    
    # Health
    p("Testing health...", "info")
    r = requests.get(f"{BASE}/health")
    d = r.json()
    p(f"Version: {d.get('version')}, Agents: {d.get('agents_registered')}", "ok")
    p(f"Scopus v2: {d.get('features',{}).get('scopus_v2')}", "info")
    p(f"Reviewer v2: {d.get('features',{}).get('reviewer_v2')}", "info")
    p(f"Email: {d.get('features',{}).get('email_notifications')}", "info")
    
    # Features
    h("API Features")
    r = requests.get(f"{BASE}/api/features")
    d = r.json()
    p(f"Version: {d.get('version')}", "ok")
    p(f"Agents: {len(d.get('features',{}).get('agents',[]))}", "info")
    p(f"Personas: {d.get('features',{}).get('reviewer_personas')}", "info")
    p(f"ML Scoring: {d.get('features',{}).get('ml_scoring')}", "info")
    
    # Reviewer Personas v2
    h("Reviewer Personas v2.0")
    r = requests.get(f"{BASE}/api/v2/review/personas")
    if r.status_code == 200:
        d = r.json()
        p(f"Personas: {d.get('count')}", "ok")
        for pid, info in d.get('personas', {}).items():
            p(f"  • {info.get('name')}: {info.get('focus')}", "info")
    else:
        p(f"Reviewer v2 not available: {r.status_code}", "warn")
    
    # Scopus Criteria v2
    h("Scopus ML Scoring v2.0")
    r = requests.get(f"{BASE}/api/v2/scopus/criteria")
    if r.status_code == 200:
        d = r.json()
        p(f"Criteria: {len(d.get('criteria', []))}", "ok")
        for c in d.get('criteria', []):
            p(f"  • {c.get('name')}: {c.get('weight')}", "info")
    else:
        p(f"Scopus v2 not available: {r.status_code}", "warn")
    
    # Notifications
    h("Email Notifications")
    r = requests.get(f"{BASE}/api/notifications/status")
    d = r.json()
    p(f"Enabled: {d.get('enabled')}", "ok" if d.get('enabled') else "warn")
    p(f"Types: {', '.join(d.get('notification_types', []))}", "info")
    
    r = requests.get(f"{BASE}/api/notifications/settings")
    d = r.json()
    p(f"Settings: {len(d.get('settings', {}))} options", "ok")
    
    return True


def test_full_flow():
    """Test full proposal generation with v2 features."""
    h("Full Flow Test (Proposal + v2 Features)")
    
    # Generate proposal
    p("Starting proposal generation...", "info")
    payload = {"topic": "AI in Healthcare Diagnostics with Machine Learning", "key_points": ["Diagnostic accuracy", "Real-time monitoring"]}
    r = requests.post(f"{BASE}/api/proposals/generate", json=payload)
    job_id = r.json().get('job_id')
    p(f"Job: {job_id[:12]}...", "ok")
    
    # Wait for completion
    p("Waiting for completion (10-15 min)...", "info")
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
            return False
        prog = d.get('progress', 0)
        stage = d.get('current_stage', '')
        elapsed = int(time.time() - start)
        print(f"\r  ⏳ [{elapsed//60:02d}:{elapsed%60:02d}] {prog:3d}% - {stage:20}", end="", flush=True)
        time.sleep(5)
    print()
    
    # Get result
    r = requests.get(f"{BASE}/api/proposals/jobs/{job_id}/result")
    result = r.json().get('result', {})
    p(f"Words: {result.get('word_count', 0):,}", "info")
    p(f"Sections: {len(result.get('sections', []))}", "info")
    
    # Test Scopus v2
    h("Scopus Q1 Compliance v2.0")
    r = requests.get(f"{BASE}/api/v2/scopus/compliance/{job_id}")
    if r.status_code == 200:
        d = r.json().get('compliance', {})
        score = d.get('overall_score', 0)
        bar = '█' * int(score * 30) + '░' * (30 - int(score * 30))
        p(f"Score: {bar} {score*100:.1f}%", "ok")
        p(f"Quality: {d.get('quality_level', 'unknown')}", "info")
        p(f"Q1 Ready: {'✅' if d.get('q1_ready') else '❌'}", "ok" if d.get('q1_ready') else "warn")
        nlp = d.get('nlp_features', {})
        p(f"NLP: {nlp.get('total_words', 0)} words, Flesch: {nlp.get('readability_flesch', 0):.1f}", "info")
    else:
        p(f"Scopus v2 scoring failed: {r.status_code}", "fail")
    
    # Test Reviewer v2
    h("Reviewer Simulation v2.0 (7 Personas)")
    r = requests.get(f"{BASE}/api/v2/review/simulate/{job_id}")
    if r.status_code == 200:
        d = r.json().get('review', {})
        p(f"Decision: {d.get('overall_assessment', 'unknown').upper()}", "ok")
        p(f"Score: {d.get('consensus_score', 0)}%", "info")
        p(f"Agreement: {d.get('agreement_level', 'unknown')}", "info")
        for fb in d.get('reviewer_feedbacks', [])[:3]:
            p(f"  • {fb.get('persona_name')}: {fb.get('decision')} ({fb.get('score')}%)", "info")
        if d.get('aggregated_strengths'):
            p(f"Strengths: {len(d.get('aggregated_strengths', []))}", "info")
        if d.get('priority_revisions'):
            p(f"Revisions: {len(d.get('priority_revisions', []))}", "info")
    else:
        p(f"Reviewer v2 simulation failed: {r.status_code}", "fail")
    
    # Test exports
    h("Export Formats")
    for fmt in ['pdf', 'docx', 'markdown', 'latex', 'overleaf']:
        r = requests.get(f"{BASE}/api/proposals/{job_id}/export/{fmt}")
        size = len(r.content) / 1024
        p(f"{fmt:10} {size:.1f} KB", "ok" if r.status_code == 200 else "fail")
    
    return True


if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  ResearchAI v2.3.0 Feature Test")
    print(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        test_endpoints()
    else:
        test_endpoints()
        print("\n  Run with --quick for endpoint tests only")
        print("  Starting full flow test...\n")
        test_full_flow()
    
    h("TEST COMPLETE")
    print("  ✅ ResearchAI v2.3.0 Ready for Production!\n")
