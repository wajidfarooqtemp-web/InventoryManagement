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
    image_url: Optional[str] = None  # short-lived signed URL, computed per-request - never stored
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
    # ---------- Periods & activity (Phase 5) ----------

class PeriodOut(BaseModel):
    id: UUID
    year: int
    month: int
    status: str
    is_current: bool  # computed - true if this period matches today's year/month


class PeriodItemSummaryOut(BaseModel):
    period_id: UUID
    item_id: UUID
    item_name: str
    location_name: str
    unit: str
    monthly_requirement: Optional[float] = None
    monthly_requirement_min: Optional[float] = None
    monthly_requirement_max: Optional[float] = None
    opening_stock: float
    received: float
    used: float
    adjustments: float
    transfers_in: float
    transfers_out: float
    closing_stock: float


class MovementOut(BaseModel):
    id: UUID
    item_id: UUID
    item_name: str
    location_name: str
    period_id: UUID
    movement_type: str
    quantity: float
    resulting_stock: float
    reason: Optional[str] = None
    related_transfer_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None  # null for system-generated OPENING_BALANCE rows
    created_at: datetime
    # ---------- Purchase list (Phase 6) ----------

class PurchaseListEntryOut(BaseModel):
    id: UUID
    item_id: UUID
    item_name: str
    location_name: str
    unit: str
    current_stock: float
    monthly_requirement: Optional[float] = None
    monthly_requirement_min: Optional[float] = None
    monthly_requirement_max: Optional[float] = None
    status: str  # needs_purchase / ordered / partially_received / received
    quantity_ordered: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class PurchaseListEntryUpdate(BaseModel):
    status: Optional[str] = None
    quantity_ordered: Optional[float] = None
    # ---------- Overview dashboard (Phase 7) ----------

class NeedsAttentionItemOut(BaseModel):
    item_id: UUID
    item_name: str
    location_name: str
    unit: str
    current_stock: float
    monthly_requirement: Optional[float] = None
    monthly_requirement_min: Optional[float] = None
    monthly_requirement_max: Optional[float] = None
    status: str  # LOW / CRITICAL / OUT_OF_STOCK only - GOOD items never appear here


class OverviewOut(BaseModel):
    total_active_items: int
    total_locations: int
    items_good: int
    items_low: int
    items_critical: int
    items_out_of_stock: int
    items_needs_confirmation: int
    needs_attention: list[NeedsAttentionItemOut]
    recent_activity: list[MovementOut]
    # ---------- Users (Phase 9) ----------

class UserOut(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    active: bool


class UserRoleUpdate(BaseModel):
    role: str  # validated against allowed roles in the router, not here


class UserActiveUpdate(BaseModel):
    active: bool


# ---------- Data confirmation (Phase 9) ----------

class DataConfirmationOut(BaseModel):
    id: UUID
    name: str
    location_name: str
    category_name: str
    unit: str
    monthly_requirement: Optional[float] = None
    monthly_requirement_min: Optional[float] = None
    monthly_requirement_max: Optional[float] = None
    confirmation_note: Optional[str] = None
class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=100)
    role: str = "kitchen_staff"