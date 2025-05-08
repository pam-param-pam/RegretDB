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
        table_data = data_manager.get_tables_data(self.table_name)
        all_columns = data_manager.get_columns_for_table(self.table_name)

        table_constraints = data_manager.get_constraint_for_table(self.table_name)

        for col_name, value in zip(self.columns, self.values):
            value = value.value

            for constraint in table_constraints[col_name]:
                # check if inserted value is unique
                if constraint.type in ['PRIMARY KEY', 'UNIQUE']:
                    if self._check_if_unique(table_data, col_name, value):
                        raise ExecutingError(f"Violation of {constraint} constraint on column {col_name}, it must be unique.")

                if constraint.type == 'FOREIGN KEY':
                    self._validate_foreign_key(constraint, value)

            row[col_name] = value

        # Fill in missing columns with None
        for col in all_columns:
            if col not in row:
                # finding default value if constraint exists
                default_value = None
                for constraint in table_constraints[col]:
                    if constraint.type == 'DEFAULT':
                        default_value = constraint.arg1.value
                row[col] = default_value

        # No violations, safe to insert
        data_manager.insert_row(self.table_name, row)

    def _check_if_unique(self, table, column, value):
        """
        Check if `value` is unique across the table.
        """
        for existing_row in table:
            if existing_row.get(column) == value:
                return True
        return False
