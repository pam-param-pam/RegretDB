from DataManager import data_manager
from Exceptions import ExecutingError
from PlanNodes.BasePlanNode import PlanNode


class Insert(PlanNode):
    def __init__(self, table_name, columns, values):
        super().__init__()
        self.table_name = table_name
        self.values = values
        self.columns = columns

    def execute(self):
        # Build row as dictionary {col_name: value}
        row = {}
        table = data_manager.tables[self.table_name]
        schema = data_manager.table_columns[self.table_name]  # List of fully qualified column names

        for col_name, value in zip(self.columns, self.values):
            col_key = col_name  # already fully qualified like 'users.id'
            row[col_key] = value.value  # assign early for check to access

            constraints = data_manager.column_constraints[col_key]

            for constraint in constraints:
                # check if inserted row is unique
                if constraint.type in ['PRIMARY KEY', 'UNIQUE']:
                    if self._check_unique_constraint(table, col_key, value.value):
                        raise ExecutingError(f"Violation of {constraint} constraint on column {col_key}")

        # Fill in missing columns with None
        for col in schema:
            if col not in row:
                # finding default value if constraint exists
                default_value = None
                constraints = data_manager.column_constraints.get(col)
                for constraint in constraints:
                    if constraint.type == 'DEFAULT':
                        default_value = constraint.arg1.value
                row[col] = default_value

        # No violations, safe to insert
        table = data_manager.tables[self.table_name]
        table.append(row)

    def _check_unique_constraint(self, table, column, value):
        """
        Check if `value` already exists in `column` for any row in `table`.
        """
        for existing_row in table:
            if existing_row.get(column) == value:
                return True
        return False
