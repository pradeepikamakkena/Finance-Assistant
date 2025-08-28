from pydantic import BaseModel
import datetime
from typing import List, Optional

class User(BaseModel):
    id: int
    email: str
    is_admin: bool

    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    item_name: str
    quantity: int
    rate: float
    subtotal: float

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    receipt_id: int

    class Config:
        from_attributes = True

class ReceiptBase(BaseModel):
    seller_name: str
    category: str
    receipt_date: datetime.datetime
    total_amount: float
    tax_amount: Optional[float] = None

class ReceiptCreate(ReceiptBase):
    items: List[ItemCreate]

class Receipt(ReceiptBase):
    id: int
    owner_id: int
    upload_date: datetime.datetime
    items: List[Item] = []
    owner: User 

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

User.model_rebuild()

class ChartData(BaseModel):
    label: str
    value: float

class KPIData(BaseModel):
    total_spend: float
    total_tax: float
    total_bills: int

class TimeSeriesData(BaseModel):
    label: str
    value: float