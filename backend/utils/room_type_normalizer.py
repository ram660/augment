"""
Room Type Normalization Utility

This module provides intelligent room type normalization to handle variations
in room type names detected by AI and prevent enum errors.
"""

import logging
from typing import Optional, Dict, Set
from backend.models.home import RoomType

logger = logging.getLogger(__name__)


class RoomTypeNormalizer:
    """
    Normalizes room type strings to valid RoomType enum values.
    
    Features:
    - Fuzzy matching for common variations
    - Automatic fallback to OTHER for unknown types
    - Learning capability to track new room types
    - Synonym mapping for common variations
    """
    
    # Synonym mapping: maps common variations to standard enum values
    SYNONYMS: Dict[str, str] = {
        # Living spaces
        "living": "living_room",
        "lounge": "living_room",
        "sitting_room": "living_room",
        "sitting": "living_room",
        "great_room": "living_room",
        
        # Dining spaces
        "dining": "dining_room",
        "breakfast_room": "dining_area",
        "breakfast_area": "dining_area",
        "eat_in_kitchen": "dining_area",
        
        # Bedrooms
        "bed": "bedroom",
        "bdrm": "bedroom",
        "br": "bedroom",
        "master": "master_bedroom",
        "master_suite": "master_bedroom",
        "primary_bedroom": "master_bedroom",
        "guest": "guest_room",
        "guest_bedroom": "guest_room",
        
        # Bathrooms
        "bath": "bathroom",
        "full_bath": "bathroom",
        "half_bath": "powder_room",
        "washroom": "bathroom",
        "wc": "powder_room",
        "restroom": "bathroom",
        "ensuite": "bathroom",
        "en_suite": "bathroom",
        
        # Kitchen
        "cook": "kitchen",
        "kitchenette": "kitchen",
        
        # Entry areas
        "entrance": "entryway",
        "vestibule": "foyer",
        "lobby": "foyer",
        
        # Utility spaces
        "laundry": "laundry_room",
        "wash": "laundry_room",
        "mud": "mudroom",
        "util": "utility_room",
        "mech": "mechanical_room",
        "furnace_room": "mechanical_room",
        "boiler_room": "mechanical_room",
        
        # Storage
        "store": "storage",
        "storeroom": "storage_room",
        "walk_in": "walk_in_closet",
        "wardrobe": "closet",
        
        # Recreation
        "rec_room": "family_room",
        "recreation_room": "family_room",
        "tv_room": "media_room",
        "theater": "media_room",
        "theatre": "media_room",
        "home_theater": "media_room",
        "games": "game_room",
        "play": "playroom",
        "kids_room": "playroom",
        
        # Work spaces
        "home_office": "office",
        "workspace": "office",
        "work": "office",
        "reading_room": "library",
        
        # Outdoor
        "terrace": "patio",
        "veranda": "porch",
        "lanai": "porch",
        "outdoor": "patio",
        
        # Other
        "bonus_room": "other",
        "flex_room": "other",
        "multi_purpose": "other",
        "misc": "other",
    }
    
    def __init__(self):
        """Initialize the normalizer."""
        self.unknown_types: Set[str] = set()
        self._valid_types = {e.value for e in RoomType}
        
    def normalize(self, room_type_str: str) -> str:
        """
        Normalize a room type string to a valid RoomType enum value.
        
        Args:
            room_type_str: Raw room type string from AI or user input
            
        Returns:
            Normalized room type string that matches a RoomType enum value
        """
        if not room_type_str:
            logger.warning("Empty room type string provided, defaulting to 'other'")
            return "other"
        
        # Clean the input
        cleaned = self._clean_string(room_type_str)
        
        # Check if it's already a valid enum value
        if cleaned in self._valid_types:
            return cleaned
        
        # Try synonym mapping
        if cleaned in self.SYNONYMS:
            normalized = self.SYNONYMS[cleaned]
            logger.info(f"Normalized room type '{room_type_str}' -> '{normalized}' via synonym")
            return normalized
        
        # Try partial matching
        normalized = self._partial_match(cleaned)
        if normalized:
            logger.info(f"Normalized room type '{room_type_str}' -> '{normalized}' via partial match")
            return normalized
        
        # Track unknown type for learning
        if cleaned not in self.unknown_types:
            self.unknown_types.add(cleaned)
            logger.warning(
                f"Unknown room type detected: '{room_type_str}' (cleaned: '{cleaned}'). "
                f"Defaulting to 'other'. Consider adding to enum or synonyms."
            )
        
        # Fallback to OTHER
        return "other"
    
    def _clean_string(self, s: str) -> str:
        """
        Clean and normalize a string.
        
        Args:
            s: Input string
            
        Returns:
            Cleaned string (lowercase, underscores, trimmed)
        """
        # Convert to lowercase
        s = s.lower().strip()
        
        # Replace common separators with underscores
        s = s.replace(" ", "_").replace("-", "_").replace("/", "_")
        
        # Remove multiple underscores
        while "__" in s:
            s = s.replace("__", "_")
        
        # Remove leading/trailing underscores
        s = s.strip("_")
        
        return s
    
    def _partial_match(self, cleaned: str) -> Optional[str]:
        """
        Try to find a partial match in valid types or synonyms.
        
        Args:
            cleaned: Cleaned room type string
            
        Returns:
            Matched room type or None
        """
        # Check if cleaned string is contained in any valid type
        for valid_type in self._valid_types:
            if cleaned in valid_type or valid_type in cleaned:
                return valid_type
        
        # Check if cleaned string is contained in any synonym key
        for synonym, target in self.SYNONYMS.items():
            if cleaned in synonym or synonym in cleaned:
                return target
        
        # Check for common patterns
        if "bed" in cleaned and "room" in cleaned:
            return "bedroom"
        if "bath" in cleaned:
            return "bathroom"
        if "kitchen" in cleaned or "cook" in cleaned:
            return "kitchen"
        if "living" in cleaned or "lounge" in cleaned:
            return "living_room"
        if "dining" in cleaned or "eat" in cleaned:
            return "dining_room"
        if "office" in cleaned or "study" in cleaned:
            return "office"
        if "closet" in cleaned or "wardrobe" in cleaned:
            return "closet"
        if "hall" in cleaned or "corridor" in cleaned:
            return "hallway"
        if "entry" in cleaned or "entrance" in cleaned or "foyer" in cleaned:
            return "entryway"
        if "garage" in cleaned or "car" in cleaned:
            return "garage"
        if "laundry" in cleaned or "wash" in cleaned:
            return "laundry_room"
        if "storage" in cleaned or "store" in cleaned:
            return "storage"
        if "patio" in cleaned or "deck" in cleaned or "porch" in cleaned:
            return "patio"
        
        return None
    
    def get_unknown_types(self) -> Set[str]:
        """
        Get the set of unknown room types encountered.
        
        Returns:
            Set of unknown room type strings
        """
        return self.unknown_types.copy()
    
    def add_synonym(self, synonym: str, target: str):
        """
        Add a new synonym mapping.
        
        Args:
            synonym: The synonym to add
            target: The target RoomType enum value
        """
        cleaned_synonym = self._clean_string(synonym)
        if target in self._valid_types:
            self.SYNONYMS[cleaned_synonym] = target
            logger.info(f"Added synonym mapping: '{synonym}' -> '{target}'")
        else:
            logger.error(f"Cannot add synonym: '{target}' is not a valid RoomType")


# Global instance
_normalizer = RoomTypeNormalizer()


def normalize_room_type(room_type_str: str) -> str:
    """
    Normalize a room type string to a valid RoomType enum value.
    
    This is a convenience function that uses the global normalizer instance.
    
    Args:
        room_type_str: Raw room type string from AI or user input
        
    Returns:
        Normalized room type string that matches a RoomType enum value
    """
    return _normalizer.normalize(room_type_str)


def get_unknown_room_types() -> Set[str]:
    """
    Get all unknown room types encountered by the normalizer.
    
    Returns:
        Set of unknown room type strings
    """
    return _normalizer.get_unknown_types()


def add_room_type_synonym(synonym: str, target: str):
    """
    Add a new synonym mapping to the global normalizer.
    
    Args:
        synonym: The synonym to add
        target: The target RoomType enum value
    """
    _normalizer.add_synonym(synonym, target)

