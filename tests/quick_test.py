"""
Quick Test Script - Validates core components without server
=============================================================

Run this first to check imports and basic functionality.
Then run the full test suite with the server running.

Usage: python tests/quick_test.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("\n" + "=" * 60)
print("  ResearchAI Quick Component Test")
print("=" * 60 + "\n")

tests_passed = 0
tests_failed = 0

def test(name, condition, error_msg=""):
    global tests_passed, tests_failed
    if condition:
        print(f"  ✅ {name}")
        tests_passed += 1
    else:
        print(f"  ❌ {name}: {error_msg}")
        tests_failed += 1

# ============================================
# TEST 1: Core Imports
# ============================================
print("\n📦 Testing Core Imports...\n")

try:
    from src.services.pdf_ingestion import PDFIngestionService, ParsedPaper, get_pdf_service
    test("PDF Ingestion Service", True)
except ImportError as e:
    test("PDF Ingestion Service", False, str(e))

try:
    from src.services.formatting_controller import FormattingController, get_formatting_controller
    test("Formatting Controller", True)
except ImportError as e:
    test("Formatting Controller", False, str(e))

try:
    from src.services.academic_structure import AcademicStructureTemplate, create_academic_template
    test("Academic Structure Template", True)
except ImportError as e:
    test("Academic Structure Template", False, str(e))

try:
    from src.agents.visual.visual_workflow_agent import VisualWorkflowAgent, DiagramType
    test("Visual Workflow Agent", True)
except ImportError as e:
    test("Visual Workflow Agent", False, str(e))

try:
    from src.api.extended_routes import extended_router
    test("Extended API Routes", True)
except ImportError as e:
    test("Extended API Routes", False, str(e))

# ============================================
# TEST 2: Service Initialization
# ============================================
print("\n🔧 Testing Service Initialization...\n")

try:
    pdf_service = get_pdf_service()
    test("PDF Service Init", pdf_service is not None)
except Exception as e:
    test("PDF Service Init", False, str(e))

try:
    formatter = get_formatting_controller()
    test("Formatter Init", formatter is not None)
except Exception as e:
    test("Formatter Init", False, str(e))

try:
    template = create_academic_template(
        title="Test",
        author_name="Test Author"
    )
    test("Academic Template Init", template is not None)
except Exception as e:
    test("Academic Template Init", False, str(e))

# ============================================
# TEST 3: Functionality Tests
# ============================================
print("\n⚙️ Testing Core Functionality...\n")

# Markdown removal
try:
    result = formatter.remove_markdown("**Bold** and *italic*")
    test("Markdown Removal", "Bold" in result and "**" not in result)
except Exception as e:
    test("Markdown Removal", False, str(e))

# Academic style
try:
    result = formatter.enforce_academic_style("don't can't won't")
    test("Academic Style", "cannot" in result)
except Exception as e:
    test("Academic Style", False, str(e))

# ParsedPaper citation
try:
    paper = ParsedPaper(
        file_path="/test.pdf",
        file_hash="abc123",
        title="Test Paper",
        authors=["Smith", "Jones", "Williams"],
        year=2024
    )
    citation = paper.get_citation_text("harvard")
    test("Harvard Citation (et al.)", "et al." in citation)
except Exception as e:
    test("Harvard Citation", False, str(e))

# Academic structure
try:
    title_page = template.generate_title_page()
    test("Title Page Generation", "content" in title_page)
except Exception as e:
    test("Title Page Generation", False, str(e))

try:
    toc = template.generate_table_of_contents()
    test("TOC Generation", len(toc) > 10)
except Exception as e:
    test("TOC Generation", False, str(e))

# Diagram types
try:
    types = [t.value for t in DiagramType]
    test("Diagram Types", len(types) >= 6)
except Exception as e:
    test("Diagram Types", False, str(e))

# ============================================
# TEST 4: Dependencies
# ============================================
print("\n📚 Testing Dependencies...\n")

try:
    import reportlab
    test("ReportLab (PDF export)", True)
except ImportError:
    test("ReportLab (PDF export)", False, "pip install reportlab")

try:
    import docx
    test("python-docx (DOCX export)", True)
except ImportError:
    test("python-docx (DOCX export)", False, "pip install python-docx")

try:
    import fitz
    test("PyMuPDF (PDF parsing)", True)
except ImportError:
    test("PyMuPDF (PDF parsing)", False, "pip install pymupdf")

try:
    from pdfminer.high_level import extract_text
    test("pdfminer (PDF parsing)", True)
except ImportError:
    test("pdfminer (PDF parsing)", False, "pip install pdfminer.six")

try:
    import httpx
    test("httpx (HTTP client)", True)
except ImportError:
    test("httpx (HTTP client)", False, "pip install httpx")

# ============================================
# SUMMARY
# ============================================
print("\n" + "=" * 60)
print("  SUMMARY")
print("=" * 60)
print(f"\n  ✅ Passed: {tests_passed}")
print(f"  ❌ Failed: {tests_failed}")

if tests_failed == 0:
    print("\n  🎉 All component tests passed!")
    print("  👉 Now start the server and run the full test suite:")
    print("     uvicorn src.api.main:app --reload --port 8001")
    print("     python tests/test_all_features.py")
else:
    print(f"\n  ⚠️ {tests_failed} test(s) failed. Fix the issues above first.")

print("\n" + "=" * 60 + "\n")

sys.exit(0 if tests_failed == 0 else 1)
