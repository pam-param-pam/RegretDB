from ASTNodes.BaseNode import ASTNode


class DeleteStmt(ASTNode):
    def __init__(self, table, where_expr):
        self.table = table
        self.where_expr = where_expr
        super().__init__()

    def __repr__(self):
        return f"DeleteStmt(table={self.table}, where={self.where_expr})"

    def perform_checks(self):
        self.table = self.table.value
        self.check_table(self.table)
        self.where_expr = self.check_expression([self.table], self.where_expr)

