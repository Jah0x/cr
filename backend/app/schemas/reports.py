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


class TaxReportItem(BaseModel):
    rule_id: str
    name: str
    rate: Decimal
    total_tax: Decimal
    by_method: dict[str, Decimal]


class FinanceOverviewReport(BaseModel):
    total_revenue: Decimal
    gross_profit: Decimal
    total_taxes: Decimal
    revenue_by_method: dict[str, Decimal]
    taxes_by_method: dict[str, Decimal]


class TopProductPerformanceReport(BaseModel):
    product_id: str
    name: str
    qty: Decimal
    revenue: Decimal
    margin: Decimal


class InventoryValuationItem(BaseModel):
    product_id: str
    name: str
    qty_on_hand: Decimal
    unit_cost: Decimal
    total_value: Decimal


class InventoryValuationReport(BaseModel):
    total_value: Decimal
    items: list[InventoryValuationItem]
