from typing import List, Tuple

from ASTNodes.Qualified import QualifiedColumn, QualifiedTable
from DataManager import data_manager
from PlanNodes.BasePlanNode import PlanNode
from TokenTypes import Literal
from utility import indent


class Update(PlanNode):
    def __init__(self, source, assignments: List[Tuple[QualifiedColumn, Literal]], table: QualifiedTable):
        super().__init__()
        self.source = source
        self.assignments = assignments
        self.table = table

    def execute(self) -> int:
        table_obj = data_manager.get_table(self.table.name)

        rows = self.source.execute()
        if not rows:
            return 0

        # Convert assignments to a dictionary of (unqualified column name -> new value)
        updates = {}
        for qcol, lit in self.assignments:
            updates[qcol.column] = lit.value

        updated_count = 0
        for row in rows:
            row_id = row['_rowid']
            table_obj.update(row_id, updates)
            updated_count += 1

        return updated_count

    def __str__(self, level=0) -> str:
        return f"UpdatePlan(\n{indent(level)}assignments={self.assignments},\n{indent(level)}source={self.source.__str__(level + 1)}\n{indent(level - 1)})"
