"""
Academic Validation State Machine v2.7.0
Deterministic, No Loops, Atomic Transitions

State Flow:
    DRAFT → FINALIZED → VALIDATION_REQUESTED → SCANNED → PASSED | FAILED

Rules:
- Once PASSED, content becomes READ-ONLY
- No automatic transition back to DRAFT
- State transitions are atomic and logged
"""
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class ValidationState(Enum):
    """Validation workflow states"""
    DRAFT = "draft"
    FINALIZED = "finalized"
    VALIDATION_REQUESTED = "validation_requested"
    SCANNED = "scanned"
    PASSED = "passed"
    FAILED = "failed"


# Valid state transitions (deterministic, one-directional)
VALID_TRANSITIONS: Dict[ValidationState, List[ValidationState]] = {
    ValidationState.DRAFT: [ValidationState.FINALIZED],
    ValidationState.FINALIZED: [ValidationState.VALIDATION_REQUESTED],
    ValidationState.VALIDATION_REQUESTED: [ValidationState.SCANNED],
    ValidationState.SCANNED: [ValidationState.PASSED, ValidationState.FAILED],
    ValidationState.PASSED: [],  # Terminal state - READ-ONLY
    ValidationState.FAILED: [ValidationState.FINALIZED],  # Allow re-finalize only
}


class ValidationStateMachine:
    """
    Finite State Machine for academic validation.
    
    Guarantees:
    - Atomic transitions only
    - No automatic retries
    - Logged state changes
    - Terminal state locking
    """
    
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.current_state = ValidationState.DRAFT
        self.transition_log: List[Dict] = []
        self._locked = False
        self._created_at = datetime.utcnow().isoformat()
        
        logger.info(f"[FSM:{document_id}] State machine initialized in DRAFT state")
    
    def transition(self, target_state: ValidationState) -> bool:
        """
        Attempt atomic state transition.
        
        Args:
            target_state: The desired target state
            
        Returns:
            bool: True if transition successful, False otherwise
        """
        # Check if document is locked (PASSED state)
        if self._locked:
            logger.warning(
                f"[FSM:{self.document_id}] Transition blocked - document is locked (PASSED state)"
            )
            return False
        
        # Validate transition is allowed
        allowed_transitions = VALID_TRANSITIONS.get(self.current_state, [])
        if target_state not in allowed_transitions:
            logger.error(
                f"[FSM:{self.document_id}] Invalid transition: "
                f"{self.current_state.value} → {target_state.value}. "
                f"Allowed: {[s.value for s in allowed_transitions]}"
            )
            return False
        
        # Perform atomic transition
        previous_state = self.current_state
        self.current_state = target_state
        
        # Log transition
        transition_record = {
            "from": previous_state.value,
            "to": target_state.value,
            "timestamp": datetime.utcnow().isoformat(),
            "document_id": self.document_id
        }
        self.transition_log.append(transition_record)
        
        # Lock if transitioned to PASSED
        if target_state == ValidationState.PASSED:
            self._locked = True
            logger.info(
                f"[FSM:{self.document_id}] Document LOCKED - validation PASSED. "
                f"Content is now read-only."
            )
        
        logger.info(
            f"[FSM:{self.document_id}] State transition: "
            f"{previous_state.value} → {target_state.value}"
        )
        
        return True
    
    def is_read_only(self) -> bool:
        """Check if document is in read-only state"""
        return self._locked or self.current_state == ValidationState.PASSED
    
    def get_state(self) -> ValidationState:
        """Get current validation state"""
        return self.current_state
    
    def get_state_info(self) -> Dict:
        """Get comprehensive state information"""
        return {
            "document_id": self.document_id,
            "current_state": self.current_state.value,
            "is_read_only": self.is_read_only(),
            "is_locked": self._locked,
            "created_at": self._created_at,
            "transition_count": len(self.transition_log),
            "transition_log": self.transition_log
        }
    
    def can_validate(self) -> bool:
        """Check if document can be submitted for validation"""
        return (
            not self._locked and 
            self.current_state in [ValidationState.DRAFT, ValidationState.FINALIZED, ValidationState.FAILED]
        )
    
    def reset_to_finalized(self) -> bool:
        """
        Reset failed validation to finalized state.
        Only allowed from FAILED state.
        """
        if self.current_state != ValidationState.FAILED:
            logger.warning(
                f"[FSM:{self.document_id}] Cannot reset - not in FAILED state"
            )
            return False
        
        return self.transition(ValidationState.FINALIZED)
