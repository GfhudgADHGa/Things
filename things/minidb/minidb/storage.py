"""In-memory table storage with typed columns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .ast_nodes import ColumnDef
from .errors import SchemaError


@dataclass
class Table:
    name: str
    columns: list  # list[ColumnDef]
    rows: list = field(default_factory=list)  # list[list[object]]

    def column_names(self) -> list:
        return [c.name for c in self.columns]

    def column_index(self, name: str) -> int:
        for i, c in enumerate(self.columns):
            if c.name == name:
                return i
        raise SchemaError(f"no such column: {name}")

    def coerce(self, col_index: int, value):
        if value is None:
            return None
        col_type = self.columns[col_index].type
        if col_type == "INTEGER":
            return int(value)
        if col_type == "REAL":
            return float(value)
        return str(value)


class Database:
    def __init__(self):
        self.tables: dict = {}

    def create_table(self, name: str, columns: list) -> None:
        if name in self.tables:
            raise SchemaError(f"table {name!r} already exists")
        if not columns:
            raise SchemaError(f"table {name!r} must have at least one column")
        seen = set()
        for c in columns:
            if c.name in seen:
                raise SchemaError(f"duplicate column name {c.name!r} in table {name!r}")
            seen.add(c.name)
        self.tables[name] = Table(name, columns)

    def get_table(self, name: str) -> Table:
        if name not in self.tables:
            raise SchemaError(f"no such table: {name}")
        return self.tables[name]
