from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class SummaryReport(BaseModel):
    total_sales: Decimal
    total_purchases: Decimal
    gross_margin: Decimal


class PnlReport(BaseModel):
    total_sales: Decimal
    cogs: Decimal
    gross_profit: Decimal
    expenses_total: Decimal
    net_profit: Decimal
    date_from: datetime | None = None
    date_to: datetime | None = None


class GroupReport(BaseModel):
    name: str
    total: Decimal


class TopProductReport(BaseModel):
    product_id: str
    name: str
    total: Decimal
