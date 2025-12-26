from decimal import Decimal
from pydantic import BaseModel


class SummaryReport(BaseModel):
    total_sales: Decimal
    total_purchases: Decimal
    gross_margin: Decimal


class GroupReport(BaseModel):
    name: str
    total: Decimal


class TopProductReport(BaseModel):
    product_id: str
    name: str
    total: Decimal
