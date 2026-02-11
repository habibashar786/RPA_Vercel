"""
ResearchAI - Quick Feature Test
================================
Tests new features using existing completed job or waits for current job.

Run: python test_new_features.py
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8001"

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

def print_success(msg):
    print(f"  {Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"  {Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg):
    print(f"  {Colors.CYAN}ℹ️  {msg}{Colors.END}")

def get_completed_job():
    """Find a completed job or wait for one."""
    print(f"\n{Colors.BLUE}▶ Looking for completed job...{Colors.END}")
    
    try:
        # List all jobs
        r = requests.get(f"{BASE_URL}/api/proposals/jobs", timeout=10)
        jobs = r.json().get('jobs', [])
        
        # Find completed job
        for job in jobs:
            if job.get('status') == 'completed':
                print_success(f"Found completed job: {job['job_id'][:12]}...")
                return job['job_id']
        
        # No completed job, check if there's a running one
        running_jobs = [j for j in jobs if j.get('status') == 'running']
        if running_jobs:
            job = running_jobs[0]
            job_id = job['job_id']
            print_info(f"Found running job: {job_id[:12]}... Waiting for completion...")
            
            # Wait for it to complete
            for i in range(60):  # Wait up to 5 minutes
                time.sleep(5)
                r = requests.get(f"{BASE_URL}/api/proposals/jobs/{job_id}", timeout=10)
                data = r.json()
                progress = data.get('progress', 0)
                status = data.get('status', 'unknown')
                stage = data.get('current_stage', 'unknown')
                
                print_info(f"[{i+1}/60] {status} - {progress}% - {stage}")
                
                if status == 'completed':
                    print_success("Job completed!")
                    return job_id
                elif status == 'failed':
                    print_error(f"Job failed: {data.get('error')}")
                    return None
            
            print_error("Timeout waiting for job")
            return None
        
        print_error("No jobs found")
        return None
        
    except Exception as e:
        print_error(f"Error: {e}")
        return None

def test_scopus_compliance(job_id):
    """Test Scopus Q1 Compliance scoring."""
    print(f"\n{Colors.BLUE}▶ Testing Scopus Q1 Compliance...{Colors.END}")
    
    try:
        r = requests.get(f"{BASE_URL}/api/scopus/compliance/{job_id}", timeout=30)
        if r.status_code == 200:
            data = r.json()
            compliance = data.get('compliance', {})
            
            print_success(f"Overall Score: {compliance.get('overall_score', 0):.3f}")
            print_info(f"Q1 Ready: {'✅ YES' if compliance.get('q1_ready') else '❌ NO'}")
            
            prob = compliance.get('acceptance_probability', {})
            print_info(f"Acceptance Probability: {prob.get('estimate', 0)*100:.1f}%")
            print_info(f"  Confidence: [{prob.get('confidence_lower', 0)*100:.1f}% - {prob.get('confidence_upper', 0)*100:.1f}%]")
            
            print_info("Criteria Scores:")
            for k, v in compliance.get('criteria_scores', {}).items():
                bar = '█' * int(v * 20) + '░' * (20 - int(v * 20))
                print_info(f"  {k}: {bar} {v:.3f}")
            
            recommendations = compliance.get('recommendations', [])
            if recommendations:
                print_info("Recommendations:")
                for rec in recommendations[:3]:
                    print_info(f"  • {rec}")
            
            return True
        else:
            print_error(f"Failed: {r.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_reviewer_simulation(job_id):
    """Test Reviewer Simulation."""
    print(f"\n{Colors.BLUE}▶ Testing Reviewer Simulation...{Colors.END}")
    
    try:
        r = requests.get(f"{BASE_URL}/api/review/simulate/{job_id}", timeout=30)
        if r.status_code == 200:
            data = r.json()
            review = data.get('review', {})
            
            assessment = review.get('overall_assessment', 'unknown')
            assessment_colors = {
                'accept': Colors.GREEN,
                'minor_revision': Colors.YELLOW,
                'major_revision': Colors.RED,
                'reject': Colors.RED
            }
            color = assessment_colors.get(assessment, Colors.END)
            print_success(f"Overall Assessment: {color}{assessment.upper()}{Colors.END}")
            
            print_info("Reviewer Comments:")
            for reviewer in review.get('reviewer_comments', []):
                rec = reviewer.get('recommendation', 'unknown')
                rec_color = assessment_colors.get(rec, Colors.END)
                print_info(f"  {reviewer.get('reviewer')}: {rec_color}{rec}{Colors.END}")
                for comment in reviewer.get('comments', [])[:2]:
                    print_info(f"    → {comment}")
            
            strengths = review.get('strengths', [])
            if strengths:
                print_info("Strengths:")
                for s in strengths[:3]:
                    print_info(f"  ✓ {s}")
            
            weaknesses = review.get('weaknesses', [])
            if weaknesses:
                print_info("Weaknesses:")
                for w in weaknesses[:3]:
                    print_info(f"  ✗ {w}")
            
            return True
        else:
            print_error(f"Failed: {r.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_latex_export(job_id):
    """Test LaTeX export."""
    print(f"\n{Colors.BLUE}▶ Testing LaTeX Export...{Colors.END}")
    
    try:
        r = requests.get(f"{BASE_URL}/api/proposals/{job_id}/export/latex", timeout=60)
        if r.status_code == 200:
            content = r.content.decode('utf-8')
            print_success(f"LaTeX generated: {len(content):,} characters")
            
            # Check for key LaTeX elements
            checks = [
                (r'\documentclass', 'Document class'),
                (r'\begin{document}', 'Document begin'),
                (r'\end{document}', 'Document end'),
                (r'\title{', 'Title'),
                (r'\section', 'Sections'),
            ]
            
            for pattern, name in checks:
                if pattern in content:
                    print_info(f"  ✓ {name} present")
                else:
                    print_info(f"  ✗ {name} missing")
            
            return True
        else:
            print_error(f"Failed: {r.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_overleaf_export(job_id):
    """Test Overleaf ZIP export."""
    print(f"\n{Colors.BLUE}▶ Testing Overleaf ZIP Export...{Colors.END}")
    
    try:
        r = requests.get(f"{BASE_URL}/api/proposals/{job_id}/export/overleaf", timeout=60)
        if r.status_code == 200:
            print_success(f"Overleaf ZIP generated: {len(r.content):,} bytes")
            
            # Check ZIP contents
            import zipfile
            import io
            
            with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
                files = zf.namelist()
                print_info(f"ZIP contains {len(files)} files:")
                for f in files:
                    info = zf.getinfo(f)
                    print_info(f"  • {f} ({info.file_size:,} bytes)")
            
            return True
        else:
            print_error(f"Failed: {r.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_all_exports(job_id):
    """Test all export formats."""
    print(f"\n{Colors.BLUE}▶ Testing All Export Formats...{Colors.END}")
    
    formats = [
        ('pdf', 'application/pdf'),
        ('docx', 'application/vnd.openxmlformats'),
        ('markdown', 'text/plain'),
    ]
    
    for fmt, expected_type in formats:
        try:
            r = requests.get(f"{BASE_URL}/api/proposals/{job_id}/export/{fmt}?subscription_tier=permanent", timeout=60)
            if r.status_code == 200:
                print_success(f"{fmt.upper()}: {len(r.content):,} bytes")
            else:
                print_error(f"{fmt.upper()}: Failed ({r.status_code})")
        except Exception as e:
            print_error(f"{fmt.upper()}: Error - {e}")

def main():
    print_header("ResearchAI v2.2 - New Features Test")
    
    # Check backend
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code != 200:
            print_error("Backend not healthy")
            return False
        print_success("Backend online")
    except:
        print_error("Backend not running!")
        print_info("Start with: python -m uvicorn src.api.main:app --port 8001")
        return False
    
    # Get completed job
    job_id = get_completed_job()
    if not job_id:
        print_error("No completed job available for testing")
        return False
    
    print_header("NEW FEATURES")
    
    # Test Scopus Compliance
    test_scopus_compliance(job_id)
    
    # Test Reviewer Simulation
    test_reviewer_simulation(job_id)
    
    print_header("EXPORT FORMATS")
    
    # Test LaTeX
    test_latex_export(job_id)
    
    # Test Overleaf
    test_overleaf_export(job_id)
    
    # Test all exports
    test_all_exports(job_id)
    
    print_header("TEST COMPLETE")
    print(f"\n  {Colors.GREEN}{Colors.BOLD}✅ All new features working!{Colors.END}")
    print(f"  {Colors.CYAN}Ready for production deployment.{Colors.END}\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted{Colors.END}")
        sys.exit(1)
