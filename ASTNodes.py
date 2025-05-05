from abc import abstractmethod, ABC

from Exceptions import PreProcessorError
from Operators.LogicalOperators import Operator


class ASTNode(ABC):
    def __init__(self):
        self.column_constraints = None
        self.column_types = None
        self.table_columns = None
        self.sql_stmt = None

    # @abstractmethod
    def verify(self, sql_stmt, metadata):
        print("verify")
        self.table_columns, self.column_types, self.column_constraints = metadata

    def check_tables(self, tables):
        """Checks if all tables exist in the schema and checks for duplicates."""
        seen = set()
        for table in tables:
            table = table.value
            if table in seen:
                raise PreProcessorError(f"Duplicate table '{table}' found.", word=table)
            if table not in self.table_columns.keys():
                raise PreProcessorError(f"Table '{table}' not found.", word=table)
            seen.add(table)

    def check_columns(self, tables, columns):
        """Checks if columns exist, checks for duplicates and checks for ambiguity"""
        seen = set()

        tables = [table.value for table in tables]

        for column in columns:
            column = column.value
            if column in seen:
                raise PreProcessorError(f"Duplicate column '{column}' found", word=column)

            table_name, col_name = self.split_column(column)
            if len(tables) == 1 and not table_name:
                table_name = tables[0]

            if table_name not in tables:
                raise PreProcessorError(f"Table '{table_name}' is not specified in 'FROM' clause", word=table_name)

            if not table_name:
                raise PreProcessorError(f"Column '{col_name}' must be prefixed(ambiguity error)", word=col_name)

            columns = self.table_columns.get(table_name)
            if not columns:
                raise PreProcessorError(f"Table '{table_name}' not found", word=table_name)
            if col_name not in self.table_columns[table_name]:
                raise PreProcessorError(f"Column '{col_name}' not found in table '{table_name}'", word=col_name)
            seen.add(column)

    def split_column(self, column):
        """Splits a column name into table and column name, if prefixed with a table."""

        if '.' in column:
            table_name, col_name = column.split('.')
        else:
            table_name = None  # No table prefix
            col_name = column
        return table_name, col_name

    def check_expression_types(self, tables, columns, where):
        def recurse(node):
            if isinstance(node, Operator):
                print(node)
                left = node.left
                right = node.right
                print(left)
                print(right)

                # # Check left operand
                # if isinstance(left, Operator):
                #     recurse(left)
                # elif isinstance(left, str) and left in columns:
                #     left_type = columns[left]
                # else:
                #     left_type = type(left).__name__.upper()
            #
            #     # Check right operand
            #     if right is not None:
            #         if isinstance(right, Operator):
            #             recurse(right)
            #         elif isinstance(right, str) and right in columns:
            #             right_type = columns[right]
            #         else:
            #             right_type = type(right).__name__.upper()
            #
            #         # Check for type mismatch in binary ops
            #         if isinstance(node, (GT, LT, GE, TE, EG, NE)):
            #             if left_type != right_type:
            #                 print(f"Type mismatch: {left_type} vs {right_type} in {node}")
            else:
                pass
        recurse(where)

class SelectStmt(ASTNode):
    def __init__(self, columns, tables, where_expr, order_by):
        self.columns = columns
        self.tables = tables
        self.where_expr = where_expr
        self.order_by = order_by
        super().__init__()

    def __repr__(self):
        return f"SelectStmt(columns={self.columns}, tables={self.tables}, where={self.where_expr}, order_by={self.order_by})"

    def verify(self, sql_stmt, metadata):
        super().verify(sql_stmt, metadata)
        try:
            self.check_tables(self.tables)
            self.check_columns(self.tables, self.columns)
            self.check_expression_types(self.tables, self.columns, self.where_expr)
        except PreProcessorError as e:
            e.sql_stmt = sql_stmt
            raise e

class InsertStmt(ASTNode):
    def __init__(self, table, columns, values):
        self.table = table
        self.columns = columns  # list of column names (or None)
        self.values = values  # list of values
        super().__init__()

    def __repr__(self):
        return f"InsertStmt(table={self.table}, columns={self.columns}, values={self.values})"

    def verify(self, sql_stmt, metadata):
        super().verify(sql_stmt, metadata)
        if len(self.columns) != len(self.values):
            # diff = abs(len(self.columns) - len(self.values))
            # if len(self.columns) > len(self.values):
            #     unmatched = self.columns[-diff:]
            # else:
            #     unmatched = self.values[-diff:]
            raise PreProcessorError(f"Columns length({len(self.columns)}) != values length({len(self.values)})")  # , word=unmatched

        tables = [self.table]
        self.check_tables(tables)
        self.check_columns(tables, self.columns)

class UpdateStmt(ASTNode):
    def __init__(self, table, assignments, where):
        self.table = table
        self.assignments = assignments  # list of (column, value) pairs
        self.where = where
        super().__init__()

    def __repr__(self):
        return f"UpdateStmt(table={self.table}, assignments={self.assignments}, where={self.where})"

    def verify(self, metadata):
        pass


class DeleteStmt(ASTNode):
    def __init__(self, table, where):
        self.table = table
        self.where = where
        super().__init__()

    def __repr__(self):
        return f"DeleteStmt(table={self.table}, where={self.where})"

    def verify(self, metadata):
        pass


class CreateStmt(ASTNode):
    def __init__(self, table, columns):
        self.table = table
        self.columns = columns  # list of (name, type) pairs
        super().__init__()

    def __repr__(self):
        return f"CreateStmt(table={self.table}, columns={self.columns})"

    def verify(self, metadata):
        pass


class DropStmt(ASTNode):
    def __init__(self, table):
        self.table = table
        super().__init__()

    def __repr__(self):
        return f"DropStmt(table={self.table})"

    def verify(self, metadata):
        pass


class AlterStmt(ASTNode):
    def __init__(self, table, action, column):
        self.table = table  # table name
        self.action = action  # 'ADD' or 'DROP'
        self.column = column  # column name or (name, type)
        super().__init__()

    def __repr__(self):
        return f"AlterStmt(table={self.table}, action={self.action}, column={self.column})"

    def verify(self, metadata):
        pass


# Tworzenie obiektu SelectStmt
# select = SelectStmt(
#     columns=['users.name', 'orders.order_id'],
#     tables=['users', 'orders'],
#     where_expr=(),  # some expression object
#     order_by=[],
# )
# select.verify()
