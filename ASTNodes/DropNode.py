from ASTNodes.BaseNode import ASTNode
from TokenTypes import Identifier


class DropStmt(ASTNode):
    def __init__(self, table: Identifier):
        self._table = table
        self.qualified_table = None
        super().__init__()

    def __repr__(self):
        return f"DropStmt(table={self.qualified_table})"

    def perform_checks(self):
        self.qualified_table = self.check_table(self._table.value, self._table.position)
