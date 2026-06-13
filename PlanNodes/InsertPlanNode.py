from typing import List

from ASTNodes.Qualified import QualifiedTable, QualifiedColumn
from DataManager import data_manager
from Exceptions import ExecutingError
from PlanNodes.BasePlanNode import PlanNode


from Exceptions import IntegrityError
from TokenTypes import Literal


class Insert(PlanNode):
    def __init__(self, table: QualifiedTable, columns: List[QualifiedColumn], values: List[Literal]):
        self.table = table          # QualifiedTable object
        self.columns = columns      # List of QualifiedColumn objects
        self.values = values        # List of Literal nodes

    def execute(self):
        table_name = self.table.name   # extract string name
        table_obj = data_manager.get_table(table_name)

        # Build row dictionary: column name -> value
        row = {}
        for qcol, val_literal in zip(self.columns, self.values):
            col_name = qcol.column
            row[col_name] = val_literal.value

        # Insert the row (this performs all checks: NOT NULL, UNIQUE, PK, FK, defaults)
        try:
            table_obj.insert(row)
        except IntegrityError as e:
            # Re-raise with a user-friendly message (or let it propagate)
            raise ExecutingError(f"Insert failed: {e}") from e
