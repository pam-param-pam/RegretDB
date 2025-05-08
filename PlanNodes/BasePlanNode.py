from DataManager import data_manager
from Exceptions import IntegrityError


class PlanNode:
    def __init__(self):
        pass

    def execute(self):
        raise NotImplementedError()

    def _validate_foreign_key(self, constraint, value):
        referenced_col = constraint.arg1
        ref_table, ref_col = referenced_col.split(".")

        # # Allow NULLs
        # if value is None:
        #     return todo

        found = False
        for row in data_manager.get_tables_data(ref_table):
            if row.get(referenced_col) == value:
                found = True

        if not found:
            raise IntegrityError(f"Violation of FOREIGN KEY constraint: no matching value in {referenced_col} for {value}")
