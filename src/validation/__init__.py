"""
Academic Validation Module v2.7.0
Turnitin Compliance & Originality Screening

This module provides:
- Finite State Machine for validation workflow
- Turnitin proxy integration (institutional)
- Deterministic rule-based evaluation
- Compliance certificate generation

Author: ResearchAI Platform
Version: 2.7.0
"""

from .state_machine import ValidationStateMachine, ValidationState
from .validation_rules import RuleEngine, ValidationResult, PRODUCTION_RULES
from .turnitin_proxy import TurnitinProxy, MockTurnitinProxy, TurnitinConfig
from .compliance_certificate import ComplianceCertificate, CertificateGenerator
from .academic_validation_layer import AcademicValidationLayer

__all__ = [
    'ValidationStateMachine',
    'ValidationState',
    'RuleEngine',
    'ValidationResult',
    'PRODUCTION_RULES',
    'TurnitinProxy',
    'MockTurnitinProxy',
    'TurnitinConfig',
    'ComplianceCertificate',
    'CertificateGenerator',
    'AcademicValidationLayer'
]

__version__ = "2.7.0"
