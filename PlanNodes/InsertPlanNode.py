from typing import List

from ASTNodes.Qualified import QualifiedTable, QualifiedColumn
from DataManager import data_manager
from Exceptions import ExecutingError
from PlanNodes.BasePlanNode import PlanNode


from Exceptions import IntegrityError
from TokenTypes import Literal


class Insert(PlanNode):
    def __init__(self, table: QualifiedTable, columns: List[QualifiedColumn], values: List[Literal]):
        self.table = table
        self.columns = columns
        self.values = values

    def __str__(self):
        return f"Insert(table={self.table}, columns={self.columns}, values={self.values})"

    def execute(self):
        table_name = self.table.name
        table_obj = data_manager.get_table(table_name)

        row = {}
        for qcol, val_literal in zip(self.columns, self.values):
            col_name = qcol.column
            row[col_name] = val_literal.value

        try:
            table_obj.insert(row)
        except IntegrityError as e:
            raise ExecutingError(f"Insert failed: {e}") from e
