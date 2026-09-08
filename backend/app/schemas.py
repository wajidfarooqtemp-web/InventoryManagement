"""
Request/response shapes, kept separate from routers so routers stay
focused on "what happens" rather than "what shape is the data".
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# ---------- Locations ----------

class LocationOut(BaseModel):
    id: UUID
    name: str
    active: bool

class LocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class LocationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    active: Optional[bool] = None


# ---------- Categories ----------

class CategoryOut(BaseModel):
    id: UUID
    name: str
    active: bool

class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    active: Optional[bool] = None


# ---------- Inventory items ----------

class InventoryItemOut(BaseModel):
    id: UUID
    name: str
    location_id: UUID
    location_name: str
    category_id: UUID
    category_name: str
    image_path: Optional[str] = None
    unit: str
    package_size: Optional[float] = None
    package_unit: Optional[str] = None
    package_count: Optional[float] = None
    monthly_requirement: Optional[float] = None
    monthly_requirement_min: Optional[float] = None
    monthly_requirement_max: Optional[float] = None
    requirement_is_estimate: bool
    current_stock: float
    minimum_stock: Optional[float] = None
    reorder_level: Optional[float] = None
    critical_level: Optional[float] = None
    active: bool
    needs_confirmation: bool
    confirmation_note: Optional[str] = None
    notes: Optional[str] = None
    status: str  # computed - GOOD / LOW / CRITICAL / OUT_OF_STOCK, never stored
    updated_at: datetime


class InventoryItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    location_id: UUID
    category_id: UUID
    unit: str = Field(min_length=1, max_length=30)
    package_size: Optional[float] = None
    package_unit: Optional[str] = None
    package_count: Optional[float] = None
    monthly_requirement: Optional[float] = None
    monthly_requirement_min: Optional[float] = None
    monthly_requirement_max: Optional[float] = None
    requirement_is_estimate: bool = False
    minimum_stock: Optional[float] = None
    reorder_level: Optional[float] = None
    critical_level: Optional[float] = None
    needs_confirmation: bool = False
    confirmation_note: Optional[str] = None
    notes: Optional[str] = None


class InventoryItemUpdate(BaseModel):
    """
    Every field optional - PATCH only changes what's provided.
    Deliberately has NO current_stock field: metadata edits can never
    change stock. Stock only ever changes through a movement (Phase 4).
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    location_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    unit: Optional[str] = Field(default=None, min_length=1, max_length=30)
    package_size: Optional[float] = None
    package_unit: Optional[str] = None
    package_count: Optional[float] = None
    monthly_requirement: Optional[float] = None
    monthly_requirement_min: Optional[float] = None
    monthly_requirement_max: Optional[float] = None
    requirement_is_estimate: Optional[bool] = None
    minimum_stock: Optional[float] = None
    reorder_level: Optional[float] = None
    critical_level: Optional[float] = None
    needs_confirmation: Optional[bool] = None
    confirmation_note: Optional[str] = None
    notes: Optional[str] = None