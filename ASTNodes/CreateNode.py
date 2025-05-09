from ASTNodes.BaseNode import ASTNode
from DataManager import data_manager
from Exceptions import PreProcessorError


class CreateStmt(ASTNode):
    def __init__(self, table, columns):
        self.name = table.value
        self.columns = columns  # list of (name, type) pairs
        super().__init__()

    def __repr__(self):
        return f"CreateStmt(table={self.name}, columns={self.columns})"

    def perform_checks(self):
        # STEP 1. Verify a table doesn't already exist
        if data_manager.does_table_exist(self.name):
            raise PreProcessorError(f"ERROR: Table '{self.name}' already exists")

        seen_columns = set()
        primary_key_count = 0

        # STEP 2. Validate columns, constraints and col types
        for i, (col_name, col_type, constraints) in enumerate(self.columns):
            # Normalizing from Identifier to a str
            col_name = col_name.value

            # Checking for column name duplicates
            if col_name in seen_columns:
                raise PreProcessorError(f"ERROR: Duplicate column name '{col_name}' in table '{self.name}'")
            seen_columns.add(col_name)

            # qualifying the name
            qualified_col_name = f"{self.name}.{col_name}"

            # Check constraints
            for constraint in constraints:
                if constraint.type == 'PRIMARY KEY':
                    primary_key_count += 1

                self.handle_new_column_constraints(constraint, col_type, qualified_col_name, self.name)

            if primary_key_count > 1:
                raise PreProcessorError(f"ERROR: Multiple PRIMARY KEY constraints defined for table '{self.name}'")

            self.columns[i] = (qualified_col_name, col_type, constraints)
