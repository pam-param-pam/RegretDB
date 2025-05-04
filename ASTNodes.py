from abc import abstractmethod, ABC

from Exceptions import PreProcessorError


class ASTNode(ABC):
    def __init__(self):
        self.verify()

    @abstractmethod
    def verify(self):
        raise NotImplementedError("verify() not implemented")

class SelectStmt(ASTNode):
    def __init__(self, columns, base_table, where_expr, order_by):
        self.columns = columns
        self.base_table = base_table
        self.where_expr = where_expr
        self.order_by = order_by
        super().__init__()

    def __repr__(self):
        return f"SelectStmt(columns={self.columns}, tables={self.base_table}, where={self.where_expr}, order_by={self.order_by})"

    def verify(self):
        pass

class InsertStmt(ASTNode):
    def __init__(self, table, columns, values):
        self.table = table
        self.columns = columns  # list of column names (or None)
        self.values = values  # list of values
        super().__init__()

    def __repr__(self):
        return f"InsertStmt(table={self.table}, columns={self.columns}, values={self.values})"

    def verify(self):
        if len(self.columns) != len(self.values):
            raise PreProcessorError(f"Values length({len(self.values)}) != columns length({len(self.columns)})")

class UpdateStmt(ASTNode):
    def __init__(self, table, assignments, where):
        self.table = table
        self.assignments = assignments  # list of (column, value) pairs
        self.where = where
        super().__init__()

    def __repr__(self):
        return f"UpdateStmt(table={self.table}, assignments={self.assignments}, where={self.where})"

    def verify(self):
        pass

class DeleteStmt(ASTNode):
    def __init__(self, table, where):
        self.table = table
        self.where = where
        super().__init__()

    def __repr__(self):
        return f"DeleteStmt(table={self.table}, where={self.where})"

    def verify(self):
        pass

class CreateStmt(ASTNode):
    def __init__(self, table, columns):
        self.table = table
        self.columns = columns  # list of (name, type) pairs
        super().__init__()

    def __repr__(self):
        return f"CreateStmt(table={self.table}, columns={self.columns})"

    def verify(self):
        pass

class DropStmt(ASTNode):
    def __init__(self, table):
        self.table = table
        super().__init__()

    def __repr__(self):
        return f"DropStmt(table={self.table})"

    def verify(self):
        pass

class AlterStmt(ASTNode):
    def __init__(self, table, action, column):
        self.table = table  # table name
        self.action = action  # 'ADD' or 'DROP'
        self.column = column  # column name or (name, type)
        super().__init__()

    def __repr__(self):
        return f"AlterStmt(table={self.table}, action={self.action}, column={self.column})"

    def verify(self):
        pass
