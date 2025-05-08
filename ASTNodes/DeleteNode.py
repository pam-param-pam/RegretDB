from ASTNodes.BaseNode import ASTNode


class DeleteStmt(ASTNode):
    def __init__(self, table, where):
        self.table = table
        self.where = where
        super().__init__()

    def __repr__(self):
        return f"DeleteStmt(table={self.table}, where={self.where})"

    def perform_checks(self):
        pass
