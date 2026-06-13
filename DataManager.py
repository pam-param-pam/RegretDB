from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple

from Exceptions import IntegrityError


class FkAction(Enum):
    RESTRICT = "RESTRICT"
    CASCADE = "CASCADE"
    SET_NULL = "SET NULL"


@dataclass
class ForeignKey:
    column: str
    ref_table: str
    ref_column: str
    on_delete: FkAction = FkAction.RESTRICT
    on_update: FkAction = FkAction.RESTRICT


@dataclass
class Column:
    name: str
    data_type: str          # 'INTEGER', 'TEXT', 'BOOLEAN', 'NULL'
    nullable: bool = True
    unique: bool = False
    primary_key: bool = False
    default: Any = None
    foreign_key: Optional[ForeignKey] = None


class Table:
    def __init__(self, name: str, columns: List[Column]):
        self.name = name
        self.columns: Dict[str, Column] = {col.name: col for col in columns}
        self.column_order: List[str] = [col.name for col in columns]
        self.data: List[Dict[str, Any]] = []               # rows with unqualified keys
        self.pk_index: Dict[Any, int] = {}                 # primary key value -> row index
        self._reverse_fk: Dict[str, List[Tuple[str, str]]] = {}  # {ref_table: [(child_table, child_col), ...]}

    def __repr__(self) -> str:
        return f"Table(name={self.name}, columns={list(self.columns.keys())})"

    def get_primary_key(self) -> Optional[str]:
        for col in self.columns.values():
            if col.primary_key:
                return col.name
        return None

    # ------------------------------------------------------------------
    # Public DML
    # ------------------------------------------------------------------
    def insert(self, row: Dict[str, Any]) -> None:
        full_row = self._prepare_row(row)
        self._check_constraints(full_row, is_insert=True)
        row_idx = len(self.data)
        self.data.append(full_row)
        self._update_pk_index(full_row, row_idx, is_insert=True)

    def update(self, row_idx: int, new_values: Dict[str, Any]) -> None:
        old_row = self.data[row_idx].copy()
        updated_row = {**old_row, **new_values}
        self._check_constraints(updated_row, is_insert=False, old_row=old_row)

        # Handle primary key changes (cascade updates)
        pk = self.get_primary_key()
        if pk and pk in new_values:
            old_pk = old_row.get(pk)
            new_pk = new_values[pk]
            if old_pk != new_pk:
                self._handle_pk_update(old_row, old_pk, new_pk, row_idx)

        self.data[row_idx] = updated_row

    def delete(self, row_idx: int) -> None:
        row = self.data[row_idx]
        pk = self.get_primary_key()
        pk_val = row.get(pk) if pk else None
        # Cascade or restrict before deletion
        self._handle_fk_on_delete(row, pk_val)
        # Remove from data and index
        self.data.pop(row_idx)
        if pk and pk_val is not None:
            self.pk_index.pop(pk_val, None)
        self._rebuild_pk_index()   # because indices shift after pop

    # ------------------------------------------------------------------
    # Row retrieval (for SELECT)
    # ------------------------------------------------------------------
    def get_qualified_rows(self) -> List[Dict[str, Any]]:
        """
        Return rows with qualified keys (table.column) and an internal '_rowid'.
        The '_rowid' is the row index in the table (0-based) and is used for fast
        deletes/updates.
        """
        result = []
        for idx, row in enumerate(self.data):
            qualified_row = {f"{self.name}.{col}": row[col] for col in self.column_order}
            qualified_row["_rowid"] = idx
            result.append(qualified_row)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _prepare_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        full = {}
        for col_name, col in self.columns.items():
            if col_name in row:
                val = row[col_name]
            else:
                if col.default is not None:
                    val = col.default
                elif col.nullable:
                    val = None
                else:
                    raise IntegrityError(f"Column '{col_name}' has no value and no default")
            full[col_name] = val
        return full

    def _check_constraints(self, row: Dict[str, Any], is_insert: bool, old_row: Dict[str, Any] = None) -> None:
        for col_name, col in self.columns.items():
            val = row.get(col_name)
            # NOT NULL
            if not col.nullable and val is None:
                raise IntegrityError(f"Column '{col_name}' cannot be NULL")

            # UNIQUE
            if col.unique and val is not None:
                if is_insert or (old_row and old_row.get(col_name) != val):
                    if self._exists_unique(col_name, val, exclude_idx=self._get_row_idx(old_row) if old_row else None):
                        raise IntegrityError(f"Unique constraint violated on '{col_name}' with value '{val}'")

            # FOREIGN KEY (basic existence check – cascades handled separately)
            if col.foreign_key and val is not None:
                ref_table = data_manager.get_table(col.foreign_key.ref_table)
                if not ref_table._exists_value(col.foreign_key.ref_column, val):
                    raise IntegrityError(
                        f"Foreign key violation: '{val}' not found in {col.foreign_key.ref_table}.{col.foreign_key.ref_column}"
                    )

    def _exists_unique(self, column: str, value: Any, exclude_idx: Optional[int] = None) -> bool:
        for i, row in enumerate(self.data):
            if exclude_idx is not None and i == exclude_idx:
                continue
            if row.get(column) == value:
                return True
        return False

    def _exists_value(self, column: str, value: Any) -> bool:
        return any(row.get(column) == value for row in self.data)

    def _get_row_idx(self, row: Dict[str, Any]) -> Optional[int]:
        for i, r in enumerate(self.data):
            if r is row:
                return i
        return None

    def _update_pk_index(self, row: Dict[str, Any], row_idx: int, is_insert: bool) -> None:
        pk = self.get_primary_key()
        if not pk:
            return
        pk_val = row.get(pk)
        if pk_val is None:
            raise IntegrityError(f"Primary key '{pk}' cannot be NULL")
        if is_insert and pk_val in self.pk_index:
            raise IntegrityError(f"Duplicate primary key value '{pk_val}'")
        self.pk_index[pk_val] = row_idx

    def _rebuild_pk_index(self) -> None:
        pk = self.get_primary_key()
        if not pk:
            return
        self.pk_index.clear()
        for idx, row in enumerate(self.data):
            val = row.get(pk)
            if val is not None:
                if val in self.pk_index:
                    raise IntegrityError(f"Inconsistent data: duplicate PK '{val}'")
                self.pk_index[val] = idx

    # ------------------------------------------------------------------
    # Foreign key actions
    # ------------------------------------------------------------------
    def _handle_fk_on_delete(self, row: Dict[str, Any], pk_val: Any) -> None:
        """Cascade or set null to referencing rows before deleting this row."""
        for child_table_name, child_col in self._get_referencing_tables():
            child_table = data_manager.get_table(child_table_name)
            fk_col = child_table.columns[child_col].foreign_key
            if not fk_col:
                continue
            # Find rows in child table that reference this row
            for child_idx, child_row in enumerate(child_table.data):
                if child_row.get(child_col) == pk_val:
                    if fk_col.on_delete == FkAction.CASCADE:
                        child_table.delete(child_idx)
                    elif fk_col.on_delete == FkAction.SET_NULL:
                        child_table.update(child_idx, {child_col: None})
                    else:  # RESTRICT
                        raise IntegrityError(
                            f"Foreign key violation: cannot delete row in {self.name} – referenced by {child_table_name}.{child_col}"
                        )

    def _handle_pk_update(self, old_row: Dict[str, Any], old_pk: Any, new_pk: Any, row_idx: int) -> None:
        """Cascade or set null to referencing rows when primary key changes."""
        if new_pk in self.pk_index and self.pk_index[new_pk] != row_idx:
            raise IntegrityError(f"Duplicate primary key value '{new_pk}'")
        # Remove old index entry, will be re-added after update
        self.pk_index.pop(old_pk, None)

        for child_table_name, child_col in self._get_referencing_tables():
            child_table = data_manager.get_table(child_table_name)
            fk_col = child_table.columns[child_col].foreign_key
            if not fk_col:
                continue
            for child_idx, child_row in enumerate(child_table.data):
                if child_row.get(child_col) == old_pk:
                    if fk_col.on_update == FkAction.CASCADE:
                        child_table.update(child_idx, {child_col: new_pk})
                    elif fk_col.on_update == FkAction.SET_NULL:
                        child_table.update(child_idx, {child_col: None})
                    else:  # RESTRICT
                        raise IntegrityError(
                            f"Foreign key violation: cannot update primary key in {self.name} – referenced by {child_table_name}.{child_col}"
                        )
        # Re-add pk index after all updates
        self.pk_index[new_pk] = row_idx

    def _get_referencing_tables(self) -> List[Tuple[str, str]]:
        """Return list of (child_table_name, child_column) that reference this table."""
        if hasattr(self, '_reverse_fk_cache'):
            return self._reverse_fk_cache
        result = []
        for table in data_manager._tables.values():
            for col_name, col in table.columns.items():
                if col.foreign_key and col.foreign_key.ref_table == self.name:
                    result.append((table.name, col_name))
        self._reverse_fk_cache = result
        return result


