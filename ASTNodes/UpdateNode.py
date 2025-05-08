from ASTNodes.BaseNode import ASTNode


class UpdateStmt(ASTNode):
    def __init__(self, table, assignments, where):
        self.table = table
        self.assignments = assignments  # list of (column, value) pairs
        self.where_expr = where
        super().__init__()

    def __repr__(self):
        return f"UpdateStmt(table={self.table}, assignments={self.assignments}, where={self.where_expr})"

    def perform_checks(self):
        self.table = self.table.value
        self.check_table(self.table)

        tables = [self.table]

        new_assignments = []
        for assignment in self.assignments:
            column = self.check_column(tables, assignment[0].value)

            self.check_type(self.table, column, assignment[1])

            new_assignments.append((column, assignment[1].value))

        self.assignments = new_assignments

        # Checking the expression and qualifying column names in the where expr
        if self.where_expr:
            self.where_expr = self.check_expression(tables, self.where_expr)
