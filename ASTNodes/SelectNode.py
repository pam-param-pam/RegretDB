from typing import List, Tuple
from ASTNodes.BaseNode import ASTNode
from DataManager import data_manager
from Exceptions import PreProcessorError
from TokenTypes import Identifier


class SelectStmt(ASTNode):
    def __init__(self, columns: List[Identifier], tables: List[Identifier], where_expr, order_by: List[Tuple[Identifier, str]]):
        self._columns = columns
        self._tables = tables
        self._where_expr = where_expr
        self._order_by = order_by

        self.qualified_tables = None
        self.qualified_columns = None
        self.qualified_where_expr = None
        self.qualified_order_by = None

        super().__init__()

    def __repr__(self):
        return f"SelectStmt(columns={self._columns}, tables={self._tables}, where={self._where_expr}, order_by={self._order_by})"

    def perform_checks(self):
        self.qualified_tables = self.check_tables(self._tables)

        self.qualified_columns = []
        for identifier in self._columns:
            col = identifier.value
            if col == '*':
                # All columns from all tables
                tables = [qt.name for qt in self.qualified_tables]
            elif col.endswith('.*'):
                # All columns from a specific table
                tables = [col[:-2]]
                self.check_table(tables[0], position=identifier.position)
            else:
                # Single column – qualify and continue
                self.qualified_columns.append(self.check_column(self.qualified_tables, col, position=identifier.position))
                continue

            # Expand and qualify all columns from the selected tables
            for t in tables:
                for col_name in data_manager.get_columns_for_table(t):
                    self.qualified_columns.append(self.check_column(self.qualified_tables, col_name, position=identifier.position))

        # Step 4: qualify column names in WHERE expression (if present)
        if self._where_expr:
            self.qualified_where_expr = self.check_expression(self.qualified_tables, self._where_expr)

        # Step 5: qualify column names in ORDER BY (if present)
        if self._order_by:
            self.qualified_order_by = self.check_order_by(self._order_by)

    def check_order_by(self, order_by: List[Tuple[Identifier, str]]):
        """Qualify and validate ORDER BY columns."""
        seen = set()
        new_order_by = []
        for element in order_by:
            col_identifier = element[0]
            qualified_col = self.check_column(self.qualified_tables, col_identifier.value, position=col_identifier.position)
            col_full_name = qualified_col.full_name
            if col_full_name in seen:
                raise PreProcessorError(f"Duplicate column '{col_full_name}' in ORDER BY", position=col_identifier.position)
            seen.add(col_full_name)
            new_order_by.append((qualified_col, element[1]))
        return new_order_by
