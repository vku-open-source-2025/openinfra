"""
AI Verification Service for Incident Reports using Gemini.
Analyzes incident report details to verify legitimacy.
"""
import os
import re
import logging
import httpx
from typing import Optional, Dict, Any
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIVerificationService:
    """Service for AI-based incident report verification using Gemini."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set, AI verification will not work")
            self.llm = None
            return
        
        # Use stable model for production reliability
        # Verification service doesn't need live streaming, so always use stable
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_CHAT_MODEL_STABLE,
            google_api_key=self.api_key,
            temperature=0.1,  # Low temperature for consistent scoring
        )
    
    async def verify_incident_report(
        self,
        incident_title: str,
        incident_description: str,
        incident_category: str,
        incident_severity: str,
        asset_type: Optional[str] = None,
        asset_name: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze incident report and return verification result.
        
        Uses Gemini to evaluate if the report content is legitimate
        and consistent with the reported category and severity.
        
        Args:
            incident_title: Title of the incident report
            incident_description: Detailed description
            incident_category: Category (damage, malfunction, safety_hazard, etc.)
            incident_severity: Severity level (low, medium, high, critical)
            asset_type: Type of the asset being reported on
            asset_name: Name of the asset
            image_url: URL of the uploaded evidence image (optional)
        
        Returns:
            {
                "confidence_score": float (0.0-1.0),
                "is_verified": bool (score >= 0.8),
                "verification_status": str ("verified" | "to_be_verified"),
                "reason": str
            }
        """
        if not self.llm:
            logger.warning("AI verification skipped - Gemini not configured")
            return {
                "confidence_score": None,
                "is_verified": False,
                "verification_status": "pending",
                "reason": "AI verification not configured"
            }
        
        try:
            # Build analysis prompt
            prompt = self._build_verification_prompt(
                incident_title,
                incident_description,
                incident_category,
                incident_severity,
                asset_type,
                asset_name,
                image_url
            )
            
            # If we have an image URL, try to include it
            message_content = []
            
            if image_url:
                try:
                    # Download image and encode as base64
                    image_data = await self._download_image(image_url)
                    if image_data:
                        message_content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        })
                except Exception as e:
                    logger.warning(f"Failed to include image in verification: {e}")
            
            message_content.append({"type": "text", "text": prompt})
            
            # Call Gemini
            message = HumanMessage(content=message_content)
            response = await self.llm.ainvoke([message])
            
            # Parse response
            result = self._parse_verification_response(response.content)
            
            logger.info(
                f"AI verification completed: score={result['confidence_score']}, "
                f"status={result['verification_status']}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"AI verification failed: {e}")
            return {
                "confidence_score": None,
                "is_verified": False,
                "verification_status": "failed",
                "reason": f"Verification failed: {str(e)}"
            }
    
    def _build_verification_prompt(
        self,
        title: str,
        description: str,
        category: str,
        severity: str,
        asset_type: Optional[str],
        asset_name: Optional[str],
        has_image: bool
    ) -> str:
        """Build the verification prompt for Gemini."""
        
        asset_info = ""
        if asset_type or asset_name:
            asset_info = f"\n- Asset Type: {asset_type or 'Not specified'}"
            if asset_name:
                asset_info += f"\n- Asset Name: {asset_name}"
        
        image_note = ""
        if has_image:
            image_note = "\n\nAn image has been provided as evidence. Please consider the image in your analysis."
        
        return f"""You are an AI assistant helping to verify the legitimacy of infrastructure incident reports.
        
Analyze the following incident report and determine if it appears to be a legitimate report or potentially spam/fake.

**Incident Report:**
- Title: {title}
- Description: {description}
- Category: {category}
- Severity: {severity}{asset_info}{image_note}

**Evaluation Criteria:**
1. Does the description provide enough detail about the actual problem?
2. Is the severity level appropriate for what's being described?
3. Does the category match the type of issue described?
4. Does the report seem genuine (not spam, test data, or nonsense)?
5. If an image is provided, does it appear relevant to the reported issue?

**Your Response Format (STRICT):**
Respond with ONLY the following format, nothing else:

CONFIDENCE_SCORE: [number between 0 and 100]
REASON: [brief explanation in 1-2 sentences]

Examples:
- A detailed report about a broken street light with specific location → CONFIDENCE_SCORE: 85
- A vague report saying just "broken" with no details → CONFIDENCE_SCORE: 40
- A report with random text or obvious spam → CONFIDENCE_SCORE: 10

Analyze this report now:"""
    
    def _parse_verification_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI response to extract confidence score and reason."""
        
        # Default values
        confidence_score = 0.5
        reason = "Unable to parse verification response"
        
        try:
            # Extract confidence score
            score_match = re.search(r'CONFIDENCE_SCORE:\s*(\d+(?:\.\d+)?)', response_text, re.IGNORECASE)
            if score_match:
                score = float(score_match.group(1))
                # Normalize to 0-1 range if given as percentage
                confidence_score = score / 100 if score > 1 else score
                confidence_score = max(0.0, min(1.0, confidence_score))  # Clamp to 0-1
            
            # Extract reason
            reason_match = re.search(r'REASON:\s*(.+?)(?:\n|$)', response_text, re.IGNORECASE | re.DOTALL)
            if reason_match:
                reason = reason_match.group(1).strip()
        
        except Exception as e:
            logger.warning(f"Error parsing verification response: {e}")
            reason = f"Parse error: {response_text[:100]}"
        
        # Determine verification status based on 80% threshold
        is_verified = confidence_score >= 0.8
        verification_status = "verified" if is_verified else "to_be_verified"
        
        return {
            "confidence_score": confidence_score,
            "is_verified": is_verified,
            "verification_status": verification_status,
            "reason": reason
        }
    
    async def _download_image(self, image_url: str) -> Optional[str]:
        """Download image from URL and return base64 encoded string."""
        import base64
        
        try:
            response = await self.http_client.get(image_url)
            response.raise_for_status()
            return base64.b64encode(response.content).decode('utf-8')
        except Exception as e:
            logger.warning(f"Failed to download image from {image_url}: {e}")
            return None
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()


# Singleton instance
_verification_service: Optional[AIVerificationService] = None


def get_verification_service() -> AIVerificationService:
    """Get or create the AI verification service singleton."""
    global _verification_service
    if _verification_service is None:
        _verification_service = AIVerificationService()
    return _verification_service
