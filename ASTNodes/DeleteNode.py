from typing import Optional

from ASTNodes.BaseNode import ASTNode
from ASTNodes.Qualified import QualifiedTable
from TokenTypes import Identifier


class DeleteStmt(ASTNode):
    def __init__(self, table: Identifier, where_expr):
        self._table = table
        self._where_expr = where_expr
        self.qualified_table: Optional[QualifiedTable] = None
        self.qualified_where_expr = None
        super().__init__()

    def __repr__(self):
        return f"DeleteStmt(table={self.qualified_table}, where={self._where_expr})"

    def perform_checks(self):
        # Step 1: validate and qualify the table
        self.qualified_table = self.check_table(self._table.value, self._table.position)
        tables = [self.qualified_table]   # list of QualifiedTable

        # Step 2: qualify columns in WHERE expression (if present)
        if self._where_expr:
            self.qualified_where_expr = self.check_expression(tables, self._where_expr)

