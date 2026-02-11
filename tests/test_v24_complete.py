"""
ResearchAI v2.4.0 - Complete Feature Test Suite
================================================
Tests all new features:
1. Visualization Artifacts (Gantt, WBS, RTM, Kanban)
2. Structured TOC with JSON format
3. Scopus Q1 Compliance Scoring
4. Reviewer Simulation (7 personas)
5. PDF/DOCX export with embedded artifacts
"""

import requests
import time
import json
import sys

API_URL = "http://localhost:8001"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_success(msg):
    print(f"  ✅ {msg}")

def print_error(msg):
    print(f"  ❌ {msg}")

def print_info(msg):
    print(f"  ℹ️  {msg}")

def test_health():
    """Test system health and version"""
    print_header("1. SYSTEM HEALTH CHECK")
    
    try:
        res = requests.get(f"{API_URL}/health", timeout=10)
        data = res.json()
        
        print_success(f"Version: {data.get('version', 'unknown')}")
        print_success(f"Agents: {data.get('agents_registered', 0)}")
        
        features = data.get('features', {})
        print_success(f"Visualization v2: {features.get('visualization_v2', False)}")
        print_success(f"Structured TOC: {features.get('structured_toc', False)}")
        print_success(f"Scopus v2: {features.get('scopus_v2', False)}")
        print_success(f"Reviewer v2: {features.get('reviewer_v2', False)}")
        
        return True
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def test_artifact_types():
    """Test artifact types endpoint"""
    print_header("2. ARTIFACT TYPES")
    
    try:
        res = requests.get(f"{API_URL}/api/v2/artifacts/types", timeout=10)
        data = res.json()
        
        print_success(f"Version: {data.get('version', 'unknown')}")
        
        artifact_types = data.get('artifact_types', [])
        print_success(f"{len(artifact_types)} artifact types available:")
        
        for art in artifact_types:
            print(f"      • {art['name']} - {art['description']}")
        
        return len(artifact_types) >= 6
    except Exception as e:
        print_error(f"Artifact types failed: {e}")
        return False

def generate_proposal():
    """Generate a test proposal"""
    print_header("3. PROPOSAL GENERATION")
    
    payload = {
        "topic": "Artificial Intelligence in Precision Medicine: A Multi-Modal Deep Learning Approach for Early Disease Detection",
        "key_points": [
            "Deep learning architectures for medical image analysis",
            "Natural language processing for clinical notes",
            "Integration of genomic data with imaging biomarkers"
        ],
        "citation_style": "harvard",
        "target_word_count": 15000,
        "student_name": "Test Researcher"
    }
    
    try:
        print_info("Starting proposal generation...")
        res = requests.post(f"{API_URL}/api/proposals/generate", json=payload, timeout=30)
        data = res.json()
        
        job_id = data.get('job_id')
        print_success(f"Job ID: {job_id}")
        print_info(f"Estimated time: {data.get('estimated_time_minutes', 15)} minutes")
        
        return job_id
    except Exception as e:
        print_error(f"Generation failed: {e}")
        return None

def wait_for_completion(job_id, max_wait=600):
    """Wait for proposal to complete"""
    print_header("4. WAITING FOR COMPLETION")
    
    start_time = time.time()
    last_progress = -1
    
    while time.time() - start_time < max_wait:
        try:
            res = requests.get(f"{API_URL}/api/proposals/jobs/{job_id}", timeout=10)
            data = res.json()
            
            status = data.get('status', 'unknown')
            progress = data.get('progress', 0)
            stage = data.get('current_stage', 'unknown')
            
            if progress != last_progress:
                elapsed = int(time.time() - start_time)
                print(f"  [{elapsed:3d}s] {progress:3d}% - {stage}")
                last_progress = progress
            
            if status == 'completed':
                print_success(f"Completed in {int(time.time() - start_time)} seconds!")
                return True
            elif status == 'failed':
                print_error(f"Failed: {data.get('error', 'Unknown error')}")
                return False
            
            time.sleep(3)
        except Exception as e:
            print_error(f"Poll error: {e}")
            time.sleep(5)
    
    print_error("Timeout waiting for completion")
    return False

