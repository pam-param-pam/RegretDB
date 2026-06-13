from ASTNodes.Qualified import QualifiedTable
from DataManager import data_manager
from PlanNodes.BasePlanNode import PlanNode


class Delete(PlanNode):
    def __init__(self, source: PlanNode, table: QualifiedTable):
        self.source = source
        self.table = table

    def execute(self) -> int:
        table_obj = data_manager.get_table(self.table.name)

        rows_to_delete = self.source.execute()

        rowids = [row["_rowid"] for row in rows_to_delete]
        rowids.sort(reverse=True)

        # Delete each row by its index
        for rid in rowids:
            table_obj.delete(rid)

        return len(rowids)
