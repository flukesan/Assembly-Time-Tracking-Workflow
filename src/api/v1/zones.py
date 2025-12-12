"""
Zone Management API
Endpoints for zone CRUD operations
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Tuple
from pydantic import BaseModel

from ...core.zones.zone_models import Zone, ZoneType

router = APIRouter(prefix="/api/v1/zones", tags=["zones"])

# Global zone manager (will be injected during startup)
zone_manager = None


def set_zone_manager(manager):
    """Set global zone manager instance"""
    global zone_manager
    zone_manager = manager


class ZoneCreateRequest(BaseModel):
    """Request model for creating a zone"""
    camera_id: int
    name: str
    zone_type: ZoneType
    polygon_coords: List[Tuple[int, int]]
    color: str = "#00FF00"
    active: bool = True


class ZoneUpdateRequest(BaseModel):
    """Request model for updating a zone"""
    name: str = None
    zone_type: ZoneType = None
    polygon_coords: List[Tuple[int, int]] = None
    color: str = None
    active: bool = None


@router.get("/", response_model=List[Zone])
async def list_zones():
    """Get all zones"""
    if zone_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zone manager not initialized"
        )

    return zone_manager.get_all_zones()


@router.get("/{zone_id}", response_model=Zone)
async def get_zone(zone_id: int):
    """Get zone by ID"""
    if zone_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zone manager not initialized"
        )

    zone = zone_manager.get_zone(zone_id)
    if zone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone {zone_id} not found"
        )

    return zone


@router.get("/camera/{camera_id}", response_model=List[Zone])
async def get_zones_by_camera(camera_id: int):
    """Get all zones for a specific camera"""
    if zone_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zone manager not initialized"
        )

    return zone_manager.get_zones_by_camera(camera_id)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_zone(request: ZoneCreateRequest):
    """Create a new zone"""
    if zone_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zone manager not initialized"
        )

    # Generate new zone_id (simple increment for now)
    existing_zones = zone_manager.get_all_zones()
    new_zone_id = max([z.zone_id for z in existing_zones], default=0) + 1

    # Create zone
    zone = Zone(
        zone_id=new_zone_id,
        camera_id=request.camera_id,
        name=request.name,
        zone_type=request.zone_type,
        polygon_coords=request.polygon_coords,
        color=request.color,
        active=request.active
    )

    success = zone_manager.add_zone(zone)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create zone"
        )

    return {
        "message": "Zone created successfully",
        "zone_id": new_zone_id
    }


@router.put("/{zone_id}")
async def update_zone(zone_id: int, request: ZoneUpdateRequest):
    """Update an existing zone"""
    if zone_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zone manager not initialized"
        )

    # Get existing zone
    existing_zone = zone_manager.get_zone(zone_id)
    if existing_zone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone {zone_id} not found"
        )

    # Update fields
    update_data = request.dict(exclude_unset=True)
    updated_zone = existing_zone.copy(update=update_data)

    success = zone_manager.update_zone(updated_zone)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update zone"
        )

    return {
        "message": "Zone updated successfully",
        "zone_id": zone_id
    }


@router.delete("/{zone_id}")
async def delete_zone(zone_id: int):
    """Delete a zone"""
    if zone_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zone manager not initialized"
        )

    success = zone_manager.remove_zone(zone_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone {zone_id} not found"
        )

    return {
        "message": "Zone deleted successfully",
        "zone_id": zone_id
    }


@router.post("/{zone_id}/activate")
async def activate_zone(zone_id: int):
    """Activate a zone"""
    if zone_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zone manager not initialized"
        )

    success = zone_manager.activate_zone(zone_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone {zone_id} not found"
        )

    return {
        "message": "Zone activated",
        "zone_id": zone_id
    }


@router.post("/{zone_id}/deactivate")
async def deactivate_zone(zone_id: int):
    """Deactivate a zone"""
    if zone_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Zone manager not initialized"
        )

    success = zone_manager.deactivate_zone(zone_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone {zone_id} not found"
        )

    return {
        "message": "Zone deactivated",
        "zone_id": zone_id
    }
