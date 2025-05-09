from abc import ABC, abstractmethod

from DataManager import data_manager
from Exceptions import PreProcessorError, RegretDBError
from Operators.LogicalOperators import Operator
from TokenTypes import Identifier, Literal


class ASTNode(ABC):
    def __init__(self):
        self.sql_text = None

    def verify(self):
        try:
            self.perform_checks()
        except PreProcessorError as e:
            if not self.sql_text:
                raise RegretDBError("sql_text not set in ASTNode")
            e.sql_stmt = self.sql_text
            raise e

    @abstractmethod
    def perform_checks(self):
        raise NotImplementedError()

    @abstractmethod
    def __repr__(self):
        raise NotImplementedError()

    def set_sql_text(self, sql_text):
        self.sql_text = sql_text

    def check_table(self, table):
        if not data_manager.does_table_exist(table):
            raise PreProcessorError(f"Table '{table}' not found.", word=table)

    def check_tables(self, tables):
        """Checks if all tables exist in the schema and checks for duplicates."""
        seen = set()
        for table in tables:
            if table in seen:
                raise PreProcessorError(f"Duplicate table '{table}' found.", word=table)
            self.check_table(table)
            seen.add(table)

    def check_column(self, tables, column):
        """Checks for ambiguity, checks if column's table are specified in the FROM clause, checks if the column exists.
        And it qualified column names"""
        table_name, col_name = self.split_column(column)
        flag = False
        if len(tables) == 1 and not table_name:
            table_name = tables[0]
            flag = True

        if not table_name:
            raise PreProcessorError(f"Column '{col_name}' must be prefixed(ambiguity error)", word=col_name)

        if table_name not in tables:
            raise PreProcessorError(f"Table '{table_name}' is not specified in 'FROM' clause", word=table_name)

        qualified_col_name = f"{table_name}.{col_name}"

        if qualified_col_name not in data_manager.get_columns_for_table(table_name):
            raise PreProcessorError(f"Column '{col_name}' not found in table '{table_name}'", word=col_name)

        if flag:
            return qualified_col_name
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
        """checks all columns and qualifies them"""

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

    def check_type(self, table, column, value):
        """checks type compared the SCHEMA, checks if constraints allow for NULL value"""
        expected_type = data_manager.get_column_types_for_table(table)[column]
        constraints = data_manager.get_constraint_for_table(table)[column]

        # Nullability check
        if not value.value and any(keyword in constraint.type for constraint in constraints for keyword in ('NOT NULL', 'PRIMARY KEY', 'FOREIGN KEY')):
            raise PreProcessorError(f"Column '{column}' cannot be NULL")

        if value.type != 'NULL' and value.type != expected_type:
            raise PreProcessorError(f"Expected type: {expected_type} got: {value} in column: '{column}'")

    def handle_new_column_constraints(self, constraint, col_type, qualified_col_name, table_name):

        if constraint.type == 'DEFAULT':
            # todo move this to a wrapper function later, and clean it up
            default = constraint.arg1
            expected_type = col_type

            if not default.value and constraint.type in ('NOT NULL', 'PRIMARY KEY', 'FOREIGN KEY'):
                raise PreProcessorError(f"Column '{qualified_col_name}' cannot be NULL")

            if default.type != 'NULL' and default.type != expected_type:
                raise PreProcessorError(f"ERROR: INVALID DEFAULT, expected type: {expected_type} got: {default} in column: '{qualified_col_name}'")

        # Handle FOREIGN KEY constraint
        if constraint.type == 'FOREIGN KEY':
            referenced_qualified_col = constraint.arg1

            # Extract referenced table and column
            referenced_table, referenced_column = self.split_column(referenced_qualified_col)

            # Check if the referenced table exists
            if not data_manager.does_table_exist(referenced_table):
                raise PreProcessorError(f"ERROR: Referenced table '{referenced_table}' does not exist in the database")

            # Check if the referenced column exists in the referenced table
            if referenced_qualified_col not in data_manager.get_columns_for_table(referenced_table):
                raise PreProcessorError(f"ERROR: Referenced column '{referenced_column}' does not exist in table '{referenced_table}'")

            # Check if the types match (this assumes both columns have the same type)
            referenced_column_type = data_manager.get_column_types_for_table(referenced_table)[referenced_qualified_col]

            if referenced_column_type != col_type:
                raise PreProcessorError(
                    f"ERROR: Column type mismatch for foreign key: '{qualified_col_name}' in '{table_name}' should match the type of '{referenced_column}' in '{referenced_table}'")

            # Add the foreign key relationship to the manager
            data_manager.foreign_key_manager.add_foreign_key(qualified_col_name, referenced_qualified_col)  # todo this must be moved outside
