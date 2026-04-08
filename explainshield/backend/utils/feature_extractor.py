import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False


# Feature patterns for extraction from text
FEATURE_PATTERNS = {
    "age": [
        r"(?:age|aged|old)\s*(?:is|:)?\s*(\d+)",
        r"(\d+)\s*(?:years?\s*old|y\.?o\.?)",
        r"claimant[^\d]*(\d+)",
    ],
    "income": [
        r"(?:annual\s*)?income[^\d]*(\d[\d,]*(?:\.\d{2})?)",
        r"(?:salary|earnings?|net\s*worth)[^\d]*(\d[\d,]*(?:\.\d{2})?)",
        r"₹\s*(\d[\d,]*(?:\.\d{2})?)",
        r"Rs\.?\s*(\d[\d,]*(?:\.\d{2})?)",
    ],
    "total_claim_amount": [
        r"(?:claim\s*amount|claimed|claim\s*value)[^\d]*(\d[\d,]*(?:\.\d{2})?)",
        r"(?:loss|damage)[^\d]*(\d[\d,]*(?:\.\d{2})?)",
        r"₹\s*(\d[\d,]*(?:\.\d{2})?)",
        r"Rs\.?\s*(\d[\d,]*(?:\.\d{2})?)",
    ],
    "policy_annual_premium": [
        r"(?:premium|policy\s*premium)[^\d]*(\d[\d,]*(?:\.\d{2})?)",
        r"(?:annual\s*premium)[^\d]*(\d[\d,]*(?:\.\d{2})?)",
    ],
    "months_as_customer": [
        r"(?:months?|years?)\s*(?:as\s*)?customer[^\d]*(\d+)",
        r"(?:customer\s*for|tenure)[^\d]*(\d+)\s*(?:months?|years?)",
        r"(\d+)\s*(?:months?|years?)\s*(?:customer|with\s*company)",
    ],
    "credit_score": [
        r"credit\s*score[^\d]*(\d{3})",
        r"(?:cibil\s*score|credit\s*rating)[^\d]*(\d{3})",
        r"(\d{3})\s*(?:credit\s*score|cibil)",
    ],
    "insured_sex": [
        r"(?:gender|sex)[^\d]*(male|female|man|woman|m|f)",
    ],
    "incident_state": [
        r"(?:state|location|incident)[^\d]*([A-Z]{2})",
    ],
    "insured_education_level": [
        r"(?:education|qualification|degree)[^\d]*(high\s*school|bachelor|master|phd|graduate|diploma|college)",
    ],
    "incident_type": [
        r"(?:incident\s*type|collision|type\s*of\s*incident)[^\d]*(single|multi|vehicle|theft|fire)",
    ],
    "incident_severity": [
        r"(?:severity|damage)[^\d]*(major|minor|total|fatal)",
    ],
    "policy_csl": [
        r"(?:csl|coverage\s*limit)[^\d]*(\d+\/\d+)",
    ],
    "insured_occupation": [
        r"(?:occupation|job|profession)[^\d]*([a-z]+(?:-[a-z]+)*)",
    ],
    "insured_relationship": [
        r"(?:relationship)[^\d]*(self|husband|wife|son|daughter|parent)",
    ],
    "number_of_vehicles_involved": [
        r"(\d+)\s*vehicles?\s*involved",
        r"(?:vehicles?\s*involved)[^\d]*(\d+)",
    ],
    "witnesses": [
        r"(\d+)\s*witness(?:es)?",
        r"(?:witness(?:es)?)[^\d]*(\d+)",
    ],
}

SENSITIVE_ATTRIBUTES = {
    "insured_sex": {"male": "MALE", "female": "FEMALE", "man": "MALE", "woman": "FEMALE", "m": "MALE", "f": "FEMALE"},
    "incident_state": None,
    "insured_education_level": None,
    "insured_relationship": None,
    "insured_occupation": None,
}

STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI",
    "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
    "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM",
    "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD",
    "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"
}


