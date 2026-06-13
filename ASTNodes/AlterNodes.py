from typing import Optional, List, Tuple
from ASTNodes.BaseNode import ASTNode
from ASTNodes.Qualified import QualifiedTable, QualifiedColumn
from DataManager import data_manager
from Exceptions import PreProcessorError
from TokenTypes import Identifier, ConstraintSpec


class AlterAddStmt(ASTNode):
    def __init__(self, table: Identifier, column_spec: Tuple[Identifier, Identifier, List[ConstraintSpec]]):
        self._table = table
        self._column_spec = column_spec
        self.qualified_table: Optional[QualifiedTable] = None
        self.qualified_column_spec = None
        super().__init__()

    def __repr__(self):
        if self.qualified_column_spec:
            qcol, col_type, constraints = self.qualified_column_spec
            return f"AlterAddStmt(table={self.qualified_table}, column={qcol.column}, type={col_type}, constraints={constraints})"
        return f"AlterAddStmt(table={self._table.value}, column={self._column_spec[0].value})"

    def perform_checks(self):
        # 1. Validate table exists and qualify it
        self.qualified_table = self.check_table(self._table.value, self._table.position)

        col_name_id, col_type_id, constraints = self._column_spec
        col_name = col_name_id.value
        col_type = col_type_id.value

        # 2. Check that column does not already exist
        if col_name in data_manager.get_columns_for_table(self.qualified_table.name):
            raise PreProcessorError(f"Column '{col_name}' already exists in table '{self.qualified_table.name}'", position=col_name_id.position)

        # 3. Build qualified column
        qualified_col = QualifiedColumn(table=self.qualified_table, column=col_name)
        qualified_full = qualified_col.full_name

        # 4. Validate each constraint
        for constraint in constraints:
            self.handle_new_column_constraints(constraint, col_type, qualified_full)

        col_name_id, col_type_id, constraints = self._column_spec
        is_not_null = any(c.type == 'NOT NULL' for c in constraints)
        has_default = any(c.type == 'DEFAULT' for c in constraints)

        if is_not_null and not has_default:
            table_obj = data_manager.get_table(self.qualified_table.name)
            if table_obj.data:
                raise PreProcessorError(
                    f"Column '{col_name_id.value}' is NOT NULL and has no DEFAULT – cannot add to non‑empty table '{self.qualified_table.name}'",
                    position=col_name_id.position
                )

        self.qualified_column_spec = (qualified_col, col_type, constraints)


class AlterRenameStmt(ASTNode):
    def __init__(self, table: Identifier, old_column: Identifier, new_column: Identifier):
        self._table = table
        self._old_column = old_column
        self._new_column = new_column
        self.qualified_table: Optional[QualifiedTable] = None
        self.qualified_old_column: Optional[QualifiedColumn] = None
        self.qualified_new_column: Optional[QualifiedColumn] = None
        super().__init__()

    def __repr__(self):
        return f"AlterRenameStmt(table={self.qualified_table}, old_column={self.qualified_old_column}, new_column={self.qualified_new_column})"

    def perform_checks(self):
        self.qualified_table = self.check_table(self._table.value, self._table.position)
        self.check_column([self.qualified_table], self._old_column.value, position=self._old_column.position)

        table_obj = data_manager.get_table(self.qualified_table.name)
        if self._new_column in table_obj.columns:
            raise PreProcessorError(f"Column '{self._new_column}' already exists in table '{self.qualified_table.name}'", position=self._new_column.position)

        self.qualified_old_column = QualifiedColumn(table=self.qualified_table, column=self._old_column.value)
        self.qualified_new_column = QualifiedColumn(table=self.qualified_table, column=self._new_column.value)


class AlterDropStmt(ASTNode):
    def __init__(self, table: Identifier, col_name: Identifier, drop_type: str):
        self._table = table
        self._col_name = col_name
        self.drop_type = drop_type
        self.qualified_table: Optional[QualifiedTable] = None
        self.qualified_column: Optional[QualifiedColumn] = None
        super().__init__()

    def __repr__(self):
        return f"AlterDropStmt(table={self.qualified_table}, column={self.qualified_column}, drop_type={self.drop_type})"

    def perform_checks(self):
        # 1. Validate table exists and qualify it
        self.qualified_table = self.check_table(self._table.value, self._table.position)
        qualified_column = self.check_column([self.qualified_table], self._col_name.value, position=self._col_name.position)

        table_obj = data_manager.get_table(self.qualified_table.name)

        col = table_obj.columns[qualified_column.column]

        # 2. Disallow dropping a PRIMARY KEY column
        if col.primary_key:
            raise PreProcessorError(f"Cannot drop PRIMARY KEY column '{col.name}' from table '{self.qualified_table.name}'", position=self._col_name.position)

        # 3. Check for foreign keys referencing this column
        referencing = data_manager.get_referencing_foreign_keys(self.qualified_table.name, col.name)
        if referencing:
            if self.drop_type != 'CASCADE':
                refs = ', '.join(f"{tbl}.{c}" for tbl, c in referencing)
                raise PreProcessorError(f"Cannot drop column '{col.name}' – referenced by foreign key(s): {refs}. Use CASCADE.", position=self._col_name.position)

        self.qualified_column = qualified_column

