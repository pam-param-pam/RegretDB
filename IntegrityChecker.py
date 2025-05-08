from Exceptions import IntegrityError


class IntegrityChecker:
    def __init__(self, data_manager):
        self.data_manager = data_manager

    def check_insert(self, table_name, new_row):
        self._check_not_null(table_name, new_row)
        self._check_unique_constraints(table_name, new_row)
        self._check_foreign_keys_on_insert(table_name, new_row)

    def check_update(self, table_name, updated_row, original_row):
        self._check_not_null(table_name, updated_row)
        self._check_unique_constraints(table_name, updated_row, original_row)
        self._check_foreign_keys_on_update(table_name, updated_row)

    def check_delete(self, table_name, row):
        self._check_foreign_key_references_on_delete(table_name, row)

    def _check_not_null(self, table_name, row):
        constraints = self.data_manager.get_constraint_for_table(table_name)
        for col, cons in constraints.items():
            for c in cons:
                if c.type == 'NOT NULL' and row.get(col) is None:
                    raise IntegrityError(f"Column '{col}' cannot be NULL")

    def _check_unique_constraints(self, table_name, row, exclude_row=None):
        table = self.data_manager.get_tables_data(table_name)
        constraints = self.data_manager.get_constraint_for_table(table_name)
        for col, cons in constraints.items():
            for c in cons:
                if c.type in ('UNIQUE', 'PRIMARY KEY'):
                    for other_row in table:
                        if exclude_row is not None and other_row == exclude_row:
                            continue
                        if other_row.get(col) == row.get(col):
                            raise IntegrityError(f"Duplicate value for {c.type} on column '{col}'")

    def _check_foreign_keys_on_insert(self, table_name, row):
        for fk in self.data_manager.foreign_key_manager.get_foreign_keys(table_name):
            if fk.referencing_column.startswith(table_name + "."):
                ref_value = row.get(fk.referencing_column.split(".")[1])
                if ref_value is None:
                    continue  # allow null foreign keys
                ref_table, ref_col = fk.referenced_column.split(".")
                ref_found = any(
                    r.get(ref_col) == ref_value for r in self.data_manager.get_tables_data(ref_table)
                )
                if not ref_found:
                    raise IntegrityError(f"Foreign key violation: value '{ref_value}' not found in {fk.referenced_column}")

    def _check_foreign_keys_on_update(self, table_name, row):
        self._check_foreign_keys_on_insert(table_name, row)

    def _check_foreign_key_references_on_delete(self, table_name, row):
        for fk in self.data_manager.foreign_key_manager.get_foreign_keys(table_name):
            if fk.referenced_column.startswith(table_name + "."):
                ref_col = fk.referenced_column.split(".")[1]
                ref_val = row.get(ref_col)
                refd_table, refd_col = fk.referencing_column.split(".")
                for ref_row in self.data_manager.get_tables_data(refd_table):
                    if ref_row.get(refd_col) == ref_val:
                        raise IntegrityError(f"Cannot delete '{table_name}' row because it is referenced by '{refd_table}.{refd_col}'")
