
class Update(PlanNode):
    def __init__(self, source, assignments, table_name):
        super().__init__()
        self.source = source
        self.assignments = assignments  # list of (column, new_value)
        self.table_name = table_name

    def execute(self):
        rows = self.source.execute()
        table = data_manager.tables[self.table_name]
        constraints = data_manager.column_constraints.get(self.table_name, {})

        updated_rows = []

        for row in rows:
            original_row = row.copy()
            updated_row = row.copy()

            # Apply assignments
            for column, new_value in self.assignments:
                updated_row[column.value] = new_value.value

            # Check uniqueness constraints
            for constraint in data_manager.table_constraints.get(self.table_name, []):
                if constraint.type in ("PRIMARY KEY", "UNIQUE"):
                    if self._violates_unique_constraint(constraint, updated_row, table, original_row):
                        raise ExecutingError(
                            f"Update violates {constraint.type} constraint on columns {', '.join(constraint.columns)}"
                        )

            # Check foreign key constraints
            for constraint in data_manager.table_constraints.get(self.table_name, []):
                if constraint.type == "FOREIGN KEY":
                    # If the updated columns include the foreign key column, check for referential integrity
                    if any(col in updated_row for col in constraint.columns):
                        self._validate_foreign_key(constraint, updated_row)

            updated_rows.append(updated_row)

        # Apply updates back to table
        for i, row in enumerate(rows):
            idx = table.index(row)
            table[idx] = updated_rows[i]

        return []

    def _violates_unique_constraint(self, constraint, new_row, table, original_row):
        for existing_row in table:
            if existing_row == original_row:
                continue  # skip self
            if all(existing_row[col] == new_row[col] for col in constraint.columns):
                return True
        return False

    def _validate_foreign_key(self, constraint, row):
        ref_table = constraint.references_table
        ref_columns = constraint.references_columns
        fk_values = [row.get(col) for col in constraint.columns]

        if None in fk_values:
            return  # allow nulls in foreign keys

        found = any(
            all(existing_row.get(ref_col) == val for ref_col, val in zip(ref_columns, fk_values))
            for existing_row in data_manager.tables[ref_table]
        )

        if not found:
            raise ExecutingError(
                f"Update violates FOREIGN KEY constraint: no matching row in {ref_table} for values {fk_values}"
            )

    def __str__(self, level=0):
        return f"UpdatePlan(\n{indent(level)}assignments={self.assignments},\n{indent(level)}source={self.source.__str__(level + 1)}\n{indent(level - 1)})"


