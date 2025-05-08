class DropTable(PlanNode):
    def __init__(self, table):
        super().__init__()
        self.table = table

    def execute(self):
        # Remove the table from the data manager's tables
        if self.table in data_manager.tables:
            del data_manager.tables[self.table]  # Remove the table from tables

        # Remove the column types for the table from column_types
        if self.table in data_manager.column_types:
            del data_manager.column_types[self.table]  # Remove the table's column types

        # Remove any constraints related to the table
        print(data_manager.column_constraints)
        if self.table in data_manager.constraints:
            del data_manager.constraints[self.table]  # Remove the table's constraints

        # If foreign key relationships exist for the table, remove them
        for fk in data_manager.foreign_key_manager.foreign_keys[:]:
            if fk.referencing_table == self.table or fk.referenced_table == self.table:
                data_manager.foreign_key_manager.foreign_keys.remove(fk)

        # Return success or relevant message
        print(f"Table '{self.table}' and all related data (columns, constraints, foreign keys) have been dropped.")

    def __str__(self):
        return f"DropTablePlan(table={self.table})"