class AlterModifyStmt(ASTNode):
    def __init__(self, table: Identifier, col_name: Identifier, new_col_type: Identifier, new_constraints: List[ConstraintSpec]):
        self._table = table
        self._col_name = col_name
        self._new_col_type = new_col_type
        self._new_constraints = new_constraints
        self.qualified_table: Optional[QualifiedTable] = None
        self.qualified_column: Optional[QualifiedColumn] = None
        self.qualified_new_column_spec: Optional[Tuple[QualifiedColumn, str, List[ConstraintSpec]]] = None
        super().__init__()

    def __repr__(self):
        return f"AlterModifyStmt(table={self.qualified_table}, column={self.qualified_column}, new_type={self._new_col_type}, new_constraints={self._new_constraints})"

    def perform_checks(self):
        pass
        # # 1. Validate table exists and qualify it
        # self.qualified_table = self.check_table(self._table.value, self._table.position)
        #
        # # 2. Qualify the existing column – also checks it exists
        # self.qualified_column = self.check_column([self.qualified_table], self._col_name.value, position=self._col_name.position)
        #
        # table_obj = data_manager.get_table(self.qualified_table.name)
        # col_name = self.qualified_column.column
        # existing_col = table_obj.columns[col_name]
        #
        # # 3. Basic static checks on the existing column
        # if existing_col.primary_key:
        #     raise PreProcessorError(f"Cannot modify PRIMARY KEY column '{col_name}'", position=self._col_name.position)
        #
        # if existing_col.foreign_key:
        #     raise PreProcessorError(f"Cannot modify column '{col_name}' – it has a foreign key constraint", position=self._col_name.position)
        #
        # referencing = data_manager.get_referencing_foreign_keys(self.qualified_table.name, col_name)
        # if referencing:
        #     refs = ', '.join(f"{tbl}.{c}" for tbl, c in referencing)
        #     raise PreProcessorError(f"Cannot modify column '{col_name}' – referenced by foreign key(s): {refs}", position=self._col_name.position)
        #
        # # 4. If table already has rows, disallow type change (strict, like many dbs)
        # if table_obj.data and existing_col.data_type != self._new_col_type.value:
        #     raise PreProcessorError(
        #         f"Cannot change type of column '{col_name}' from {existing_col.data_type} to {self._new_col_type.value} – table '{self.qualified_table.name}' already contains rows",
        #         position=self._new_col_type.position
        #     )
        #
        # # 5. Parse the new constraints to see if they are allowed
        # new_col_type_str = self._new_col_type.value
        # qualified_full = self.qualified_column.full_name
        #
        # # Determine nullability and default from new constraints
        # is_not_null = any(c.type == 'NOT NULL' for c in self._new_constraints)
        # has_default = any(c.type == 'DEFAULT' for c in self._new_constraints)
        #
        # # If adding NOT NULL and no DEFAULT, and table has rows, we need to verify that no NULLs exist
        # if is_not_null and not has_default and table_obj.data:
        #     for row in table_obj.data:
        #         if row.get(col_name) is None:
        #             raise PreProcessorError(f"Cannot add NOT NULL constraint to column '{col_name}' – existing NULL values found", position=self._col_name.position)
        #
        # # Validate the new constraints against the column (type compatibility, FK existence etc.)
        # for constraint in self._new_constraints:
        #     # For FOREIGN KEY, we disallow adding FK via MODIFY
        #     if constraint.type == 'FOREIGN KEY':
        #         raise PreProcessorError(f"Cannot add FOREIGN KEY constraint via MODIFY – use separate ALTER TABLE ADD CONSTRAINT", position=self._col_name.position)
        #
        #     self.handle_new_column_constraints(constraint, new_col_type_str, qualified_full)
        #
        # # 6. Store the new specification for the executor
        # self.qualified_new_column_spec = (self.qualified_column, new_col_type_str, self._new_constraints)
