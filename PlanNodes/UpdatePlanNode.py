from DataManager import data_manager
from Exceptions import ExecutingError
from PlanNodes.BasePlanNode import PlanNode
from utility import indent


class Update(PlanNode):
    def __init__(self, source, assignments, table_name):
        super().__init__()
        self.source = source
        self.assignments = assignments  # list of (column, new_value)
        self.table_name = table_name

    def execute(self):
        rows = self.source.execute()
        table = data_manager.get_tables_data(self.table_name)
        constraints = data_manager.get_constraint_for_table(self.table_name)

        updated_rows = []

        for row in rows:
            original_row = row.copy()
            updated_row = row.copy()

            for column, new_value in self.assignments:
                old_value = original_row[column]

                # Apply assignments
                updated_row[column] = new_value

                for constraint in constraints[column]:
                    # checks uniqueness
                    if constraint.type in ("PRIMARY KEY", "UNIQUE"):
                        if self._violates_unique_constraint(column, updated_row, table, updated_rows, original_row):
                            raise ExecutingError(f"Update violates {constraint.type} constraint on column {column}")

                    # checks if foreign key blocks the update
                    if constraint.type == "FOREIGN KEY" and column in updated_row:
                        self._validate_foreign_key(constraint, updated_row[column])

                for fk in data_manager.foreign_key_manager.get_columns_foreign_keys(column):
                    # Someone else points to this column
                    ref_table, ref_col = fk.referencing_column.split(".")
                    referencing_rows = data_manager.get_tables_data(ref_table)

                    for r in referencing_rows:
                        if r.get(column) == old_value:
                            raise ExecutingError(f"Cannot update '{column}' from {old_value} to {new_value}: it is referenced in '{r}'")

            updated_rows.append(updated_row)

        # Apply updates to the actual table
        for i, row in enumerate(rows):
            idx = table.index(row)
            table[idx] = updated_rows[i]

    def _violates_unique_constraint(self, col, new_row, table, updated_rows, original_row):
        for existing_row in table:
            if existing_row == original_row:
                continue  # skip self
            if existing_row.get(col) == new_row.get(col):
                return True
        for new_updated_row in updated_rows:
            if new_updated_row.get(col) == new_row.get(col):
                return True

        return False

    def __str__(self, level=0):
        return f"UpdatePlan(\n{indent(level)}assignments={self.assignments},\n{indent(level)}source={self.source.__str__(level + 1)}\n{indent(level - 1)})"
