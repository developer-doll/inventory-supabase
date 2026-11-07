from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

RoleName = Literal["superadmin", "inventory_manager", "sales_person"]

class LoginIn(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8)
    role: RoleName

class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    price: float = Field(ge=0)
    opening_stock: int = Field(default=0, ge=0)

class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, ge=0)

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    name: str
    description: str | None
    price: float
    stock_quantity: int
    is_active: bool

class StockChange(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=255)

class OrderLineIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)

class OrderCreate(BaseModel):
    items: list[OrderLineIn] = Field(min_length=1)
    tax_percent: float = Field(default=0, ge=0, le=100)
    payment_method: Literal["cash", "upi", "card", "credit"] = "cash"

class OrderItemOut(BaseModel):
    product_id: int
    product_name: str
    sku: str
    quantity: int
    unit_price: float
    line_total: float

class OrderOut(BaseModel):
    id: int
    invoice_number: str
    created_by: int
    status: str
    subtotal: float
    tax_amount: float
    total_amount: float
    payment_method: str
    created_at: str
    items: list[OrderItemOut]
