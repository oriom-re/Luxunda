
"""
AI-Powered Genotype Generator for LuxDB
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class GenotypeSuggestion:
    """Suggestion for genotype structure"""
    genotype: Dict[str, Any]
    explanation: str
    use_cases: List[str]
    complexity_score: int  # 1-10


class AIGenotypGenerator:
    """
    AI-powered generator for LuxDB genotypes
    Helps users create proper genotype structures
    """
    
    def __init__(self):
        self.common_patterns = self._load_common_patterns()
    
    def _load_common_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load common genotype patterns"""
        return {
            "user_profile": {
                "genesis": {
                    "name": "user_profile",
                    "version": "1.0",
                    "description": "Standard user profile with basic information"
                },
                "attributes": {
                    "name": {"py_type": "str", "max_length": 100},
                    "email": {"py_type": "str", "unique": True},
                    "age": {"py_type": "int", "min_value": 0, "max_value": 150},
                    "bio": {"py_type": "str", "nullable": True},
                    "preferences": {"py_type": "dict"},
                    "active": {"py_type": "bool", "default": True}
                }
            },
            "product": {
                "genesis": {
                    "name": "product",
                    "version": "1.0",
                    "description": "E-commerce product with pricing and inventory"
                },
                "attributes": {
                    "name": {"py_type": "str", "max_length": 200},
                    "description": {"py_type": "str"},
                    "price": {"py_type": "float", "min_value": 0},
                    "currency": {"py_type": "str", "max_length": 3, "default": "USD"},
                    "stock_quantity": {"py_type": "int", "min_value": 0},
                    "categories": {"py_type": "List[str]"},
                    "metadata": {"py_type": "dict"},
                    "is_available": {"py_type": "bool", "default": True}
                }
            },
            "article": {
                "genesis": {
                    "name": "article",
                    "version": "1.0",
                    "description": "Article with content and SEO metadata"
                },
                "attributes": {
                    "title": {"py_type": "str", "max_length": 200},
                    "content": {"py_type": "str"},
                    "author": {"py_type": "str"},
                    "tags": {"py_type": "List[str]"},
                    "published_at": {"py_type": "str"},
                    "view_count": {"py_type": "int", "default": 0},
                    "meta_description": {"py_type": "str", "max_length": 160},
                    "featured_image": {"py_type": "str", "nullable": True}
                }
            },
            "ai_document": {
                "genesis": {
                    "name": "ai_document",
                    "version": "1.0", 
                    "description": "Document with AI embeddings for semantic search"
                },
                "attributes": {
                    "title": {"py_type": "str", "max_length": 200},
                    "content": {"py_type": "str"},
                    "summary": {"py_type": "str", "nullable": True},
                    "source": {"py_type": "str"},
                    "embedding": {"py_type": "List[float]", "vector_size": 1536},
                    "tags": {"py_type": "List[str]"},
                    "processed_at": {"py_type": "str"}
                }
            },
            "iot_device": {
                "genesis": {
                    "name": "iot_device",
                    "version": "1.0",
                    "description": "IoT device with sensor data and configuration"
                },
                "attributes": {
                    "device_id": {"py_type": "str", "unique": True},
                    "device_type": {"py_type": "str"},
                    "location": {"py_type": "str"},
                    "sensor_data": {"py_type": "dict"},
                    "last_reading": {"py_type": "str"},
                    "battery_level": {"py_type": "float", "min_value": 0, "max_value": 100},
                    "is_online": {"py_type": "bool", "default": False},
                    "configuration": {"py_type": "dict"}
                }
            }
        }
    
    def suggest_genotype(self, description: str, domain: str = None) -> List[GenotypeSuggestion]:
        """
        Generate genotype suggestions based on description
        """
        suggestions = []
        
        # Match against common patterns
        for pattern_name, pattern in self.common_patterns.items():
            if self._matches_description(description, pattern_name, pattern):
                suggestions.append(GenotypeSuggestion(
                    genotype=pattern,
                    explanation=f"Based on '{pattern_name}' pattern: {pattern['genesis']['description']}",
                    use_cases=[f"{pattern_name} management", "data modeling", "content management"],
                    complexity_score=self._calculate_complexity(pattern)
                ))
        
        # Generate custom suggestions based on keywords
        custom_genotype = self._generate_custom_genotype(description, domain)
        if custom_genotype:
            suggestions.append(GenotypeSuggestion(
                genotype=custom_genotype,
                explanation="Custom genotype generated based on your description",
                use_cases=["custom application", "specific domain modeling"],
                complexity_score=self._calculate_complexity(custom_genotype)
            ))
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def _matches_description(self, description: str, pattern_name: str, pattern: Dict[str, Any]) -> bool:
        """Check if description matches a pattern"""
        description_lower = description.lower()
        pattern_keywords = {
            "user_profile": ["user", "profile", "person", "account", "member"],
            "product": ["product", "item", "goods", "merchandise", "catalog"],
            "article": ["article", "blog", "post", "content", "news"],
            "ai_document": ["document", "ai", "embedding", "semantic", "search"],
            "iot_device": ["device", "sensor", "iot", "hardware", "telemetry"]
        }
        
        keywords = pattern_keywords.get(pattern_name, [])
        return any(keyword in description_lower for keyword in keywords)
    
    def _generate_custom_genotype(self, description: str, domain: str = None) -> Optional[Dict[str, Any]]:
        """Generate custom genotype based on description analysis"""
        # Simple keyword-based generation
        # In a real implementation, this would use AI/ML models
        
        attributes = {}
        
        # Common attributes based on keywords
        keywords_to_attributes = {
            "name": {"py_type": "str", "max_length": 100},
            "title": {"py_type": "str", "max_length": 200},
            "description": {"py_type": "str"},
            "email": {"py_type": "str", "unique": True},
            "phone": {"py_type": "str"},
            "address": {"py_type": "str"},
            "price": {"py_type": "float", "min_value": 0},
            "quantity": {"py_type": "int", "min_value": 0},
            "date": {"py_type": "str"},
            "active": {"py_type": "bool", "default": True},
            "tags": {"py_type": "List[str]"},
            "metadata": {"py_type": "dict"}
        }
        
        description_lower = description.lower()
        for keyword, attr_def in keywords_to_attributes.items():
            if keyword in description_lower:
                attributes[keyword] = attr_def
        
        if not attributes:
            return None
        
        return {
            "genesis": {
                "name": "custom_entity",
                "version": "1.0",
                "description": f"Custom entity based on: {description}"
            },
            "attributes": attributes
        }
    
    def _calculate_complexity(self, genotype: Dict[str, Any]) -> int:
        """Calculate complexity score (1-10)"""
        attributes = genotype.get("attributes", {})
        
        base_score = min(len(attributes), 5)  # 1-5 based on attribute count
        
        # Add complexity for special types
        for attr_name, attr_def in attributes.items():
            py_type = attr_def.get("py_type", "str")
            if py_type.startswith("List["):
                base_score += 1
            elif py_type == "dict":
                base_score += 1
            elif "vector_size" in attr_def:
                base_score += 2
        
        return min(base_score, 10)
    
    def generate_genotype_variations(self, base_genotype: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate variations of existing genotype"""
        variations = []
        
        # Add AI features variation
        ai_variation = self._add_ai_features(base_genotype)
        if ai_variation:
            variations.append(ai_variation)
        
        # Add metadata variation
        metadata_variation = self._add_metadata_features(base_genotype)
        if metadata_variation:
            variations.append(metadata_variation)
        
        # Add temporal variation
        temporal_variation = self._add_temporal_features(base_genotype)
        if temporal_variation:
            variations.append(temporal_variation)
        
        return variations
    
    def _add_ai_features(self, genotype: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add AI/ML features to genotype"""
        import copy
        variation = copy.deepcopy(genotype)
        
        attributes = variation.get("attributes", {})
        
        # Add embedding for text fields
        has_text = any(attr.get("py_type") == "str" for attr in attributes.values())
        if has_text:
            attributes["embedding"] = {
                "py_type": "List[float]", 
                "vector_size": 1536,
                "description": "AI embedding for semantic search"
            }
            
            variation["genesis"]["description"] += " (with AI embeddings)"
            return variation
        
        return None
    
    def _add_metadata_features(self, genotype: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add metadata tracking features"""
        import copy
        variation = copy.deepcopy(genotype)
        
        attributes = variation.get("attributes", {})
        
        # Add common metadata fields
        metadata_fields = {
            "created_by": {"py_type": "str", "nullable": True},
            "updated_by": {"py_type": "str", "nullable": True},
            "version": {"py_type": "int", "default": 1},
            "status": {"py_type": "str", "default": "active"},
            "metadata": {"py_type": "dict", "default": {}}
        }
        
        for field_name, field_def in metadata_fields.items():
            if field_name not in attributes:
                attributes[field_name] = field_def
        
        variation["genesis"]["description"] += " (with metadata tracking)"
        return variation
    
    def _add_temporal_features(self, genotype: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add temporal/audit features"""
        import copy
        variation = copy.deepcopy(genotype)
        
        attributes = variation.get("attributes", {})
        
        # Add temporal fields
        temporal_fields = {
            "valid_from": {"py_type": "str", "nullable": True},
            "valid_to": {"py_type": "str", "nullable": True},
            "audit_log": {"py_type": "List[dict]", "default": []},
            "last_modified": {"py_type": "str", "nullable": True}
        }
        
        for field_name, field_def in temporal_fields.items():
            if field_name not in attributes:
                attributes[field_name] = field_def
        
        variation["genesis"]["description"] += " (with temporal features)"
        return variation
    
    def validate_genotype(self, genotype: Dict[str, Any]) -> List[str]:
        """Validate genotype structure and return warnings/errors"""
        warnings = []
        
        # Check required structure
        if "genesis" not in genotype:
            warnings.append("Missing 'genesis' section")
        elif "name" not in genotype["genesis"]:
            warnings.append("Missing 'name' in genesis")
        
        if "attributes" not in genotype:
            warnings.append("Missing 'attributes' section")
        else:
            attributes = genotype["attributes"]
            
            # Check for empty attributes
            if not attributes:
                warnings.append("No attributes defined")
            
            # Validate attribute definitions
            for attr_name, attr_def in attributes.items():
                if not isinstance(attr_def, dict):
                    warnings.append(f"Attribute '{attr_name}' should be a dictionary")
                    continue
                
                if "py_type" not in attr_def:
                    warnings.append(f"Attribute '{attr_name}' missing py_type")
                
                # Check for potential issues
                py_type = attr_def.get("py_type", "")
                if py_type == "str" and "max_length" not in attr_def:
                    warnings.append(f"String attribute '{attr_name}' should have max_length")
                
                if py_type == "float" and attr_def.get("min_value") is None:
                    warnings.append(f"Float attribute '{attr_name}' should consider min_value")
        
        return warnings


def export_genotype_to_file(genotype: Dict[str, Any], filename: str):
    """Export genotype to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(genotype, f, indent=2, ensure_ascii=False)


def load_genotype_from_file(filename: str) -> Dict[str, Any]:
    """Load genotype from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)
