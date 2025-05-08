from DataManager import data_manager
from Exceptions import ExecutingError
from PlanNodes.BasePlanNode import PlanNode


class Delete(PlanNode):
    def __init__(self, source, table, where_expr):
        super().__init__()
        self.source = source
        self.table_name = table
        self.where_expr = where_expr

    def execute(self):
        rows = self.source.execute()
        deleted_rows = []

        for row in rows:
            for column, value in row.items():
                referencing_fks = data_manager.foreign_key_manager.get_foreign_keys_referencing(column)
                for fk in referencing_fks:
                    ref_col_full = fk.referencing_column
                    ref_table, ref_col = ref_col_full.split(".")
                    referencing_rows = data_manager.get_tables_data(ref_table)
                    for r in referencing_rows:
                        if r.get(ref_col_full) == value:
                            raise ExecutingError(f"Cannot delete row {row}: it is referenced by {r}")

            deleted_rows.append(row)

        # Actually remove the rows
        table_data = data_manager.get_tables_data(self.table_name)
        for row in deleted_rows:
            table_data.remove(row)

        return deleted_rows
