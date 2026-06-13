from typing import List, Optional, Tuple

from ASTNodes.BaseNode import ASTNode
from ASTNodes.Qualified import QualifiedTable, QualifiedColumn
from TokenTypes import Identifier, Literal


class UpdateStmt(ASTNode):
    def __init__(self, table: Identifier, assignments: List[Tuple[Identifier, Literal]], where_expr):
        self._table = table
        self._assignments = assignments
        self.where_expr = where_expr
        self.qualified_table: Optional[QualifiedTable] = None
        self.qualified_assignments: Optional[List[Tuple[QualifiedColumn, Literal]]] = None
        super().__init__()

    def __repr__(self):
        return f"UpdateStmt(table={self.qualified_table}, assignments={self.qualified_assignments}, where={self.where_expr})"

    def perform_checks(self):
        # 1. Validate and qualify the target table
        self.qualified_table = self.check_table(self._table.value, self._table.position)
        tables = [self.qualified_table]   # list of QualifiedTable

        # 2. Process each assignment: qualify column and type-check
        self.qualified_assignments = []
        for col_id, val_literal in self._assignments:

            qualified_col = self.check_column(tables, col_id.value, position=col_id.position)

            self.check_type(qualified_col, val_literal)
            self.qualified_assignments.append((qualified_col, val_literal))

        # 3. Qualify columns in WHERE clause (if any)
        if self.where_expr:
            self.where_expr = self.check_expression(tables, self.where_expr)
