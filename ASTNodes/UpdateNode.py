from ASTNodes.BaseNode import ASTNode


class UpdateStmt(ASTNode):
    def __init__(self, table, assignments, where):
        self.table = table
        self.assignments = assignments  # list of (column, value) pairs
        self.where = where
        super().__init__()

    def __repr__(self):
        return f"UpdateStmt(table={self.table}, assignments={self.assignments}, where={self.where})"

    def perform_checks(self):
        tables = [self.table.value]
        self.check_tables(tables)

        new_assignments = []
        for assignment in self.assignments:
            column = self.check_column(tables, assignment[0].value)

            self.check_type(column, assignment[1])

            new_assignments.append((column, assignment[1].value))

        self.assignments = new_assignments
