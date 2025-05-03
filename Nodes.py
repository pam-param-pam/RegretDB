class ASTNode:
    pass

class SelectStmt(ASTNode):
    def __init__(self, columns, base_table, joins, where_expr, order_by):
        self.columns = columns
        self.base_table = base_table
        self.joins = joins  # List of (table, condition)
        self.where_expr = where_expr
        self.order_by = order_by

    def __repr__(self):
        return f"SelectStmt(columns={self.columns}, joins={self.joins}, tables={self.base_table}, where={self.where_expr}, order_by={self.order_by})"


class InsertStmt(ASTNode):
    def __init__(self, table, columns, values):
        self.table = table
        self.columns = columns  # list of column names (or None)
        self.values = values  # list of values

    def __repr__(self):
        return f"InsertStmt(table={self.table}, columns={self.columns}, values={self.values})"


class UpdateStmt(ASTNode):
    def __init__(self, table, assignments, where):
        self.table = table
        self.assignments = assignments  # list of (column, value) pairs
        self.where = where

    def __repr__(self):
        return f"UpdateStmt(table={self.table}, assignments={self.assignments}, where={self.where})"


class DeleteStmt(ASTNode):
    def __init__(self, table, where):
        self.table = table
        self.where = where

    def __repr__(self):
        return f"DeleteStmt(table={self.table}, where={self.where})"


class CreateStmt(ASTNode):
    def __init__(self, table, columns):
        self.table = table
        self.columns = columns  # list of (name, type) pairs

    def __repr__(self):
        return f"CreateStmt(table={self.table}, columns={self.columns})"


class DropStmt(ASTNode):
    def __init__(self, table):
        self.table = table

    def __repr__(self):
        return f"DropStmt(table={self.table})"


class AlterStmt(ASTNode):
    def __init__(self, table, action, column):
        self.table = table  # table name
        self.action = action  # 'ADD' or 'DROP'
        self.column = column  # column name or (name, type)

    def __repr__(self):
        return f"AlterStmt(table={self.table}, action={self.action}, column={self.column})"
