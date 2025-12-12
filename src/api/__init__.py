"""
API Module
FastAPI routers and endpoints
"""

from .v1 import cameras, detection, zones

__all__ = ["cameras", "detection", "zones"]
