import csv
import io
import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Brand, Category, Product, ProductLine, ProductUnit
from app.repos.imports_repo import ImportsRepo
from app.schemas.imports import ImportCounters


class ImportService:
    def __init__(self, session: AsyncSession, imports_repo: ImportsRepo):
        self.session = session
        self.imports_repo = imports_repo

    def parse_file(self, file_bytes: bytes, sheet: str | None = None, encoding: str | None = None, delimiter: str | None = None):
        del sheet
        text = file_bytes.decode(encoding or "utf-8")
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter or ",")
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append({str(k): (v.strip() if isinstance(v, str) else v) for k, v in row.items()})
        return {
            "columns": list(reader.fieldnames or []),
            "rows": rows,
            "sample_rows": rows[:20],
        }

    @staticmethod
    def _parse_decimal(value: object, decimal_separator: str = ".", thousand_separator: str = ",") -> Decimal | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        cleaned = text.replace(thousand_separator, "") if thousand_separator else text
        cleaned = cleaned.replace(decimal_separator, ".") if decimal_separator and decimal_separator != "." else cleaned
        return Decimal(cleaned)

    async def _lookup_ids(self):
        categories = {
            row.name.strip().lower(): row.id
            for row in (await self.session.execute(select(Category.id, Category.name))).all()
        }
        brands = {
            row.name.strip().lower(): row.id
            for row in (await self.session.execute(select(Brand.id, Brand.name))).all()
        }
        lines = {
            row.name.strip().lower(): row.id
            for row in (await self.session.execute(select(ProductLine.id, ProductLine.name))).all()
        }
        return categories, brands, lines

    async def preview_import(self, job_id: uuid.UUID, mapping: dict[str, str], options: dict):
        job = await self.imports_repo.get_import(job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found")

        if "name" not in mapping or not mapping["name"]:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Mapping for 'name' is required")

        decimal_separator = str(options.get("decimal_separator", "."))
        thousand_separator = str(options.get("thousand_separator", ","))

        categories, brands, lines = await self._lookup_ids()
        errors: list[dict[str, str]] = []
        sample_actions: list[dict[str, str | int]] = []
        valid_count = 0
        invalid_count = 0

        for idx, row in enumerate(job.source_rows, start=2):
            row_errors: list[str] = []
            name = str(row.get(mapping["name"], "")).strip()
            if not name:
                row_errors.append("name is required")

            for numeric_field in ("cost_price", "sell_price", "tax_rate"):
                source_column = mapping.get(numeric_field)
                if not source_column:
                    continue
                raw = row.get(source_column)
                if raw in (None, ""):
                    continue
                try:
                    self._parse_decimal(raw, decimal_separator, thousand_separator)
                except Exception:
                    row_errors.append(f"invalid number in {numeric_field}: {raw}")

            category_col = mapping.get("category")
            if category_col:
                category_name = str(row.get(category_col, "")).strip().lower()
                if category_name and category_name not in categories:
                    row_errors.append(f"unknown category: {row.get(category_col)}")

            brand_col = mapping.get("brand")
            if brand_col:
                brand_name = str(row.get(brand_col, "")).strip().lower()
                if brand_name and brand_name not in brands:
                    row_errors.append(f"unknown brand: {row.get(brand_col)}")

            line_col = mapping.get("line")
            if line_col:
                line_name = str(row.get(line_col, "")).strip().lower()
                if line_name and line_name not in lines:
                    row_errors.append(f"unknown line: {row.get(line_col)}")

            if row_errors:
                invalid_count += 1
                errors.append({"row": str(idx), "error": "; ".join(row_errors)})
                sample_actions.append({"row": idx, "action": "error", "reason": "; ".join(row_errors)})
            else:
                valid_count += 1
                sample_actions.append({"row": idx, "action": "create", "reason": None})

        job.mapping = mapping
        job.options = options
        job.rows_total = len(job.source_rows)
        job.rows_valid = valid_count
        job.rows_invalid = invalid_count
        job.errors = errors
        await self.session.flush()

        return {
            "mapping": mapping,
            "options": options,
            "rows": job.source_rows[:50],
            "summary": {
                "rows": job.rows_total,
                "valid": valid_count,
                "invalid": invalid_count,
                "would_create": valid_count,
                "would_update": 0,
                "would_skip": 0,
            },
            "sample_actions": sample_actions[:50],
        }

    async def perform_import(self, import_id: uuid.UUID, mapping: dict[str, str], options: dict):
        job = await self.imports_repo.get_import(import_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found")

        await self.imports_repo.update_status(import_id, "running")
        categories, brands, lines = await self._lookup_ids()

        match_by = options.get("match_by") or "sku"
        counters = ImportCounters(total=len(job.source_rows)).model_dump()
        errors: list[dict[str, str]] = []

        for idx, row in enumerate(job.source_rows, start=2):
            name_col = mapping.get("name")
            name = str(row.get(name_col, "")).strip() if name_col else ""
            if not name:
                counters["failed"] += 1
                errors.append({"row": str(idx), "error": "name is required"})
                continue

            sku_col = mapping.get("sku")
            sku = str(row.get(sku_col, "")).strip() if sku_col else None
            barcode_col = mapping.get("barcode")
            barcode = str(row.get(barcode_col, "")).strip() if barcode_col else None

            category_id = None
            if mapping.get("category"):
                category_name = str(row.get(mapping["category"], "")).strip().lower()
                category_id = categories.get(category_name)
            brand_id = None
            if mapping.get("brand"):
                brand_name = str(row.get(mapping["brand"], "")).strip().lower()
                brand_id = brands.get(brand_name)
            line_id = None
            if mapping.get("line"):
                line_name = str(row.get(mapping["line"], "")).strip().lower()
                line_id = lines.get(line_name)

            if not category_id or not brand_id:
                counters["failed"] += 1
                errors.append({"row": str(idx), "error": "category/brand not found"})
                continue

            payload = {
                "id": uuid.uuid4(),
                "name": name,
                "sku": sku or None,
                "barcode": barcode or None,
                "category_id": category_id,
                "brand_id": brand_id,
                "line_id": line_id,
                "unit": str(row.get(mapping.get("unit", ""), "pcs") or "pcs"),
                "cost_price": self._parse_decimal(row.get(mapping.get("cost_price", "")), options.get("decimal_separator", "."), options.get("thousand_separator", ",")) or Decimal("0"),
                "sell_price": self._parse_decimal(row.get(mapping.get("sell_price", "")), options.get("decimal_separator", "."), options.get("thousand_separator", ",")) or Decimal("0"),
                "tax_rate": self._parse_decimal(row.get(mapping.get("tax_rate", "")), options.get("decimal_separator", "."), options.get("thousand_separator", ",")) or Decimal("0"),
                "image_url": (str(row.get(mapping["image_url"])).strip() if mapping.get("image_url") and row.get(mapping["image_url"]) else None),
                "description": str(row.get(mapping["description"], "")).strip() if mapping.get("description") else "",
                "is_active": True,
                "is_hidden": False,
            }
            if payload["unit"] not in {unit.value for unit in ProductUnit}:
                payload["unit"] = ProductUnit.pcs.value

            conflict_column = Product.sku if match_by == "sku" else getattr(Product, match_by, Product.sku)
            conflict_values = payload.copy()
            conflict_values.pop("id", None)
            stmt = insert(Product).values(**payload).on_conflict_do_update(
                index_elements=[conflict_column],
                set_=conflict_values,
            )
            await self.session.execute(stmt)
            counters["processed"] += 1
            counters["updated"] += 1

        counters["created"] = max(counters["processed"] - counters["updated"], 0)
        status_value = "failed" if counters["failed"] and counters["processed"] == 0 else "done"
        await self.imports_repo.append_errors(import_id, errors)
        await self.imports_repo.finalize(
            import_id,
            status=status_value,
            counters=counters,
            rows_total=len(job.source_rows),
            rows_valid=counters["processed"],
            rows_invalid=len(errors),
        )
        return counters
