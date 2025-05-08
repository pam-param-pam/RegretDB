class ForeignKeyRelationship:
    def __init__(self, referencing_column, referenced_column):
        # Storing columns as fully qualified names like 'table.column'
        self.referencing_column = referencing_column
        self.referenced_column = referenced_column

    def __repr__(self):
        return (f"ForeignKeyRelationship(referencing_column='{self.referencing_column}', "
                f"referenced_column='{self.referenced_column}')")


class ForeignKeyManager:
    def __init__(self):
        self.foreign_keys = []

    def add_foreign_key(self, referencing_column, referenced_column):
        # Add foreign key relationship with fully qualified column names
        relationship = ForeignKeyRelationship(referencing_column, referenced_column)
        self.foreign_keys.append(relationship)

    def get_columns_foreign_keys(self, column):
        # Get all foreign keys where the column is either in the referencing or referenced column
        return [
            fk for fk in self.foreign_keys
            if fk.referencing_column == column or fk.referenced_column == column
        ]

    def check_foreign_key(self, referencing_column, referenced_column):
        # Check if there is a foreign key relationship between two fully qualified columns
        for fk in self.foreign_keys:
            if fk.referencing_column == referencing_column and fk.referenced_column == referenced_column:
                return True
        return False

    def is_table_referenced(self, table_name):
        for fk in self.foreign_keys:
            referenced_table = fk.referenced_column.split('.')[0]
            if referenced_table == table_name:
                return True
        return False

    def __str__(self):
        # Return a human-readable string representation of all foreign key relationships
        if not self.foreign_keys:
            return "No foreign key relationships found."

        fk_str = "\n".join([f"{fk.referencing_column} -> {fk.referenced_column}" for fk in self.foreign_keys])
        return f"ForeignKeyManager:\n{fk_str}"