class DataManager:
    def __init__(self):
        self._tables: Dict[str, Table] = {}

    # ------------------------------------------------------------------
    # Schema operations
    # ------------------------------------------------------------------
    def create_table(self, name: str, columns: List[Column]) -> None:
        if name in self._tables:
            raise IntegrityError(f"Table '{name}' already exists")
        self._tables[name] = Table(name, columns)

    def drop_table(self, name: str) -> None:
        table = self.get_table(name)
        # Check foreign key dependencies (tables that reference this table)
        for other in self._tables.values():
            for col in other.columns.values():
                if col.foreign_key and col.foreign_key.ref_table == name:
                    raise IntegrityError(f"Cannot drop '{name}' – referenced by FK in '{other.name}.{col.name}'")
        del self._tables[name]

    def get_table(self, name: str) -> Table:
        if name not in self._tables:
            raise IntegrityError(f"Table '{name}' does not exist")
        return self._tables[name]

    def does_table_exist(self, name: str) -> bool:
        return name in self._tables

    # ------------------------------------------------------------------
    # Data access for DML / SELECT
    # ------------------------------------------------------------------
    def insert_row(self, table_name: str, row: Dict[str, Any]) -> None:
        self._tables[table_name].insert(row)

    def update_rows(self, table_name: str, updates: Dict[str, Any], where_func: Optional[callable] = None) -> int:
        """Update rows matching where_func (if None, update all). Returns count of updated rows."""
        table = self._tables[table_name]
        updated = 0
        for idx, row in enumerate(table.data):
            if where_func is None or where_func(row):
                table.update(idx, updates)
                updated += 1
        return updated

    def delete_rows(self, table_name: str, where_func: Optional[callable] = None) -> int:
        """Delete rows matching where_func (if None, delete all). Returns count of deleted rows."""
        table = self._tables[table_name]
        # Delete from end to avoid index shifting issues
        deleted = 0
        for idx in range(len(table.data) - 1, -1, -1):
            if where_func is None or where_func(table.data[idx]):
                table.delete(idx)
                deleted += 1
        return deleted

    # ------------------------------------------------------------------
    # Query execution helpers (for SELECT)
    # ------------------------------------------------------------------
    def get_qualified_rows(self, table_name: str) -> List[Dict[str, Any]]:
        """Return rows with 'table.column' keys – ready for SELECT."""
        return self._tables[table_name].get_qualified_rows()

    def get_all_qualified_rows(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return qualified rows for all tables (for multi‑table SELECT)."""
        return {name: table.get_qualified_rows() for name, table in self._tables.items()}

    # ------------------------------------------------------------------
    # Metadata helpers (for preprocessor)
    # ------------------------------------------------------------------
    def get_columns_for_table(self, table_name: str) -> List[str]:
        return self._tables[table_name].column_order

    def get_column_type(self, table_name: str, column_name: str) -> str:
        col = self._tables[table_name].columns.get(column_name)
        if not col:
            raise IntegrityError(f"Column '{column_name}' not found in table '{table_name}'")
        return col.data_type

    def get_column_types_for_table(self, table_name: str) -> Dict[str, str]:
        return {name: col.data_type for name, col in self._tables[table_name].columns.items()}

    def get_constraint_for_table(self, table_name: str) -> Dict[str, List[Any]]:
        constraints = {}
        for col in self._tables[table_name].columns.values():
            col_constraints = []
            if not col.nullable:
                col_constraints.append(self._make_constraint("NOT NULL"))
            if col.unique:
                col_constraints.append(self._make_constraint("UNIQUE"))
            if col.primary_key:
                col_constraints.append(self._make_constraint("PRIMARY KEY"))
            if col.foreign_key:
                fk = col.foreign_key
                col_constraints.append(self._make_constraint("FOREIGN KEY", arg1=f"{fk.ref_table}.{fk.ref_column}"))
            constraints[col.name] = col_constraints
        return constraints

    @staticmethod
    def _make_constraint(typ: str, arg1=None):
        # Simple object to mimic old Constraint class
        return type("Constraint", (), {"type": typ, "arg1": arg1})()


# Singleton instance
data_manager = DataManager()