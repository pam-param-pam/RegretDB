from ASTNodes.BaseNode import ASTNode


class AlterAddStmt(ASTNode):
    def __init__(self, table, col_name, col_type, constraints):
        self.table = table
        self.column = col_name
        self.col_type = col_type
        self.constraints = constraints
        super().__init__()

    def __repr__(self):
        return f"AlterAddStmt(table={self.table}, new_column={self.column}, col_type={self.col_type}, constraints={self.constraints})"

    def perform_checks(self):
        pass


class AlterDropStmt(ASTNode):
    def __init__(self, table, col_name, drop_type):
        self.table = table
        self.column = col_name
        self.drop_type = drop_type
        super().__init__()

    def __repr__(self):
        return f"AlterAddStmt(table={self.table}, column={self.column}, drop_type={self.drop_type})"

    def perform_checks(self):
        pass


class AlterRenameStmt(ASTNode):
    def __init__(self, table, old_column, new_column):
        self.table = table
        self.old_column = old_column
        self.new_column = new_column
        super().__init__()

    def __repr__(self):
        return f"AlterAddStmt(table={self.table}, old_column={self.old_column}, new_column={self.new_column})"

    def perform_checks(self):
        pass


class AlterModifyStmt(ASTNode):
    def __init__(self, table, col_name, new_col_type, new_constraints):
        self.table = table
        self.column = col_name
        self.new_col_type = new_col_type
        self.new_constraints = new_constraints
        super().__init__()

    def __repr__(self):
        return f"AlterAddStmt(table={self.table}, new_column={self.column}, new_column_type={self.new_col_type}, new_constraints={self.new_constraints})"

    def perform_checks(self):
        pass
