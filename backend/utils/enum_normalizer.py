"""
Universal Enum Normalizer

Provides intelligent normalization for all enum types in the system to handle
variations detected by AI and prevent database errors.
"""

import logging
from typing import Dict, Set, Optional

logger = logging.getLogger(__name__)


class EnumNormalizer:
    """Universal normalizer for all enum types."""
    
    # Material Category Synonyms
    MATERIAL_CATEGORY_SYNONYMS = {
        # Cabinetry variations
        "cabinet": "cabinetry",
        "cabinets": "cabinetry",
        "cabinet_work": "cabinetry",
        "cupboard": "cabinetry",
        "cupboards": "cabinetry",
        
        # Flooring variations
        "floor": "flooring",
        "floors": "flooring",
        "floor_covering": "flooring",
        
        # Wall variations
        "walls": "wall",
        "wall_covering": "wall",
        "wallpaper": "wall",
        "paint": "wall",
        
        # Ceiling variations
        "ceilings": "ceiling",
        
        # Countertop variations
        "counter": "countertop",
        "counters": "countertop",
        "counter_top": "countertop",
        "worktop": "countertop",
        
        # Backsplash variations
        "back_splash": "backsplash",
        "tile_backsplash": "backsplash",
        
        # Trim variations
        "molding": "trim",
        "moulding": "trim",
        "baseboard": "trim",
        "baseboards": "trim",
        "crown_molding": "trim",
        
        # Door variations
        "doors": "door",
        "doorway": "door",
        
        # Window variations
        "windows": "window",
        "window_frame": "window",
    }
    
    # Fixture Type Synonyms
    FIXTURE_TYPE_SYNONYMS = {
        # Lighting variations
        "lights": "lighting",
        "light_fixture": "lighting",
        "light_fixtures": "lighting",
        "lamp": "lighting",
        "chandelier": "lighting",
        "pendant": "lighting",
        "sconce": "lighting",
        
        # Faucet variations
        "faucets": "faucet",
        "tap": "faucet",
        "taps": "faucet",
        "sink_faucet": "faucet",
        
        # Sink variations
        "sinks": "sink",
        "basin": "sink",
        "wash_basin": "sink",
        
        # Toilet variations
        "toilets": "toilet",
        "wc": "toilet",
        "commode": "toilet",
        
        # Shower variations
        "showers": "shower",
        "shower_head": "shower",
        "shower_fixture": "shower",
        
        # Bathtub variations
        "tub": "bathtub",
        "bath": "bathtub",
        "bathtubs": "bathtub",
        
        # Appliance variations
        "appliances": "appliance",
        "kitchen_appliance": "appliance",
        
        # Hardware variations
        "door_hardware": "hardware",
        "cabinet_hardware": "hardware",
        "handles": "hardware",
        "knobs": "hardware",
        "pulls": "hardware",
    }
    
    def __init__(self):
        """Initialize the normalizer with tracking."""
        self.unknown_materials: Set[str] = set()
        self.unknown_fixtures: Set[str] = set()
        self.unknown_room_types: Set[str] = set()
    
    def normalize_material_category(self, category: str) -> str:
        """
        Normalize a material category string.
        
        Args:
            category: Raw material category string
            
        Returns:
            Normalized category that matches MaterialCategory enum
        """
        if not category:
            return "other"
        
        # Clean the string
        cleaned = self._clean_string(category)
        
        # Valid enum values
        valid_values = {
            "flooring", "wall", "ceiling", "countertop", "backsplash",
            "cabinetry", "trim", "door", "window", "other"
        }
        
        # Check if already valid
        if cleaned in valid_values:
            return cleaned
        
        # Check synonyms
        if cleaned in self.MATERIAL_CATEGORY_SYNONYMS:
            result = self.MATERIAL_CATEGORY_SYNONYMS[cleaned]
            logger.info(f"Normalized material category: '{category}' -> '{result}' via synonym")
            return result
        
        # Partial matching
        for key, value in self.MATERIAL_CATEGORY_SYNONYMS.items():
            if key in cleaned or cleaned in key:
                logger.info(f"Normalized material category: '{category}' -> '{value}' via partial match")
                return value
        
        # Check if it contains any valid value
        for valid in valid_values:
            if valid in cleaned or cleaned in valid:
                logger.info(f"Normalized material category: '{category}' -> '{valid}' via substring match")
                return valid
        
        # Unknown - track and fallback
        self.unknown_materials.add(category)
        logger.warning(f"Unknown material category: '{category}'. Defaulting to 'other'.")
        return "other"
    
    def normalize_fixture_type(self, fixture_type: str) -> str:
        """
        Normalize a fixture type string.
        
        Args:
            fixture_type: Raw fixture type string
            
        Returns:
            Normalized type that matches FixtureType enum
        """
        if not fixture_type:
            return "other"
        
        # Clean the string
        cleaned = self._clean_string(fixture_type)
        
        # Valid enum values
        valid_values = {
            "lighting", "faucet", "sink", "toilet", "shower", "bathtub",
            "appliance", "hardware", "hvac", "electrical", "plumbing", "other"
        }
        
        # Check if already valid
        if cleaned in valid_values:
            return cleaned
        
        # Check synonyms
        if cleaned in self.FIXTURE_TYPE_SYNONYMS:
            result = self.FIXTURE_TYPE_SYNONYMS[cleaned]
            logger.info(f"Normalized fixture type: '{fixture_type}' -> '{result}' via synonym")
            return result
        
        # Partial matching
        for key, value in self.FIXTURE_TYPE_SYNONYMS.items():
            if key in cleaned or cleaned in key:
                logger.info(f"Normalized fixture type: '{fixture_type}' -> '{value}' via partial match")
                return value
        
        # Check if it contains any valid value
        for valid in valid_values:
            if valid in cleaned or cleaned in valid:
                logger.info(f"Normalized fixture type: '{fixture_type}' -> '{valid}' via substring match")
                return valid
        
        # Unknown - track and fallback
        self.unknown_fixtures.add(fixture_type)
        logger.warning(f"Unknown fixture type: '{fixture_type}'. Defaulting to 'other'.")
        return "other"
    
    def _clean_string(self, value: str) -> str:
        """Clean and normalize a string value."""
        if not value:
            return ""
        
        # Convert to lowercase
        cleaned = value.lower().strip()
        
        # Replace spaces and hyphens with underscores
        cleaned = cleaned.replace(" ", "_").replace("-", "_")
        
        # Remove multiple underscores
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        
        # Remove leading/trailing underscores
        cleaned = cleaned.strip("_")
        
        return cleaned
    
    def get_unknown_materials(self) -> Set[str]:
        """Get all unknown material categories encountered."""
        return self.unknown_materials.copy()
    
    def get_unknown_fixtures(self) -> Set[str]:
        """Get all unknown fixture types encountered."""
        return self.unknown_fixtures.copy()
    
    def add_material_synonym(self, synonym: str, target: str):
        """Add a new material category synonym at runtime."""
        cleaned_synonym = self._clean_string(synonym)
        self.MATERIAL_CATEGORY_SYNONYMS[cleaned_synonym] = target
        logger.info(f"Added material category synonym: '{synonym}' -> '{target}'")
    
    def add_fixture_synonym(self, synonym: str, target: str):
        """Add a new fixture type synonym at runtime."""
        cleaned_synonym = self._clean_string(synonym)
        self.FIXTURE_TYPE_SYNONYMS[cleaned_synonym] = target
        logger.info(f"Added fixture type synonym: '{synonym}' -> '{target}'")


# Global normalizer instance
_normalizer = EnumNormalizer()


# Convenience functions for material categories
def normalize_material_category(category: str) -> str:
    """Normalize a material category string."""
    return _normalizer.normalize_material_category(category)


def get_unknown_materials() -> Set[str]:
    """Get all unknown material categories."""
    return _normalizer.get_unknown_materials()


def add_material_synonym(synonym: str, target: str):
    """Add a material category synonym."""
    _normalizer.add_material_synonym(synonym, target)


# Convenience functions for fixture types
def normalize_fixture_type(fixture_type: str) -> str:
    """Normalize a fixture type string."""
    return _normalizer.normalize_fixture_type(fixture_type)


def get_unknown_fixtures() -> Set[str]:
    """Get all unknown fixture types."""
    return _normalizer.get_unknown_fixtures()


def add_fixture_synonym(synonym: str, target: str):
    """Add a fixture type synonym."""
    _normalizer.add_fixture_synonym(synonym, target)

