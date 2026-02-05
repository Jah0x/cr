import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class RecurringExpensePeriod(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class RecurringExpenseAllocationMethod(str, enum.Enum):
    calendar_days = "calendar_days"
    fixed_30 = "fixed_30"


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    expenses = relationship("Expense", back_populates="category")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("expense_categories.id", ondelete="SET NULL")
    )
    note = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    store_id = Column(
        UUID(as_uuid=True), ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False
    )

    category = relationship("ExpenseCategory", back_populates="expenses")
    store = relationship("Store", back_populates="expenses")


class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(
        UUID(as_uuid=True), ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False
    )
    name = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    period = Column(Enum(RecurringExpensePeriod), nullable=False)
    allocation_method = Column(
        Enum(RecurringExpenseAllocationMethod),
        nullable=False,
        default=RecurringExpenseAllocationMethod.calendar_days,
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    store = relationship("Store")
    accruals = relationship("ExpenseAccrual", back_populates="recurring_expense")


class ExpenseAccrual(Base):
    __tablename__ = "expense_accruals"
    __table_args__ = (
        UniqueConstraint(
            "recurring_expense_id", "date", name="uq_expense_accruals_recurring_expense_id_date"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(
        UUID(as_uuid=True), ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False
    )
    recurring_expense_id = Column(
        UUID(as_uuid=True), ForeignKey("recurring_expenses.id", ondelete="CASCADE"), nullable=False
    )
    date = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    store = relationship("Store")
    recurring_expense = relationship("RecurringExpense", back_populates="accruals")
