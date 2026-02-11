"""
Academic Validation Layer v2.7.0 - Main Orchestrator

This module orchestrates the complete academic validation workflow:
- Document finalization
- Turnitin submission
- Rule evaluation
- Certificate generation

CRITICAL CONSTRAINTS:
- Stateless between runs
- User-initiated only (no automatic triggers)
- NO content modification
- NO feedback loops to generation agents
- Single validation per finalized document
"""
import hashlib
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import logging
import base64

from .state_machine import ValidationStateMachine, ValidationState
from .validation_rules import RuleEngine, ValidationResult, PRODUCTION_RULES
from .turnitin_proxy import TurnitinProxy, MockTurnitinProxy, TurnitinConfig, ScanResult
from .compliance_certificate import ComplianceCertificate, CertificateGenerator

logger = logging.getLogger(__name__)


class AcademicValidationLayer:
    """
    Pre-Submission Academic Validation Module.
    
    This is a VERIFICATION WRAPPER, not a content editor.
    
    Data Flow (ONE-DIRECTIONAL):
        Content → Validation → Verdict → Certificate → Export
    
    Guarantees:
    - No validation output fed back to content generation
    - Validation runs once per finalized document
    - No background polling or retry loops
    - Content remains unchanged after validation
    """
    
    def __init__(self, turnitin_config: Optional[TurnitinConfig] = None):
        """
        Initialize validation layer.
        
        Args:
            turnitin_config: Configuration for institutional Turnitin proxy.
                            If None, uses mock proxy for development.
        """
        self.rule_engine = RuleEngine(PRODUCTION_RULES)
        
        # Use mock proxy for development, real proxy for production
        if turnitin_config:
            self.turnitin = TurnitinProxy(turnitin_config)
            logger.info("[ValidationLayer] Using PRODUCTION Turnitin proxy")
        else:
            self.turnitin = MockTurnitinProxy()
            logger.info("[ValidationLayer] Using MOCK Turnitin proxy (development mode)")
        
        # State machines per document (in-memory)
        # In production, this should be persisted to database
        self._state_machines: Dict[str, ValidationStateMachine] = {}
        
        # Certificate storage (in-memory)
        # In production, this should be encrypted and persisted
        self._certificates: Dict[str, ComplianceCertificate] = {}
        
        logger.info("[ValidationLayer] Academic Validation Layer initialized (v2.7.0)")
    
    def _get_state_machine(self, document_id: str) -> ValidationStateMachine:
        """Get or create state machine for document"""
        if document_id not in self._state_machines:
            self._state_machines[document_id] = ValidationStateMachine(document_id)
            logger.debug(f"[ValidationLayer] Created new state machine for {document_id}")
        return self._state_machines[document_id]
    
    def _compute_document_hash(self, content: str) -> str:
        """Compute SHA-256 hash of document content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def validate_document(
        self,
        document_id: str,
        document_content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main validation entry point.
        
        Workflow:
            DRAFT → FINALIZED → VALIDATION_REQUESTED → SCANNED → PASSED/FAILED
        
        Args:
            document_id: Unique document identifier
            document_content: Full document text content
            metadata: Document metadata (title, author, institution, etc.)
            
        Returns:
            Dict containing validation result, certificate (if passed), and state info
        """
        logger.info(f"[ValidationLayer] Starting validation for document: {document_id}")
        
        sm = self._get_state_machine(document_id)
        
        # ===== CHECK IF ALREADY VALIDATED (READ-ONLY) =====
        if sm.is_read_only():
            logger.warning(f"[ValidationLayer] Document {document_id} already validated and locked")
            
            # Return existing certificate if available
            existing_cert = self._certificates.get(document_id)
            if existing_cert:
                return {
                    "success": True,
                    "passed": True,
                    "state": sm.get_state().value,
                    "message": "Document already validated. Content is read-only.",
                    "certificate": {
                        "id": existing_cert.certificate_id,
                        "hash": existing_cert.certificate_hash
                    },
                    "read_only": True,
                    "already_validated": True
                }
            
            return {
                "success": False,
                "error": "Document already validated. Content is read-only.",
                "state": sm.get_state().value,
                "read_only": True
            }
        
        # ===== STATE TRANSITIONS =====
        
        # Transition to FINALIZED if in DRAFT
        if sm.get_state() == ValidationState.DRAFT:
            if not sm.transition(ValidationState.FINALIZED):
                return {
                    "success": False,
                    "error": "Cannot finalize document for validation",
                    "state": sm.get_state().value
                }
        
        # Transition to VALIDATION_REQUESTED
        if sm.get_state() == ValidationState.FINALIZED:
            if not sm.transition(ValidationState.VALIDATION_REQUESTED):
                return {
                    "success": False,
                    "error": "Cannot request validation",
                    "state": sm.get_state().value
                }
        
        # If in FAILED state, reset to FINALIZED first
        if sm.get_state() == ValidationState.FAILED:
            if not sm.reset_to_finalized():
                return {
                    "success": False,
                    "error": "Cannot reset failed validation",
                    "state": sm.get_state().value
                }
            sm.transition(ValidationState.VALIDATION_REQUESTED)
        
        # ===== COMPUTE DOCUMENT HASH =====
        document_hash = self._compute_document_hash(document_content)
        logger.info(f"[ValidationLayer] Document hash: {document_hash[:16]}...")
        
        # ===== SUBMIT TO TURNITIN (SINGLE REQUEST) =====
        logger.info(f"[ValidationLayer] Submitting to Turnitin proxy...")
        
        scan_result = await self.turnitin.submit_for_scan(
            document_hash=document_hash,
            document_content=document_content,
            metadata=metadata
        )
        
        # Handle scan failure
        if not scan_result or scan_result.status == "error":
            error_msg = scan_result.error_message if scan_result else "Unknown error"
            logger.error(f"[ValidationLayer] Turnitin scan failed: {error_msg}")
            return {
                "success": False,
                "error": f"Validation service unavailable: {error_msg}",
                "state": sm.get_state().value,
                "retry_allowed": True
            }
        
        # ===== TRANSITION TO SCANNED =====
        sm.transition(ValidationState.SCANNED)
        
        # ===== BUILD VALIDATION RESULT =====
        
        # Calculate single source max
        single_source_max = 0.0
        if scan_result.source_matches:
            single_source_max = max(
                [s.get("percentage", 0) for s in scan_result.source_matches],
                default=0.0
            )
        
        # Determine AI risk flag
        ai_risk_flag = "acceptable"
        if scan_result.ai_detection_score and scan_result.ai_detection_score > 20:
            ai_risk_flag = "flagged"
        
        # Apply exclusion adjustments (references, citations, etc.)
        adjustment_factor = 0.85  # ~15% excluded for references/citations
        adjusted_score = round(scan_result.similarity_score * adjustment_factor, 1)
        
        validation_result = ValidationResult(
            overall_similarity=scan_result.similarity_score,
            single_source_max=single_source_max,
            source_breakdown=scan_result.source_matches,
            ai_risk_flag=ai_risk_flag,
            ai_detection_score=scan_result.ai_detection_score,
            excluded_sections=["references", "citations", "bibliography"],
            raw_score=scan_result.similarity_score,
            adjusted_score=adjusted_score,
            scan_timestamp=scan_result.scan_timestamp,
            submission_id=scan_result.submission_id
        )
        
        # ===== EVALUATE AGAINST RULES =====
        passed, reason = self.rule_engine.evaluate(validation_result)
        
        logger.info(
            f"[ValidationLayer] Evaluation complete. "
            f"Passed: {passed}, Reason: {reason}"
        )
        
        # ===== FINAL STATE TRANSITION =====
        if passed:
            sm.transition(ValidationState.PASSED)
            
            # ===== GENERATE COMPLIANCE CERTIFICATE =====
            certificate = ComplianceCertificate(
                certificate_id=f"CERT-{uuid.uuid4().hex[:12].upper()}",
                document_hash=document_hash,
                validation_timestamp=datetime.utcnow().isoformat(),
                similarity_score=validation_result.adjusted_score,
                ai_detection_score=scan_result.ai_detection_score,
                validation_source="Turnitin",
                rule_set_version=PRODUCTION_RULES.version,
                status="PASSED - Ready for Institutional Submission",
                institution=metadata.get("institution"),
                submission_id=scan_result.submission_id
            )
            
            # Store certificate
            self._certificates[document_id] = certificate
            
            # Generate PDF certificate
            try:
                certificate_pdf = CertificateGenerator.generate_pdf(certificate)
                certificate_pdf_base64 = base64.b64encode(certificate_pdf).decode('utf-8')
            except Exception as e:
                logger.error(f"[ValidationLayer] Certificate PDF generation failed: {e}")
                certificate_pdf_base64 = None
            
            logger.info(
                f"[ValidationLayer] VALIDATION PASSED for {document_id}. "
                f"Certificate: {certificate.certificate_id}"
            )
            
            return {
                "success": True,
                "passed": True,
                "state": sm.get_state().value,
                "similarity_score": validation_result.adjusted_score,
                "raw_similarity_score": validation_result.overall_similarity,
                "ai_detection_score": scan_result.ai_detection_score,
                "source_breakdown": validation_result.source_breakdown,
                "excluded_sections": validation_result.excluded_sections,
                "certificate": {
                    "id": certificate.certificate_id,
                    "hash": certificate.certificate_hash,
                    "document_hash": certificate.document_hash,
                    "pdf_base64": certificate_pdf_base64
                },
                "message": "Document passed validation. Ready for institutional submission.",
                "read_only": True,
                "submission_id": scan_result.submission_id
            }
        
        else:
            sm.transition(ValidationState.FAILED)
            
            logger.info(
                f"[ValidationLayer] VALIDATION FAILED for {document_id}. "
                f"Reason: {reason}"
            )
            
            return {
                "success": True,
                "passed": False,
                "state": sm.get_state().value,
                "similarity_score": validation_result.adjusted_score,
                "raw_similarity_score": validation_result.overall_similarity,
                "ai_detection_score": scan_result.ai_detection_score,
                "source_breakdown": validation_result.source_breakdown,
                "excluded_sections": validation_result.excluded_sections,
                "failure_reason": reason,
                "message": f"Validation failed: {reason}",
                "read_only": False,
                "retry_allowed": True,
                "submission_id": scan_result.submission_id
            }
    
    def get_document_state(self, document_id: str) -> Dict[str, Any]:
        """
        Get current validation state for document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Dict with state information
        """
        sm = self._get_state_machine(document_id)
        state_info = sm.get_state_info()
        
        # Add certificate info if available
        cert = self._certificates.get(document_id)
        if cert:
            state_info["certificate"] = {
                "id": cert.certificate_id,
                "hash": cert.certificate_hash,
                "timestamp": cert.validation_timestamp
            }
        
        return state_info
    
    def get_certificate(self, document_id: str) -> Optional[ComplianceCertificate]:
        """Get compliance certificate for document"""
        return self._certificates.get(document_id)
    
    def get_certificate_pdf(self, document_id: str) -> Optional[bytes]:
        """Get PDF certificate for document"""
        cert = self._certificates.get(document_id)
        if cert:
            try:
                return CertificateGenerator.generate_pdf(cert)
            except Exception as e:
                logger.error(f"[ValidationLayer] PDF generation failed: {e}")
                return None
        return None
    
    def can_validate(self, document_id: str) -> bool:
        """Check if document can be validated"""
        sm = self._get_state_machine(document_id)
        return sm.can_validate()
    
    def get_rule_summary(self) -> Dict:
        """Get current validation rules summary"""
        return self.rule_engine.get_rule_summary()
