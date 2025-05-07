from abc import ABC

from DataManager import data_manager
from Exceptions import PreProcessorError, RegretDBError
from Operators.LogicalOperators import Operator
from TokenTypes import Identifier, Literal


class ASTNode(ABC):
    def __init__(self):
        self.column_constraints = data_manager.get_column_constraints()
        self.column_types = data_manager.get_column_types()
        self.table_columns = data_manager.get_table_columns()
        self.sql_text = None

    def verify(self):
        try:
            self.perform_checks()
        except PreProcessorError as e:
            if not self.sql_text:
                raise RegretDBError("sql_text not set in ASTNode")
            e.sql_stmt = self.sql_text
            raise e

    # @abstractmethod
    def perform_checks(self):
        raise NotImplementedError()

    def set_sql_text(self, sql_text):
        self.sql_text = sql_text

    def deanonymize_columns(self, columns, table_name):
        for column in columns:
            if table_name:
                if "." not in column.value:
                    column.value = f"{table_name}.{column.value}"

    def check_tables(self, tables):
        """Checks if all tables exist in the schema and checks for duplicates."""
        seen = set()
        for table in tables:
            if table in seen:
                raise PreProcessorError(f"Duplicate table '{table}' found.", word=table)
            if table not in self.table_columns.keys():
                raise PreProcessorError(f"Table '{table}' not found.", word=table)
            seen.add(table)

    def check_column(self, tables, column):
        table_name, col_name = self.split_column(column)
        flag = False
        if len(tables) == 1 and not table_name:
            table_name = tables[0]
            flag = True

        if not table_name:
            raise PreProcessorError(f"Column '{col_name}' must be prefixed(ambiguity error)", word=col_name)

        if table_name not in tables:
            raise PreProcessorError(f"Table '{table_name}' is not specified in 'FROM' clause", word=table_name)

        columns = self.table_columns.get(table_name)
        if not columns:
            raise PreProcessorError(f"Table '{table_name}' not found", word=table_name)
        if col_name not in self.table_columns[table_name]:
            raise PreProcessorError(f"Column '{col_name}' not found in table '{table_name}'", word=col_name)

        if flag:
            return f"{table_name}.{column}"
        return column

    def check_columns(self, tables, columns):
        """Checks if columns exist, checks for duplicates and checks for ambiguity
        If columns are missing table name, they are added in the SQL . format
        """
        seen = []
        for column in columns:
            if column in seen:
                raise PreProcessorError(f"Duplicate column '{column}' found", word=column)

            column = self.check_column(tables, column)

            seen.append(column)
        return seen

    def split_column(self, column):
        """Splits a column name into table and column name, if prefixed with a table."""

        if '.' in column:
            table_name, col_name = column.split('.')
        else:
            table_name = None  # No table prefix
            col_name = column
        return table_name, col_name

    def check_expression(self, tables, where_expr):
        def recurse(node):
            if isinstance(node, Operator):
                node.left = recurse(node.left)
                node.right = recurse(node.right)
                return node

            elif isinstance(node, Identifier):
                column = self.check_column(tables, node.value)
                return column

            elif isinstance(node, Literal):
                return node.value

            return node

        return recurse(where_expr)


class SelectStmt(ASTNode):
    def __init__(self, columns, tables, where_expr, order_by):
        self.columns = columns
        self.tables = tables
        self.where_expr = where_expr
        self.order_by = order_by
        super().__init__()

    def __repr__(self):
        return f"SelectStmt(columns={self.columns}, tables={self.tables}, where={self.where_expr}, order_by={self.order_by})"

    def perform_checks(self):
        self.tables = [table.value for table in self.tables]
        self.columns = [column.value for column in self.columns]
        self.check_tables(self.tables)
        self.columns = self.check_columns(self.tables, self.columns)
        self.where_expr = self.check_expression(self.tables, self.where_expr)
        self.order_by = self.check_order_by()

    def check_order_by(self):
        seen = []
        new_order_by = []
        for element in self.order_by:
            column = self.check_column(self.tables, element[0].value)
            if column in seen:
                raise PreProcessorError(f"Duplicate column '{column}' found", word=column)
            seen.append(column)
            new_order_by.append((column, element[1]))

        return new_order_by


class InsertStmt(ASTNode):
    def __init__(self, table, columns, values):
        self.table = table
        self.columns = columns  # list of column names (or None)
        self.values = values  # list of values
        super().__init__()

    def __repr__(self):
        return f"InsertStmt(table={self.table}, columns={self.columns}, values={self.values})"

    def perform_checks(self):
        if len(self.columns) != len(self.values):
            raise PreProcessorError(f"Columns length({len(self.columns)}) != values length({len(self.values)})")  # , word=unmatched

        self.columns = [column.value for column in self.columns]
        self.table = self.table.value

        tables = [self.table]
        self.check_tables(tables)
        self.columns = self.check_columns(tables, self.columns)

        for col, val in zip(self.columns, self.values):
            expected_type = self.column_types[col]
            constraints = self.column_constraints[col]

            # Nullability check
            if not val.value and any(keyword in constraint.upper() for constraint in constraints for keyword in ('NOT NULL', 'PRIMARY KEY', 'FOREIGN KEY')):
                raise PreProcessorError(f"Column '{col}' cannot be NULL")

            if val.type != 'NULL' and val.type != expected_type:
                raise PreProcessorError(f"Expected type: {expected_type} got: {val} in column: '{col}'")


class CreateStmt(ASTNode):
    def __init__(self, table, columns):
        self.name = table.value
        self.columns = columns  # list of (name, type) pairs
        super().__init__()

    def __repr__(self):
        return f"CreateStmt(table={self.name}, columns={self.columns})"

    def perform_checks(self):
        if self.table_columns.get(self.name):
            raise PreProcessorError(f"ERROR: Table '{self.name}' already exists")
        seen_columns = set()
        primary_key_count = 0
        for col_name, col_type, constraints in self.columns:
            col_name = col_name.value
            # Check for duplicate column names
            if col_name in seen_columns:
                raise PreProcessorError(f"ERROR: Duplicate column name '{col_name}' in table '{self.name}'")
            seen_columns.add(col_name)

            # Count PRIMARY KEY constraints
            if constraints and 'PRIMARY KEY' in constraints:
                primary_key_count += 1

            # Ensure at most one PRIMARY KEY
            if primary_key_count > 1:
                raise PreProcessorError(f"ERROR: Multiple PRIMARY KEY constraints defined for table '{self.name}'")

            # todo check constraitn default value type


class DropStmt(ASTNode):
    def __init__(self, tables):
        self.tables = tables
        super().__init__()

    def __repr__(self):
        return f"DropStmt(tables={self.tables})"

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


class DeleteStmt(ASTNode):
    def __init__(self, table, where):
        self.table = table
        self.where = where
        super().__init__()

    def __repr__(self):
        return f"DeleteStmt(table={self.table}, where={self.where})"

    def verify(self):
        pass


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
