from typing import List, Tuple

from ASTNodes.BaseNode import ASTNode, QualifiedColumn, QualifiedTable
from DataManager import data_manager
from Exceptions import PreProcessorError
from TokenTypes import Identifier, ConstraintSpec


class CreateStmt(ASTNode):
    def __init__(self, table: Identifier, column_spec: List[Tuple[Identifier, Identifier, List[ConstraintSpec]]]):
        self._table = table
        self._raw_column_spec = column_spec

        self.qualified_table = None
        self.qualified_columns_spec = None

        super().__init__()

    def __repr__(self):
        return f"CreateStmt(table={self._table}, columns={self._raw_column_spec})"

    def perform_checks(self):
        if data_manager.does_table_exist(self._table):
            raise PreProcessorError(f"Table '{self._table}' already exists", position=self._table.position)

        self.qualified_table = QualifiedTable(name=self._table.value)

        seen_columns = set()
        primary_key_count = 0

        new_columns = []

        for col_identifier, col_type_identifier, constraints in self._raw_column_spec:
            col_name = col_identifier.value
            col_type = col_type_identifier.type

            if col_name in seen_columns:
                raise PreProcessorError(f" Duplicate column name '{col_name}' in table '{self.qualified_table.name}'", position=col_identifier.position)
            seen_columns.add(col_name)

            qualified_col = QualifiedColumn(table=self.qualified_table, column=col_name)

            primary_constraint_pos = 0
            for constraint in constraints:
                if constraint.type == 'PRIMARY KEY':
                    primary_constraint_pos = constraint.position
                    primary_key_count += 1

                self.handle_new_column_constraints(constraint, col_type, qualified_col.full_name)

            if primary_key_count > 1:
                raise PreProcessorError(f"Multiple PRIMARY KEY constraints defined for table '{self.qualified_table.name}'", position=primary_constraint_pos)

            new_columns.append((qualified_col, col_type, constraints))

        self.qualified_columns_spec = new_columns
