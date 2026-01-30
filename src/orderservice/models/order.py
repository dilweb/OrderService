from pydantic import BaseModel, Field

class Base(BaseModel):
    pass

class OrderCreate(BaseModel):
    order_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    item: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0)

class OrderAccepted(Base):
    order_id: str
    status: str = "accepted"