class FeatureExtractor:
    def __init__(self):
        self._embedder = None
        
    def _get_embedder(self):
        if self._embedder is None and ST_AVAILABLE:
            logger.info("Loading sentence-transformer model...")
            self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
        return self._embedder
    
    def extract_features(self, text: str, document_embeddings: list = None) -> Dict[str, Any]:
        """
        Extract structured features from document text and optionally use semantic embeddings.
        
        Args:
            text: Raw text from document
            document_embeddings: Optional embeddings for semantic search
            
        Returns:
            Dictionary of extracted features
        """
        features = {}
        
        # Rule-based extraction
        for feature_name, patterns in FEATURE_PATTERNS.items():
            value = self._extract_pattern(text, feature_name, patterns)
            if value is not None:
                features[feature_name] = value
        
        # Use embeddings for semantic feature extraction
        if document_embeddings and ST_AVAILABLE:
            semantic_features = self._semantic_extract(text, document_embeddings)
            features.update(semantic_features)
        
        # Fill defaults for missing required features
        features = self._fill_defaults(features)
        
        return features
    
    def _extract_pattern(self, text: str, feature_name: str, patterns: list) -> Optional[Any]:
        text_lower = text.lower()
        
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                value = match.group(1)
                
                # Clean and convert
                if feature_name in ("age", "months_as_customer", "number_of_vehicles_involved", "witnesses", "credit_score"):
                    try:
                        return int(re.sub(r"[^\d]", "", value))
                    except:
                        pass
                elif feature_name in ("income", "total_claim_amount", "policy_annual_premium"):
                    try:
                        cleaned = re.sub(r"[^\d.]", "", value)
                        return float(cleaned)
                    except:
                        pass
                elif feature_name == "insured_sex":
                    mapping = SENSITIVE_ATTRIBUTES.get("insured_sex", {})
                    return mapping.get(value.lower(), value.upper())
                elif feature_name == "incident_state":
                    candidate = value.upper()
                    if candidate in STATE_CODES:
                        return candidate
                elif feature_name == "policy_csl":
                    if "/" in value:
                        return value
                elif feature_name == "insured_education_level":
                    return value.title()
                elif feature_name == "incident_type":
                    return value.title()
                elif feature_name == "incident_severity":
                    return value.title()
                elif feature_name == "insured_occupation":
                    return value.lower().replace(" ", "-")
                elif feature_name == "insured_relationship":
                    return value.lower()
                
                return value
        
        return None
    
    def _semantic_extract(self, text: str, embeddings: list) -> dict:
        """
        Use embeddings to infer features that couldn't be extracted via patterns.
        """
        extracted = {}
        
        embedder = self._get_embedder()
        if embedder is None:
            return extracted
        
        # Known templates for common features
        templates = {
            "income": [
                "The claimant earns annually",
                "Monthly salary",
                "Annual income"
            ],
            "total_claim_amount": [
                "Claim amount",
                "Claimed damages",
                "Total loss"
            ],
        }
        
        for feature, query_templates in templates.items():
            best_score = 0
            best_value = None
            
            for template in query_templates:
                query_emb = embedder.encode([template])
                
                # Simple cosine similarity (manual computation)
                dot = sum(e * q for e, q in zip(embeddings, query_emb[0]))
                norm1 = sum(e * e for e in embeddings) ** 0.5
                norm2 = sum(q * q for q in query_emb[0]) ** 0.5
                
                if norm1 > 0 and norm2 > 0:
                    score = dot / (norm1 * norm2)
                    if score > best_score and score > 0.6:
                        best_score = score
                        best_value = feature
            
            if best_value:
                extracted[best_value] = best_score
        
        return extracted
    
    def _fill_defaults(self, features: dict) -> dict:
        defaults = {
            "age": 40,
            "policy_annual_premium": 1200.0,
            "total_claim_amount": 50000.0,
            "months_as_customer": 120,
            "number_of_vehicles_involved": 1,
            "witnesses": 1,
            "credit_score": 700,
            "insured_sex": "MALE",
            "incident_state": "OH",
            "insured_education_level": "Bachelor",
            "incident_type": "Single Vehicle Collision",
            "incident_severity": "Minor Damage",
            "policy_csl": "100/300",
            "insured_occupation": "other",
            "insured_relationship": "self"
        }
        
        for key, default_value in defaults.items():
            if key not in features:
                features[key] = default_value
        
        return features


def extract_features_from_text(text: str, embeddings: list = None) -> dict:
    """
    Convenience function for feature extraction.
    """
    extractor = FeatureExtractor()
    return extractor.extract_features(text, embeddings)


if __name__ == "__main__":
    print("Feature Extractor module loaded.")
    print(f"sentence-transformers available: {ST_AVAILABLE}")