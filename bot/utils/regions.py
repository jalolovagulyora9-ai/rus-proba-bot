"""
Helper utility for Uzbekistan regions and districts.
Loads data from data/uzbekistan_regions.json.
"""
import json
from pathlib import Path
from django.conf import settings

_REGIONS_CACHE: dict[str, list[str]] | None = None

def get_regions_data() -> dict[str, list[str]]:
    """Loads and caches the regions and districts dictionary."""
    global _REGIONS_CACHE
    if _REGIONS_CACHE is None:
        file_path = settings.BASE_DIR / 'data' / 'uzbekistan_regions.json'
        with open(file_path, 'r', encoding='utf-8') as f:
            _REGIONS_CACHE = json.load(f)
    return _REGIONS_CACHE

def get_region_list() -> list[str]:
    """Returns list of region names."""
    return list(get_regions_data().keys())

def get_region_by_index(index: int) -> str | None:
    """Returns region name by its 0-based index."""
    regions = get_region_list()
    if 0 <= index < len(regions):
        return regions[index]
    return None

def get_region_index(region_name: str) -> int | None:
    """Returns index of given region name."""
    regions = get_region_list()
    try:
        return regions.index(region_name)
    except ValueError:
        return None

def get_districts_by_region(region_name: str) -> list[str]:
    """Returns list of districts for the given region."""
    data = get_regions_data()
    return data.get(region_name, [])

def get_district_by_index(region_name: str, index: int) -> str | None:
    """Returns district name by its index within the region."""
    districts = get_districts_by_region(region_name)
    if 0 <= index < len(districts):
        return districts[index]
    return None
