"""
KYC Manager - Know Your Customer verification and management
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import hashlib
import base64

from .models import (
    KYCRequest, KYCResult, KYCStatus,
    DocumentType
)


class KYCManager:
    """
    Manages KYC verification processes
    """
    
    def __init__(self):
        self.logger = logging.getLogger("kyc_manager")
        self.kyc_records = {}  # user_id -> KYCResult
        self.verification_queue = asyncio.Queue()
        self.document_store = {}  # doc_hash -> document_data
        
    async def initialize(self):
        """Initialize KYC manager"""
        self.logger.info("Initializing KYC Manager")
        
        # In production:
        # - Connect to identity verification providers
        # - Load ML models for document verification
        # - Connect to government databases
        
    async def verify_identity(
        self,
        user_id: str,
        request: KYCRequest
    ) -> KYCResult:
        """Initiate identity verification"""
        self.logger.info(f"Starting KYC verification for user {user_id}")
        
        # Create initial result
        result = KYCResult(
            user_id=user_id,
            status=KYCStatus.PENDING,
            risk_score=0.0
        )
        
        # Run immediate checks
        checks_passed = []
        checks_failed = []
        
        # 1. Document validation
        doc_valid = await self._validate_document(request)
        if doc_valid:
            checks_passed.append("document_format")
        else:
            checks_failed.append("document_format")
            
        # 2. Age verification
        age_valid = await self._verify_age(request.date_of_birth)
        if age_valid:
            checks_passed.append("age_verification")
        else:
            checks_failed.append("age_verification")
            result.rejection_reason = "Must be 18 or older"
            
        # 3. Sanctions check
        sanctions_clear = await self._check_sanctions(
            request.first_name,
            request.last_name,
            request.nationality
        )
        if sanctions_clear:
            checks_passed.append("sanctions_check")
        else:
            checks_failed.append("sanctions_check")
            
        # 4. PEP check
        if request.is_pep:
            checks_passed.append("pep_disclosed")
            result.notes = f"PEP: {request.pep_details}"
            result.risk_score += 20
        else:
            checks_passed.append("pep_check")
            
        # 5. Address verification (if proof provided)
        if request.proof_of_address:
            address_valid = await self._verify_address(request)
            if address_valid:
                checks_passed.append("address_verification")
            else:
                checks_failed.append("address_verification")
                
        # Update result
        result.checks_passed = checks_passed
        result.checks_failed = checks_failed
        
        # Determine status
        if checks_failed:
            if "age_verification" in checks_failed or "sanctions_check" in checks_failed:
                result.status = KYCStatus.REJECTED
            else:
                result.status = KYCStatus.DOCUMENTS_REQUIRED
                result.notes = "Additional documentation required"
        else:
            # All immediate checks passed, move to review
            result.status = KYCStatus.UNDER_REVIEW
            
            # Store documents
            await self._store_documents(user_id, request)
            
            # Queue for manual/advanced verification
            await self.verification_queue.put({
                "user_id": user_id,
                "request": request,
                "result": result
            })
            
        # Calculate initial risk score
        result.risk_score = await self._calculate_risk_score(request, result)
        
        # Store result
        self.kyc_records[user_id] = result
        
        return result
        
    async def _validate_document(self, request: KYCRequest) -> bool:
        """Validate document format and basic checks"""
        # Check document number format based on type
        if request.document_type == DocumentType.PASSPORT:
            # Passport validation (simplified)
            return len(request.document_number) >= 6
        elif request.document_type == DocumentType.DRIVERS_LICENSE:
            # Driver's license validation
            return len(request.document_number) >= 5
        else:
            # Generic validation
            return len(request.document_number) >= 5
            
    async def _verify_age(self, date_of_birth: Any) -> bool:
        """Verify user is 18 or older"""
        from datetime import date
        
        today = date.today()
        age = today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )
        
        return age >= 18
        
    async def _check_sanctions(
        self,
        first_name: str,
        last_name: str,
        nationality: str
    ) -> bool:
        """Check against sanctions lists"""
        # In production, check against:
        # - OFAC SDN List
        # - UN Sanctions List
        # - EU Consolidated List
        # - Local sanctions lists
        
        # Mock check - block certain nationalities
        sanctioned_countries = ["IR", "KP", "SY"]
        
        if nationality in sanctioned_countries:
            return False
            
        # Mock name check
        sanctioned_names = ["test", "blocked"]
        full_name = f"{first_name} {last_name}".lower()
        
        for name in sanctioned_names:
            if name in full_name:
                return False
                
        return True
        
    async def _verify_address(self, request: KYCRequest) -> bool:
        """Verify address proof"""
        # In production:
        # - OCR to extract address from document
        # - Match with provided address
        # - Check document authenticity
        
        # Mock verification
        return bool(request.proof_of_address)
        
    async def _store_documents(self, user_id: str, request: KYCRequest):
        """Store KYC documents securely"""
        # In production:
        # - Encrypt documents
        # - Store in secure storage (S3, etc.)
        # - Generate audit trail
        
        docs = []
        
        if request.document_front:
            doc_hash = hashlib.sha256(request.document_front.encode()).hexdigest()
            self.document_store[doc_hash] = {
                "user_id": user_id,
                "type": "document_front",
                "data": request.document_front,
                "uploaded_at": datetime.now()
            }
            docs.append(doc_hash)
            
        if request.document_back:
            doc_hash = hashlib.sha256(request.document_back.encode()).hexdigest()
            self.document_store[doc_hash] = {
                "user_id": user_id,
                "type": "document_back",
                "data": request.document_back,
                "uploaded_at": datetime.now()
            }
            docs.append(doc_hash)
            
        self.logger.info(f"Stored {len(docs)} documents for user {user_id}")
        
    async def _calculate_risk_score(
        self,
        request: KYCRequest,
        result: KYCResult
    ) -> float:
        """Calculate KYC risk score"""
        score = 0.0
        
        # Country risk
        high_risk_countries = ["AF", "YE", "LY", "SO"]
        medium_risk_countries = ["NG", "PK", "LB", "EG"]
        
        if request.nationality in high_risk_countries:
            score += 30
        elif request.nationality in medium_risk_countries:
            score += 15
            
        # PEP risk
        if request.is_pep:
            score += 25
            
        # Occupation risk
        high_risk_occupations = ["cash business", "money services", "gambling"]
        if any(risk in request.occupation.lower() for risk in high_risk_occupations):
            score += 20
            
        # Source of funds risk
        high_risk_sources = ["cash", "cryptocurrency", "third party"]
        if any(risk in request.source_of_funds.lower() for risk in high_risk_sources):
            score += 15
            
        # Failed checks
        score += len(result.checks_failed) * 10
        
        # Cap at 100
        return min(100, score)
        
    async def complete_verification(
        self,
        user_id: str,
        verification_id: str
    ):
        """Complete the verification process"""
        # In production, this would involve:
        # - Manual review by compliance team
        # - Advanced document verification
        # - Biometric checks
        # - Database cross-references
        
        # Mock completion
        await asyncio.sleep(5)  # Simulate processing
        
        result = self.kyc_records.get(user_id)
        if result and result.verification_id == verification_id:
            # Mock 90% success rate
            import random
            if random.random() < 0.9:
                result.status = KYCStatus.VERIFIED
                result.verified_at = datetime.now()
                result.expires_at = datetime.now() + timedelta(days=365)
                result.risk_level = self._get_risk_level(result.risk_score)
                
                self.logger.info(f"KYC verified for user {user_id}")
            else:
                result.status = KYCStatus.REJECTED
                result.rejection_reason = "Unable to verify identity"
                
                self.logger.warning(f"KYC rejected for user {user_id}")
                
    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level from score"""
        if risk_score < 20:
            return "low"
        elif risk_score < 50:
            return "medium"
        else:
            return "high"
            
    async def get_kyc_status(self, user_id: str) -> Optional[KYCResult]:
        """Get user's KYC status"""
        result = self.kyc_records.get(user_id)
        
        # Check if expired
        if result and result.expires_at and result.expires_at < datetime.now():
            result.status = KYCStatus.EXPIRED
            
        return result
        
    async def update_kyc_status(
        self,
        user_id: str,
        status: KYCStatus,
        notes: Optional[str] = None
    ):
        """Update KYC status"""
        result = self.kyc_records.get(user_id)
        if result:
            result.status = status
            if notes:
                result.notes = notes
                
            self.logger.info(f"Updated KYC status for user {user_id} to {status}")
            
    async def get_verification_queue_size(self) -> int:
        """Get number of pending verifications"""
        return self.verification_queue.qsize()
        
    async def process_verification_queue(self):
        """Process verification queue (for background task)"""
        while True:
            try:
                item = await self.verification_queue.get()
                user_id = item["user_id"]
                result = item["result"]
                
                # Simulate verification process
                await self.complete_verification(user_id, result.verification_id)
                
            except Exception as e:
                self.logger.error(f"Error processing verification: {str(e)}")
                
    async def generate_kyc_report(self, user_id: str) -> Dict[str, Any]:
        """Generate KYC report for user"""
        result = self.kyc_records.get(user_id)
        if not result:
            return {"error": "No KYC record found"}
            
        return {
            "user_id": user_id,
            "verification_id": result.verification_id,
            "status": result.status.value,
            "risk_level": result.risk_level,
            "risk_score": result.risk_score,
            "verified_at": result.verified_at.isoformat() if result.verified_at else None,
            "expires_at": result.expires_at.isoformat() if result.expires_at else None,
            "checks": {
                "passed": result.checks_passed,
                "failed": result.checks_failed
            },
            "notes": result.notes
        }
        
    async def bulk_kyc_check(self, user_ids: List[str]) -> Dict[str, KYCStatus]:
        """Check KYC status for multiple users"""
        results = {}
        
        for user_id in user_ids:
            result = await self.get_kyc_status(user_id)
            results[user_id] = result.status if result else KYCStatus.NOT_STARTED
            
        return results 