from DataManager import data_manager
from PlanNodes.BasePlanNode import PlanNode


class DropTable(PlanNode):
    def __init__(self, table):
        super().__init__()
        self.table = table

    def execute(self):
        data_manager.drop_table(self.table)

    def __str__(self):
        return f"DropTablePlan(table={self.table})"