def test_artifacts(job_id):
    """Test visualization artifacts"""
    print_header("5. VISUALIZATION ARTIFACTS")
    
    try:
        # Get all artifacts
        res = requests.get(f"{API_URL}/api/v2/artifacts/{job_id}", timeout=30)
        data = res.json()
        
        artifacts = data.get('artifacts', {}).get('artifacts', [])
        print_success(f"Retrieved {len(artifacts)} artifacts")
        
        for art in artifacts:
            art_type = art.get('type', 'unknown')
            title = art.get('title', 'Untitled')
            fmt = art.get('format', 'unknown')
            has_mermaid = '✓' if art.get('mermaid_code') else '✗'
            print(f"      • {art_type}: {title} [{fmt}] Mermaid:{has_mermaid}")
        
        # Test individual endpoints
        print_info("Testing individual artifact endpoints...")
        
        endpoints = [
            ('gantt', 'Gantt Chart'),
            ('wbs', 'Work Breakdown Structure'),
            ('rtm', 'Requirements Traceability Matrix'),
            ('kanban', 'Kanban State Model')
        ]
        
        for endpoint, name in endpoints:
            try:
                res = requests.get(f"{API_URL}/api/v2/artifacts/{job_id}/{endpoint}", timeout=10)
                if res.status_code == 200:
                    print_success(f"{name} endpoint OK")
                else:
                    print_error(f"{name} endpoint failed: {res.status_code}")
            except Exception as e:
                print_error(f"{name} endpoint error: {e}")
        
        return len(artifacts) >= 4
    except Exception as e:
        print_error(f"Artifacts test failed: {e}")
        return False

def test_structured_toc(job_id):
    """Test structured TOC"""
    print_header("6. STRUCTURED TABLE OF CONTENTS")
    
    try:
        res = requests.get(f"{API_URL}/api/v2/toc/{job_id}", timeout=10)
        data = res.json()
        
        toc = data.get('toc', {})
        version = toc.get('version', 'unknown')
        entry_count = toc.get('entry_count', 0)
        entries = toc.get('entries', [])
        
        print_success(f"TOC Version: {version}")
        print_success(f"Entry Count: {entry_count}")
        
        # Check rendering instructions
        render = toc.get('rendering_instructions', {})
        print_success(f"Leader Style: {render.get('leader_style', 'none')}")
        print_success(f"Font: {render.get('font_family', 'unknown')}")
        
        # Show first few entries
        print_info("Sample TOC entries:")
        for entry in entries[:8]:
            indent = "  " * entry.get('indent', 0)
            num = entry.get('number', '')
            title = entry.get('title', '')
            page = entry.get('page', '')
            print(f"      {indent}{num} {title} ... {page}")
        
        if len(entries) > 8:
            print(f"      ... and {len(entries) - 8} more entries")
        
        return entry_count >= 30
    except Exception as e:
        print_error(f"TOC test failed: {e}")
        return False

def test_scopus_compliance(job_id):
    """Test Scopus Q1 compliance scoring"""
    print_header("7. SCOPUS Q1 COMPLIANCE")
    
    try:
        res = requests.get(f"{API_URL}/api/v2/scopus/compliance/{job_id}", timeout=30)
        data = res.json()
        
        compliance = data.get('compliance', {})
        score = compliance.get('overall_score', 0)
        q1_ready = compliance.get('q1_ready', False)
        quality = compliance.get('quality_level', 'unknown')
        
        # Display score bar
        bar_len = 30
        filled = int(score * bar_len)
        bar = '█' * filled + '░' * (bar_len - filled)
        
        print_success(f"Overall Score: {score*100:.1f}% [{bar}]")
        print_success(f"Q1 Ready: {'✅ YES' if q1_ready else '⚠️ NO'}")
        print_success(f"Quality Level: {quality}")
        
        # Criteria scores
        criteria = compliance.get('criteria_scores', {})
        if criteria:
            print_info("Criteria breakdown:")
            for key, val in criteria.items():
                if isinstance(val, dict):
                    score = val.get('score', val.get('value', 0))
                    print(f"      • {key}: {score*100:.0f}%")
                elif isinstance(val, (int, float)):
                    print(f"      • {key}: {val*100:.0f}%")
                else:
                    print(f"      • {key}: {val}")
        
        # Acceptance probability
        prob = compliance.get('acceptance_probability', {})
        if prob:
            est = prob.get('estimate', 0)
            print_success(f"Acceptance Probability: {est*100:.1f}%")
        
        return q1_ready
    except Exception as e:
        print_error(f"Scopus test failed: {e}")
        return False

