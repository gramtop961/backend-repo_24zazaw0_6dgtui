"""
Database Schemas for Vistro

Each Pydantic model maps to a MongoDB collection (lowercased class name).
"""
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class ProductVariant(BaseModel):
    size: Optional[str] = Field(None, description="Size label (e.g., S, M, L)")
    color: Optional[str] = Field(None, description="Color name (e.g., Black)")
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    stock: int = Field(0, ge=0, description="Units in stock for this variant")


class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Base price in USD")
    category: str = Field(..., description="Product category, e.g., 'Hoodies'")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    brand: str = Field("Vistro", description="Brand name")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    variants: List[ProductVariant] = Field(default_factory=list, description="Product variants")
    featured: bool = Field(False, description="Is featured on homepage")


class CartItem(BaseModel):
    product_id: str = Field(..., description="Referenced product id as string")
    quantity: int = Field(..., ge=1, description="Quantity ordered")
    size: Optional[str] = Field(None)
    color: Optional[str] = Field(None)


class CustomerInfo(BaseModel):
    name: str
    email: EmailStr
    address: str
    city: str
    country: str
    postal_code: str


class Order(BaseModel):
    items: List[CartItem]
    subtotal: float = Field(..., ge=0)
    shipping: float = Field(..., ge=0)
    total: float = Field(..., ge=0)
    currency: str = Field("USD")
    status: str = Field("pending")
    customer: CustomerInfo
