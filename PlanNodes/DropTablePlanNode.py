from ASTNodes.Qualified import QualifiedTable
from DataManager import data_manager
from PlanNodes.BasePlanNode import PlanNode


class DropTable(PlanNode):
    def __init__(self, table: QualifiedTable):
        self.table = table

    def __str__(self):
        return f"DropTable(table={self.table})"

    def execute(self):
        data_manager.drop_table(self.table.name)
