from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

from ASTNodes.Qualified import QualifiedTable, QualifiedColumn
from DataManager import data_manager
from Exceptions import PreProcessorError, RegretDBError
from Operators.LogicalOperators import Operator
from TokenTypes import Identifier, Literal, ConstraintSpec


class ASTNode(ABC):
    def __init__(self):
        self.sql_text = None

    def verify(self):
        try:
            self.perform_checks()
        except PreProcessorError as e:
            if not self.sql_text:
                raise RegretDBError("sql_text not set in ASTNode")
            e.sql_stmt = self.sql_text
            raise e

    @abstractmethod
    def perform_checks(self):
        raise NotImplementedError()

    @abstractmethod
    def __repr__(self):
        raise NotImplementedError()

    def set_sql_text(self, sql_text):
        self.sql_text = sql_text

    def check_table(self, table_name: str, position) -> QualifiedTable:
        """Checks if table exists. Takes in a string. Returns QualifiedTable"""
        table_name = table_name.lower()
        if not data_manager.does_table_exist(table_name):
            raise PreProcessorError(f"Table '{table_name}' not found.", position=position)
        return QualifiedTable(name=table_name)

    def check_tables(self, tables: List[Identifier]) -> List[QualifiedTable]:
        """Checks if all tables exist and are unique. Returns a list of QualifiedTable."""
        seen = {}
        for t in tables:
            if t.value in seen:
                raise PreProcessorError(f"Duplicate table '{t.value}' found.", position=t.position)
            seen[t.value] = self.check_table(t.value, t.position)
        return list(seen.values())

    def check_column(self, tables: List[QualifiedTable], column: str, position) -> QualifiedColumn:
        table_name_str, col_name = self.split_column(column)

        if table_name_str:
            # Prefixed: find matching table
            matching_table = None
            for qt in tables:
                if qt.name == table_name_str:
                    matching_table = qt
                    break
            if matching_table is None:
                raise PreProcessorError(f"Table '{table_name_str}' is not specified in 'FROM' clause", position=position)
            if col_name not in data_manager.get_columns_for_table(table_name_str):
                raise PreProcessorError(f"Column '{col_name}' not found in table '{table_name_str}'", position=position)
            return QualifiedColumn(table=matching_table, column=col_name)
        else:

            # No prefix: need to resolve ambiguity
            candidates = []
            for qt in tables:
                if col_name in data_manager.get_columns_for_table(qt.name):
                    candidates.append(qt)
            if len(candidates) == 0:
                raise PreProcessorError(f"Column '{col_name}' not found in any table in FROM clause", position=position)
            if len(candidates) > 1:
                # ambiguous
                table_names = [c.name for c in candidates]
                raise PreProcessorError(f"Column '{col_name}' is ambiguous (found in tables: {', '.join(table_names)}). Please qualify it with a table name.", position=position)

            # Exactly one table has this column
            return QualifiedColumn(table=candidates[0], column=col_name)

    def check_columns(self, tables: List[QualifiedTable], columns: List[Identifier]) -> List[QualifiedColumn]:
        """Returns a list of QualifiedColumn objects after validation."""
        qualified_columns = []
        for column in columns:
            qualified_col = self.check_column(tables, column.value, position=column.position)

            if qualified_col in qualified_columns:
                raise PreProcessorError(f"Duplicate column '{column}' found", position=column.position)

            qualified_columns.append(qualified_col)
        return qualified_columns

    def split_column(self, column: str) -> Tuple[Optional[str], str]:
        """Splits a column name into (table_name, col_name). Table may be None."""
        if '.' in column:
            table_name, col_name = column.split('.')
        else:
            table_name = None
            col_name = column
        return table_name, col_name

    def check_expression(self, tables: List[QualifiedTable], where_expr):
        """checks all columns and qualifies them"""

        def recurse(node):
            if isinstance(node, Operator):
                node.left = recurse(node.left)
                node.right = recurse(node.right)
                return node

            elif isinstance(node, Identifier):
                column = self.check_column(tables, node.value, position=node.position)
                return column.full_name

            elif isinstance(node, Literal):
                return node.value

            return node

        return recurse(where_expr)

    def check_type(self, column: QualifiedColumn, value: Literal):
        """checks type compared the SCHEMA, checks if constraints allow for NULL value"""
        expected_type = data_manager.get_column_types_for_table(column.table.name)[column.column]
        constraints = data_manager.get_constraint_for_table(column.table.name)[column.column]

        # Nullability check
        if value.value is None and any(keyword in constraint.type for constraint in constraints for keyword in ('NOT NULL', 'PRIMARY KEY', 'FOREIGN KEY')):
            raise PreProcessorError(f"Column '{column}' cannot be NULL", position=value.position)

        if value.type != 'NULL' and value.type != expected_type:
            raise PreProcessorError(f"Expected type: {expected_type} got: {value} in column: '{column}'", position=value.position)

    def handle_new_column_constraints(self, constraint: ConstraintSpec, col_type: str, qualified_col_name: str) -> None:
        """
        Validates column constraints during CREATE TABLE pre-processing.
        Only performs static checks; does NOT modify the database state.
        """
        if constraint.type == 'DEFAULT':
            default = constraint.arg1  # a Literal node
            expected_type = col_type  # e.g., 'INTEGER', 'TEXT', 'BOOLEAN'

            # Type compatibility check (NULL is always allowed as DEFAULT)
            if default.type != 'NULL' and default.type != expected_type:
                raise PreProcessorError(
                    f"Invalid DEFAULT value: expected type {expected_type}, got {default.type} with value {default.value} "
                    f"for column '{qualified_col_name}'",
                    position=constraint.position
                )

        elif constraint.type == 'FOREIGN KEY':
            referenced_qualified_col = constraint.arg1  # e.g., "departments.id"
            if '.' not in referenced_qualified_col:
                raise PreProcessorError(f"Invalid FOREIGN KEY syntax: expected 'table.column', got '{referenced_qualified_col}'", position=constraint.position)
            ref_table_name, ref_col_name = self.split_column(referenced_qualified_col)

            # 1. Referenced table must exist
            if not data_manager.does_table_exist(ref_table_name):
                raise PreProcessorError(f"Referenced table '{ref_table_name}' does not exist (for foreign key on '{qualified_col_name}')", position=constraint.position)

            # 2. Referenced column must exist in that table
            if ref_col_name not in data_manager.get_columns_for_table(ref_table_name):
                raise PreProcessorError(
                    f"Referenced column '{ref_col_name}' does not exist in table '{ref_table_name}' "
                    f"(for foreign key on '{qualified_col_name}')",
                    position=constraint.position
                )

            # 3. Data types must match
            ref_table = data_manager.get_table(ref_table_name)
            ref_column = ref_table.columns.get(ref_col_name)
            if not ref_column:
                raise PreProcessorError(f"Column '{ref_col_name}' not found in table '{ref_table_name}'", position=constraint.position)

            referenced_column_type = ref_column.data_type
            if referenced_column_type != col_type:
                raise PreProcessorError(
                    f"Foreign key type mismatch: column '{qualified_col_name}' (type {col_type}) "
                    f"references '{ref_table_name}.{ref_col_name}' (type {referenced_column_type})",
                    position=constraint.position
                )
