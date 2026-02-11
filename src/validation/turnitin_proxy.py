"""
Turnitin Integration Proxy v2.7.0

Security-First Integration:
- NEVER stores Turnitin credentials
- NEVER calls Turnitin endpoints directly
- Abstracts via institutional proxy/LMS
- Returns metadata only (no source text storage)

This module treats Turnitin as an external compliance oracle.
"""
import hashlib
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import logging
import random
import string

logger = logging.getLogger(__name__)


@dataclass
class TurnitinConfig:
    """
    Configuration for institutional Turnitin proxy.
    NO credentials are stored in this configuration.
    """
    proxy_url: str  # Institutional Turnitin proxy URL
    institution_id: str  # Institution identifier
    api_timeout: int = 120  # Request timeout in seconds
    # NOTE: Authentication is handled by the institutional proxy


@dataclass
class ScanResult:
    """
    Turnitin scan result containing metadata only.
    No source text is stored.
    """
    submission_id: str
    similarity_score: float
    ai_detection_score: Optional[float]
    source_matches: list
    scan_timestamp: str
    report_url: Optional[str]  # Link to institutional report
    status: str = "completed"
    error_message: Optional[str] = None


class TurnitinProxy:
    """
    Abstraction layer for Turnitin integration via institutional proxy.
    
    Security Guarantees:
    - No direct Turnitin API calls
    - No credential storage
    - Single request per submission (no retries)
    - Metadata only response handling
    """
    
    def __init__(self, config: TurnitinConfig):
        self.config = config
        self._initialized = True
        logger.info(
            f"[TurnitinProxy] Initialized for institution: {config.institution_id}"
        )
    
    async def submit_for_scan(
        self, 
        document_hash: str, 
        document_content: str,
        metadata: Dict[str, Any]
    ) -> Optional[ScanResult]:
        """
        Submit document to institutional Turnitin proxy.
        
        IMPORTANT: Single request only - NO automatic retries.
        
        Args:
            document_hash: SHA-256 hash of document
            document_content: Full document text
            metadata: Document metadata (title, author, etc.)
            
        Returns:
            ScanResult if successful, None if failed
        """
        try:
            # Import httpx here to avoid startup issues
            import httpx
            
            async with httpx.AsyncClient(timeout=self.config.api_timeout) as client:
                # Prepare submission payload
                payload = {
                    "document_hash": document_hash,
                    "content": document_content,
                    "institution_id": self.config.institution_id,
                    "metadata": {
                        "title": metadata.get("title", "Research Proposal"),
                        "author": metadata.get("author", "Anonymous"),
                        "submission_type": "research_proposal",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
                logger.info(
                    f"[TurnitinProxy] Submitting document (hash: {document_hash[:16]}...) "
                    f"to {self.config.proxy_url}"
                )
                
                # Single request - NO retry loop
                response = await client.post(
                    f"{self.config.proxy_url}/api/v1/scan",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(
                        f"[TurnitinProxy] Scan completed. "
                        f"Similarity: {data.get('similarity_score', 'N/A')}%"
                    )
                    
                    return ScanResult(
                        submission_id=data["submission_id"],
                        similarity_score=data["similarity_score"],
                        ai_detection_score=data.get("ai_detection_score"),
                        source_matches=data.get("sources", []),
                        scan_timestamp=data["timestamp"],
                        report_url=data.get("report_url"),
                        status="completed"
                    )
                else:
                    logger.error(
                        f"[TurnitinProxy] Proxy returned error: {response.status_code}"
                    )
                    return ScanResult(
                        submission_id="",
                        similarity_score=0.0,
                        ai_detection_score=None,
                        source_matches=[],
                        scan_timestamp=datetime.utcnow().isoformat(),
                        report_url=None,
                        status="error",
                        error_message=f"Proxy error: {response.status_code}"
                    )
                    
        except Exception as e:
            logger.error(f"[TurnitinProxy] Exception during scan: {e}")
            return None


class MockTurnitinProxy(TurnitinProxy):
    """
    Development/Testing mock for Turnitin integration.
    
    Simulates realistic scan results for development purposes.
    Replace with real TurnitinProxy in production.
    """
    
    def __init__(self, config: Optional[TurnitinConfig] = None):
        if config is None:
            config = TurnitinConfig(
                proxy_url="http://mock-turnitin-proxy",
                institution_id="MOCK_INSTITUTION"
            )
        super().__init__(config)
        logger.info("[MockTurnitinProxy] Using MOCK Turnitin proxy for development")
    
    async def submit_for_scan(
        self, 
        document_hash: str, 
        document_content: str,
        metadata: Dict[str, Any]
    ) -> ScanResult:
        """
        Generate mock scan result for development/testing.
        
        Simulates:
        - Realistic similarity scores (5-18%)
        - AI detection scores (0-15%)
        - Source match breakdown
        - Processing delay
        """
        # Simulate processing time (2-4 seconds)
        await asyncio.sleep(random.uniform(2.0, 4.0))
        
        # Generate realistic mock scores
        similarity = round(random.uniform(5.0, 18.0), 1)
        ai_score = round(random.uniform(0.0, 15.0), 1)
        
        # Generate mock source matches
        source_types = [
            "Academic Database",
            "Journal Repository", 
            "Open Access Archive",
            "University Repository",
            "Conference Proceedings",
            "Preprint Server"
        ]
        
        num_sources = random.randint(3, 6)
        sources = []
        remaining_percentage = similarity
        
        for i in range(num_sources):
            if i == num_sources - 1:
                pct = round(remaining_percentage, 1)
            else:
                pct = round(random.uniform(0.5, min(4.0, remaining_percentage - 1)), 1)
                remaining_percentage -= pct
            
            sources.append({
                "source": f"{random.choice(source_types)} {chr(65 + i)}",
                "percentage": max(0.1, pct),
                "url": f"https://example.com/source/{i+1}"
            })
        
        # Sort by percentage descending
        sources.sort(key=lambda x: x["percentage"], reverse=True)
        
        # Generate submission ID
        submission_id = f"MOCK-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
        
        logger.info(
            f"[MockTurnitinProxy] Mock scan completed. "
            f"Similarity: {similarity}%, AI: {ai_score}%"
        )
        
        return ScanResult(
            submission_id=submission_id,
            similarity_score=similarity,
            ai_detection_score=ai_score,
            source_matches=sources,
            scan_timestamp=datetime.utcnow().isoformat(),
            report_url=f"https://mock-turnitin.example.com/report/{submission_id}",
            status="completed"
        )
