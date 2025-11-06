"""Utility modules for HomeVision AI."""

from backend.utils.room_type_normalizer import (
    normalize_room_type,
    get_unknown_room_types,
    add_room_type_synonym,
    RoomTypeNormalizer
)

__all__ = [
    "normalize_room_type",
    "get_unknown_room_types",
    "add_room_type_synonym",
    "RoomTypeNormalizer"
]