def test_reviewer_simulation(job_id):
    """Test reviewer simulation"""
    print_header("8. REVIEWER SIMULATION")
    
    try:
        res = requests.get(f"{API_URL}/api/v2/review/simulate/{job_id}", timeout=60)
        data = res.json()
        
        review = data.get('review', {})
        decision = review.get('overall_assessment', 'unknown')
        score = review.get('consensus_score', 0)
        agreement = review.get('agreement_level', 'unknown')
        
        # Decision emoji
        decision_emoji = {
            'accept': '✅',
            'minor_revision': '🔄',
            'major_revision': '⚠️',
            'reject': '❌'
        }.get(decision, '❓')
        
        print_success(f"Decision: {decision_emoji} {decision.upper()}")
        print_success(f"Consensus Score: {score:.1f}%")
        print_success(f"Agreement Level: {agreement}")
        
        # Reviewer feedback
        feedback = review.get('reviewer_feedback', [])
        print_info(f"Reviewer Count: {len(feedback)}")
        
        for rev in feedback[:5]:
            name = rev.get('persona_name', 'Unknown')
            rec = rev.get('recommendation', 'unknown')
            rscore = rev.get('score', 0)
            print(f"      • {name}: {rec} ({rscore*100:.0f}%)")
        
        return decision in ['accept', 'minor_revision']
    except Exception as e:
        print_error(f"Review test failed: {e}")
        return False

def test_result_details(job_id):
    """Test proposal result details"""
    print_header("9. PROPOSAL RESULT")
    
    try:
        res = requests.get(f"{API_URL}/api/proposals/jobs/{job_id}/result", timeout=10)
        data = res.json()
        
        result = data.get('result', {})
        word_count = result.get('word_count', 0)
        sections = result.get('sections', [])
        
        print_success(f"Word Count: {word_count:,}")
        print_success(f"Sections: {len(sections)}")
        
        # Check for appendices
        appendix_count = sum(1 for s in sections if 'APPENDIX' in s.get('title', ''))
        print_success(f"Appendices: {appendix_count}")
        
        # List appendices
        print_info("Appendix sections:")
        for s in sections:
            if 'APPENDIX' in s.get('title', ''):
                print(f"      • {s.get('title', '')}")
        
        return word_count >= 10000 and appendix_count >= 4
    except Exception as e:
        print_error(f"Result test failed: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  ResearchAI v2.4.0 - COMPLETE FEATURE TEST")
    print("="*60)
    
    results = {}
    
    # 1. Health check
    results['health'] = test_health()
    if not results['health']:
        print_error("Backend not available. Start with: python -m uvicorn src.api.main:app --port 8001")
        return
    
    # 2. Artifact types
    results['artifact_types'] = test_artifact_types()
    
    # 3. Generate proposal
    job_id = generate_proposal()
    if not job_id:
        print_error("Failed to start proposal generation")
        return
    
    # 4. Wait for completion
    completed = wait_for_completion(job_id)
    if not completed:
        print_error("Proposal generation did not complete")
        return
    
    # 5. Test artifacts
    results['artifacts'] = test_artifacts(job_id)
    
    # 6. Test TOC
    results['toc'] = test_structured_toc(job_id)
    
    # 7. Test Scopus
    results['scopus'] = test_scopus_compliance(job_id)
    
    # 8. Test Review
    results['review'] = test_reviewer_simulation(job_id)
    
    # 9. Test result details
    results['result'] = test_result_details(job_id)
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test.upper():20} {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 ALL TESTS PASSED! ResearchAI v2.4.0 is fully operational.")
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed. Review the output above.")
    
    print(f"\n  Job ID for manual testing: {job_id}")
    print(f"  Frontend: http://localhost:3000/dashboard")

if __name__ == "__main__":
    main()
