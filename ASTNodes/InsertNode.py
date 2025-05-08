from ASTNodes.BaseNode import ASTNode
from DataManager import data_manager
from Exceptions import PreProcessorError


class InsertStmt(ASTNode):
    def __init__(self, table, columns, values):
        self.table = table
        self.columns = columns  # list of column names (or None)
        self.values = values  # list of values
        super().__init__()

    def __repr__(self):
        return f"InsertStmt(table={self.table}, columns={self.columns}, values={self.values})"

    def perform_checks(self):
        # Checking if values are not missing
        if len(self.columns) != len(self.values):
            raise PreProcessorError(f"Columns length({len(self.columns)}) != values length({len(self.values)})")  # , word=unmatched

        # Normalizing table and columns
        self.table = self.table.value
        self.columns = [column.value for column in self.columns]

        self.check_table(self.table)
        tables = [self.table]

        # Checking columns and qualifying them
        self.columns = self.check_columns(tables, self.columns)

        for col, val in zip(self.columns, self.values):
            self.check_type(self.table, col, val)

        # Check for NOT NULL constraint violations on unspecified columns
        table_constraints = data_manager.get_constraint_for_table(self.table)
        for col in data_manager.get_columns_for_table(self.table):
            if col not in self.columns:
                for constraint in table_constraints[col]:
                    if constraint.type == "NOT NULL":
                        raise PreProcessorError(f"ERROR: Column '{col}' must be specified (NOT NULL constraint)")
