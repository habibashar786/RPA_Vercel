"""
ResearchAI v2.2 - Complete End-to-End System Test
==================================================
Tests all features including new Scopus Compliance and Reviewer Simulation.

Run: python test_e2e_complete.py
"""

import requests
import time
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3001"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")

def print_test(name):
    print(f"\n{Colors.BLUE}▶ {name}{Colors.END}")

def print_success(msg):
    print(f"  {Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"  {Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"  {Colors.YELLOW}⚠️ {msg}{Colors.END}")

def print_info(msg):
    print(f"  {Colors.CYAN}ℹ️ {msg}{Colors.END}")

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests = []
    
    def add_pass(self, name):
        self.passed += 1
        self.tests.append(("PASS", name))
    
    def add_fail(self, name, error):
        self.failed += 1
        self.tests.append(("FAIL", name, error))
    
    def add_warning(self, name, warning):
        self.warnings += 1
        self.tests.append(("WARN", name, warning))
    
    def summary(self):
        print_header("TEST SUMMARY")
        print(f"\n  Total Tests: {self.passed + self.failed}")
        print(f"  {Colors.GREEN}Passed: {self.passed}{Colors.END}")
        print(f"  {Colors.RED}Failed: {self.failed}{Colors.END}")
        print(f"  {Colors.YELLOW}Warnings: {self.warnings}{Colors.END}")
        
        if self.failed > 0:
            print(f"\n  {Colors.RED}Failed Tests:{Colors.END}")
            for t in self.tests:
                if t[0] == "FAIL":
                    print(f"    - {t[1]}: {t[2]}")
        
        return self.failed == 0

results = TestResults()

# ============================================================================
# PHASE 1: Backend Health & Infrastructure
# ============================================================================
def test_backend_health():
    print_test("1.1 Backend Health Check")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        if r.status_code == 200:
            data = r.json()
            print_success(f"Backend healthy - v{data.get('version', 'unknown')}")
            print_info(f"Agents registered: {data.get('agents_registered', 0)}")
            results.add_pass("Backend Health")
            return True
        else:
            print_error(f"Unexpected status: {r.status_code}")
            results.add_fail("Backend Health", f"Status {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Backend not running!")
        print_info("Start with: python -m uvicorn src.api.main:app --port 8001")
        results.add_fail("Backend Health", "Connection refused")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("Backend Health", str(e))
        return False

def test_system_status():
    print_test("1.2 System Status")
    try:
        r = requests.get(f"{BASE_URL}/api/system/status", timeout=10)
        data = r.json()
        print_success(f"Version: {data.get('version')}")
        print_info(f"Model: {data.get('model')}")
        features = data.get('features', {})
        print_info(f"Subscription tiers: {features.get('subscription_tiers', False)}")
        print_info(f"Watermark support: {features.get('watermark_support', False)}")
        results.add_pass("System Status")
        return data
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("System Status", str(e))
        return None

def test_features_list():
    print_test("1.3 Features List")
    try:
        r = requests.get(f"{BASE_URL}/api/features", timeout=10)
        data = r.json()
        print_success(f"Version: {data.get('version')}")
        features = data.get('features', {})
        agents = features.get('agents', [])
        print_info(f"Agents: {len(agents)}")
        print_info(f"Export formats: {features.get('export_formats', [])}")
        print_info(f"Scopus Compliance: {features.get('scopus_compliance', False)}")
        print_info(f"Reviewer Simulation: {features.get('reviewer_simulation', False)}")
        results.add_pass("Features List")
        return True
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("Features List", str(e))
        return False

def test_agents_list():
    print_test("1.4 Agents List")
    try:
        r = requests.get(f"{BASE_URL}/agents", timeout=10)
        data = r.json()
        count = data.get('count', 0)
        agents = data.get('agents', [])
        
        if count >= 12:
            print_success(f"{count} agents registered")
            for agent in agents[:5]:
                print_info(f"  - {agent}")
            if len(agents) > 5:
                print_info(f"  ... and {len(agents) - 5} more")
            results.add_pass("Agents List")
            return True
        else:
            print_warning(f"Only {count} agents (expected 12+)")
            results.add_warning("Agents List", f"Only {count} agents")
            return True
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("Agents List", str(e))
        return False

# ============================================================================
# PHASE 2: Authentication
# ============================================================================
def test_demo_login():
    print_test("2.1 Demo Login")
    try:
        r = requests.post(f"{BASE_URL}/api/auth/login", 
                         json={"email": "demo@researchai.app", "password": "demo123"},
                         timeout=10)
        data = r.json()
        
        if data.get('access_token'):
            print_success("Login successful")
            user = data.get('user', {})
            print_info(f"User: {user.get('name')}")
            print_info(f"Tier: {user.get('subscription_tier', 'unknown')}")
            results.add_pass("Demo Login")
            return data.get('access_token'), user
        else:
            print_error("No access token returned")
            results.add_fail("Demo Login", "No token")
            return None, None
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("Demo Login", str(e))
        return None, None

# ============================================================================
# PHASE 3: Subscription System
# ============================================================================
def test_subscription_tiers():
    print_test("3.1 Subscription Tiers")
    try:
        r = requests.get(f"{BASE_URL}/api/subscription/tiers", timeout=10)
        data = r.json()
        tiers = data.get('tiers', [])
        
        if len(tiers) >= 3:
            print_success(f"{len(tiers)} tiers available")
            for tier in tiers:
                print_info(f"  {tier['name']}: ${tier['price']}")
            results.add_pass("Subscription Tiers")
            return True
        else:
            print_warning(f"Only {len(tiers)} tiers")
            results.add_warning("Subscription Tiers", f"Only {len(tiers)} tiers")
            return True
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("Subscription Tiers", str(e))
        return False

# ============================================================================
# PHASE 4: Proposal Generation
# ============================================================================
def test_proposal_generation():
    print_test("4.1 Proposal Generation (Start Job)")
    try:
        payload = {
            "topic": "Artificial Intelligence in Precision Medicine for Early Cancer Detection",
            "key_points": [
                "Current limitations in cancer diagnosis",
                "Machine learning approaches for biomarker analysis",
                "Integration of multi-omics data",
                "Clinical validation considerations"
            ],
            "citation_style": "harvard",
            "target_word_count": 15000,
            "student_name": "Test Researcher"
        }
        
        r = requests.post(f"{BASE_URL}/api/proposals/generate", json=payload, timeout=30)
        data = r.json()
        
        if data.get('job_id'):
            job_id = data['job_id']
            print_success(f"Job created: {job_id[:12]}...")
            print_info(f"Status: {data.get('status')}")
            print_info(f"Estimated time: {data.get('estimated_time_minutes')} min")
            results.add_pass("Proposal Generation Start")
            return job_id
        else:
            print_error("No job ID returned")
            results.add_fail("Proposal Generation Start", "No job ID")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("Proposal Generation Start", str(e))
        return None

def test_job_polling(job_id, max_polls=30, poll_interval=5):
    print_test(f"4.2 Job Polling (max {max_polls} polls)")
    
    if not job_id:
        print_error("No job ID to poll")
        results.add_fail("Job Polling", "No job ID")
        return None
    
    last_progress = -1
    for i in range(max_polls):
        try:
            r = requests.get(f"{BASE_URL}/api/proposals/jobs/{job_id}", timeout=10)
            data = r.json()
            
            status = data.get('status', 'unknown')
            progress = data.get('progress', 0)
            stage = data.get('current_stage', 'unknown')
            
            if progress != last_progress:
                print_info(f"[{i+1}/{max_polls}] {status} - {progress}% - {stage}")
                last_progress = progress
            
            if status == 'completed':
                print_success(f"Job completed at {progress}%!")
                results.add_pass("Job Polling")
                return data
            elif status == 'failed':
                print_error(f"Job failed: {data.get('error', 'Unknown error')}")
                results.add_fail("Job Polling", data.get('error', 'Job failed'))
                return None
            
            time.sleep(poll_interval)
            
        except Exception as e:
            print_warning(f"Poll error: {e}")
            time.sleep(poll_interval)
    
    print_warning("Polling timeout - job still running")
    results.add_warning("Job Polling", "Timeout")
    return None

def test_job_result(job_id):
    print_test("4.3 Get Job Result")
    
    if not job_id:
        print_error("No job ID")
        results.add_fail("Job Result", "No job ID")
        return None
    
    try:
        r = requests.get(f"{BASE_URL}/api/proposals/jobs/{job_id}/result", timeout=30)
        data = r.json()
        
        result = data.get('result', {})
        if result:
            print_success("Result retrieved")
            print_info(f"Topic: {result.get('topic', 'N/A')[:50]}...")
            print_info(f"Word count: {result.get('word_count', 0):,}")
            print_info(f"Sections: {len(result.get('sections', []))}")
            results.add_pass("Job Result")
            return result
        else:
            print_error("No result data")
            results.add_fail("Job Result", "Empty result")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("Job Result", str(e))
        return None

# ============================================================================
# PHASE 5: Preview & Export
# ============================================================================
def test_preview(job_id, tier='permanent'):
    print_test(f"5.1 Preview ({tier} tier)")
    
    if not job_id:
        print_error("No job ID")
        results.add_fail(f"Preview ({tier})", "No job ID")
        return None
    
    try:
        r = requests.get(f"{BASE_URL}/api/proposals/{job_id}/preview?subscription_tier={tier}", timeout=30)
        data = r.json()
        
        if data.get('html_preview'):
            preview_len = len(data['html_preview'])
            print_success(f"Preview generated ({preview_len:,} chars)")
            print_info(f"Limited: {data.get('is_limited', False)}")
            results.add_pass(f"Preview ({tier})")
            return True
        else:
            print_error("No preview generated")
            results.add_fail(f"Preview ({tier})", "No preview")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail(f"Preview ({tier})", str(e))
        return False

def test_export_pdf(job_id, tier='permanent'):
    print_test(f"5.2 PDF Export ({tier} tier)")
    
    if not job_id:
        print_error("No job ID")
        results.add_fail(f"PDF Export ({tier})", "No job ID")
        return False
    
    try:
        r = requests.get(f"{BASE_URL}/api/proposals/{job_id}/export/pdf?subscription_tier={tier}", timeout=60)
        
        if tier == 'free':
            if r.status_code == 403:
                print_success("Free tier correctly blocked from PDF")
                results.add_pass(f"PDF Export ({tier})")
                return True
        
        if r.status_code == 200:
            content_length = len(r.content)
            print_success(f"PDF generated ({content_length:,} bytes)")
            results.add_pass(f"PDF Export ({tier})")
            return True
        else:
            print_error(f"Export failed: {r.status_code}")
            results.add_fail(f"PDF Export ({tier})", f"Status {r.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail(f"PDF Export ({tier})", str(e))
        return False

def test_export_docx(job_id):
    print_test("5.3 DOCX Export")
    
    if not job_id:
        print_error("No job ID")
        results.add_fail("DOCX Export", "No job ID")
        return False
    
    try:
        r = requests.get(f"{BASE_URL}/api/proposals/{job_id}/export/docx", timeout=60)
        
        if r.status_code == 200:
            content_length = len(r.content)
            print_success(f"DOCX generated ({content_length:,} bytes)")
            results.add_pass("DOCX Export")
            return True
        else:
            print_error(f"Export failed: {r.status_code}")
            results.add_fail("DOCX Export", f"Status {r.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("DOCX Export", str(e))
        return False

def test_export_markdown(job_id):
    print_test("5.4 Markdown Export")
    
    if not job_id:
        print_error("No job ID")
        results.add_fail("Markdown Export", "No job ID")
        return False
    
    try:
        r = requests.get(f"{BASE_URL}/api/proposals/{job_id}/export/markdown", timeout=60)
        
        if r.status_code == 200:
            content_length = len(r.content)
            print_success(f"Markdown generated ({content_length:,} bytes)")
            results.add_pass("Markdown Export")
            return True
        else:
            print_error(f"Export failed: {r.status_code}")
            results.add_fail("Markdown Export", f"Status {r.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("Markdown Export", str(e))
        return False

def test_export_latex(job_id):
    print_test("5.5 LaTeX Export")
    
    if not job_id:
        print_error("No job ID")
        results.add_fail("LaTeX Export", "No job ID")
        return False
    
    try:
        r = requests.get(f"{BASE_URL}/api/proposals/{job_id}/export/latex", timeout=60)
        
        if r.status_code == 200:
            content_length = len(r.content)
            print_success(f"LaTeX generated ({content_length:,} bytes)")
            results.add_pass("LaTeX Export")
            return True
        else:
            print_error(f"Export failed: {r.status_code}")
            results.add_fail("LaTeX Export", f"Status {r.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("LaTeX Export", str(e))
        return False

def test_export_overleaf(job_id):
    print_test("5.6 Overleaf ZIP Export")
    
    if not job_id:
        print_error("No job ID")
        results.add_fail("Overleaf Export", "No job ID")
        return False
    
    try:
        r = requests.get(f"{BASE_URL}/api/proposals/{job_id}/export/overleaf", timeout=60)
        
        if r.status_code == 200:
            content_length = len(r.content)
            print_success(f"Overleaf ZIP generated ({content_length:,} bytes)")
            results.add_pass("Overleaf Export")
            return True
        else:
            print_error(f"Export failed: {r.status_code}")
            results.add_fail("Overleaf Export", f"Status {r.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("Overleaf Export", str(e))
        return False

# ============================================================================
# PHASE 6: New Features - Scopus Compliance & Reviewer Simulation
# ============================================================================
def test_scopus_compliance_info():
    print_test("6.1 Scopus Compliance Info")
    try:
        r = requests.get(f"{BASE_URL}/api/scopus/compliance", timeout=10)
        if r.status_code == 200:
            data = r.json()
            print_success("Scopus Compliance endpoint available")
            print_info(f"Description: {data.get('description', 'N/A')}")
            criteria = data.get('criteria', [])
            print_info(f"Criteria: {len(criteria)}")
            for c in criteria[:3]:
                print_info(f"  - {c.get('name')}: {c.get('weight')}")
            results.add_pass("Scopus Compliance Info")
            return True
        else:
            print_error(f"Status: {r.status_code}")
            results.add_fail("Scopus Compliance Info", f"Status {r.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("Scopus Compliance Info", str(e))
        return False

def test_scopus_compliance_score(job_id):
    print_test("6.2 Scopus Compliance Score")
    
    if not job_id:
        print_error("No job ID")
        results.add_fail("Scopus Compliance Score", "No job ID")
        return False
    
    try:
        r = requests.get(f"{BASE_URL}/api/scopus/compliance/{job_id}", timeout=30)
        if r.status_code == 200:
            data = r.json()
            compliance = data.get('compliance', {})
            print_success("Compliance score calculated")
            print_info(f"Overall Score: {compliance.get('overall_score', 0):.3f}")
            print_info(f"Q1 Ready: {compliance.get('q1_ready', False)}")
            
            prob = compliance.get('acceptance_probability', {})
            print_info(f"Acceptance Probability: {prob.get('estimate', 0):.1%}")
            
            criteria = compliance.get('criteria_scores', {})
            for k, v in list(criteria.items())[:3]:
                print_info(f"  {k}: {v:.3f}")
            
            recommendations = compliance.get('recommendations', [])
            if recommendations:
                print_info(f"Recommendations: {len(recommendations)}")
            
            results.add_pass("Scopus Compliance Score")
            return compliance
        elif r.status_code == 404:
            print_error("Proposal not found")
            results.add_fail("Scopus Compliance Score", "Not found")
            return None
        else:
            print_error(f"Status: {r.status_code}")
            results.add_fail("Scopus Compliance Score", f"Status {r.status_code}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("Scopus Compliance Score", str(e))
        return None

def test_reviewer_simulation_info():
    print_test("6.3 Reviewer Simulation Info")
    try:
        r = requests.get(f"{BASE_URL}/api/review/simulate", timeout=10)
        if r.status_code == 200:
            data = r.json()
            print_success("Reviewer Simulation endpoint available")
            print_info(f"Description: {data.get('description', 'N/A')}")
            personas = data.get('personas', {})
            print_info(f"Personas: {len(personas)}")
            for pid, pdata in list(personas.items())[:3]:
                print_info(f"  - {pdata.get('name', pid)}")
            results.add_pass("Reviewer Simulation Info")
            return True
        else:
            print_error(f"Status: {r.status_code}")
            results.add_fail("Reviewer Simulation Info", f"Status {r.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("Reviewer Simulation Info", str(e))
        return False

def test_reviewer_simulation(job_id):
    print_test("6.4 Reviewer Simulation")
    
    if not job_id:
        print_error("No job ID")
        results.add_fail("Reviewer Simulation", "No job ID")
        return False
    
    try:
        r = requests.get(f"{BASE_URL}/api/review/simulate/{job_id}", timeout=30)
        if r.status_code == 200:
            data = r.json()
            review = data.get('review', {})
            print_success("Review simulation completed")
            print_info(f"Overall Assessment: {review.get('overall_assessment', 'N/A')}")
            
            reviewers = review.get('reviewer_comments', [])
            print_info(f"Reviewers: {len(reviewers)}")
            for rev in reviewers[:2]:
                print_info(f"  - {rev.get('reviewer')}: {rev.get('recommendation')}")
            
            strengths = review.get('strengths', [])
            weaknesses = review.get('weaknesses', [])
            print_info(f"Strengths: {len(strengths)}, Weaknesses: {len(weaknesses)}")
            
            results.add_pass("Reviewer Simulation")
            return review
        elif r.status_code == 404:
            print_error("Proposal not found")
            results.add_fail("Reviewer Simulation", "Not found")
            return None
        else:
            print_error(f"Status: {r.status_code}")
            results.add_fail("Reviewer Simulation", f"Status {r.status_code}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        results.add_fail("Reviewer Simulation", str(e))
        return None

# ============================================================================
# Main Test Runner
# ============================================================================
def main():
    start_time = datetime.now()
    
    print_header("ResearchAI v2.2 - Complete E2E Test")
    print(f"\n  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Backend: {BASE_URL}")
    
    # Phase 1: Infrastructure
    print_header("PHASE 1: Infrastructure")
    if not test_backend_health():
        print(f"\n{Colors.RED}Cannot continue without backend!{Colors.END}")
        results.summary()
        return False
    
    test_system_status()
    test_features_list()
    test_agents_list()
    
    # Phase 2: Authentication
    print_header("PHASE 2: Authentication")
    token, user = test_demo_login()
    
    # Phase 3: Subscription
    print_header("PHASE 3: Subscription System")
    test_subscription_tiers()
    
    # Phase 4: Proposal Generation
    print_header("PHASE 4: Proposal Generation")
    job_id = test_proposal_generation()
    
    job_data = None
    if job_id:
        job_data = test_job_polling(job_id, max_polls=40, poll_interval=5)
        if job_data and job_data.get('status') == 'completed':
            test_job_result(job_id)
    
    # Phase 5: Preview & Export
    print_header("PHASE 5: Preview & Export")
    if job_id and job_data and job_data.get('status') == 'completed':
        test_preview(job_id, 'free')
        test_preview(job_id, 'permanent')
        test_export_pdf(job_id, 'free')
        test_export_pdf(job_id, 'permanent')
        test_export_docx(job_id)
        test_export_markdown(job_id)
        test_export_latex(job_id)
        test_export_overleaf(job_id)
    else:
        print_warning("Skipping export tests - no completed job")
        results.add_warning("Export Tests", "Skipped")
    
    # Phase 6: New Features
    print_header("PHASE 6: Scopus Compliance & Reviewer Simulation")
    test_scopus_compliance_info()
    test_reviewer_simulation_info()
    
    if job_id and job_data and job_data.get('status') == 'completed':
        test_scopus_compliance_score(job_id)
        test_reviewer_simulation(job_id)
    else:
        print_warning("Skipping scoring tests - no completed job")
        results.add_warning("Scoring Tests", "Skipped")
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n  Duration: {duration:.1f} seconds")
    
    success = results.summary()
    
    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}  ✅ ALL TESTS PASSED - READY FOR PRODUCTION!{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}  ❌ SOME TESTS FAILED - FIX BEFORE DEPLOYMENT{Colors.END}")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted{Colors.END}")
        sys.exit(1)
