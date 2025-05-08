from ASTNodes.BaseNode import ASTNode
from DataManager import data_manager
from Exceptions import PreProcessorError


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
        # Normalizing table and columns
        self.tables = [table.value for table in self.tables]
        self.columns = [column.value for column in self.columns]

        self.check_tables(self.tables)

        # expanding *
        expanded_columns = []
        for col in self.columns:
            if col == '*':
                for table in self.tables:
                    expanded_columns.extend([col_name for col_name in data_manager.get_columns_for_table(table)])
            elif col.endswith('.*'):
                table_name = col[:-2]
                self.check_table(table_name)
                expanded_columns.extend([col_name for col_name in data_manager.get_columns_for_table(table_name)])
            else:
                PreProcessorError(f"Unable to expand: {col}")

        self.columns = expanded_columns

        # Checking columns and qualifying them
        self.columns = self.check_columns(self.tables, self.columns)

        # Checking the expression and qualifying column names in the where expr
        if self.where_expr:
            self.where_expr = self.check_expression(self.tables, self.where_expr)

        # Checking the expression and qualifying column names in the order by expr
        if self.order_by:
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
