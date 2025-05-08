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
        if self.table_columns.get(self.name):
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
                if constraint.type == 'DEFAULT':
                    # todo move this to a wrapper function later, and clean it up
                    default = constraint.arg1
                    expected_type = col_type

                    if not default.value and any(keyword in constraint.type for constraint in constraints for keyword in ('NOT NULL', 'PRIMARY KEY', 'FOREIGN KEY')):
                        raise PreProcessorError(f"Column '{qualified_col_name}' cannot be NULL")

                    if default.type != 'NULL' and default.type != expected_type:
                        raise PreProcessorError(f"ERROR: INVALID DEFAULT, expected type: {expected_type} got: {default} in column: '{qualified_col_name}'")

                # Handle FOREIGN KEY constraint
                if constraint.type == 'FOREIGN KEY':
                    referenced_qualified_col = constraint.arg1

                    # Extract referenced table and column
                    referenced_table, referenced_column = self.split_column(referenced_qualified_col)

                    # Check if the referenced table exists
                    if referenced_table not in data_manager.tables:
                        raise PreProcessorError(f"ERROR: Referenced table '{referenced_table}' does not exist in the database")

                    # Check if the referenced column exists in the referenced table
                    if referenced_qualified_col not in data_manager.table_columns[referenced_table]:
                        raise PreProcessorError(f"ERROR: Referenced column '{referenced_column}' does not exist in table '{referenced_table}'")

                    # Check if the types match (this assumes both columns have the same type)
                    referenced_column_type = data_manager.column_types[referenced_qualified_col]

                    if referenced_column_type != col_type:
                        raise PreProcessorError(
                            f"ERROR: Column type mismatch for foreign key: '{col_name}' in '{self.name}' should match the type of '{referenced_column}' in '{referenced_table}'")

                    # Add the foreign key relationship to the manager
                    data_manager.foreign_key_manager.add_foreign_key(qualified_col_name, referenced_qualified_col)

            if primary_key_count > 1:
                raise PreProcessorError(f"ERROR: Multiple PRIMARY KEY constraints defined for table '{self.name}'")

            self.columns[i] = (qualified_col_name, col_type, constraints)
