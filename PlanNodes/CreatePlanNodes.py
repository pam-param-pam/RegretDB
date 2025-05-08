from DataManager import data_manager
from PlanNodes.BasePlanNode import PlanNode


class CreateTable(PlanNode):
    def __init__(self, name, columns):
        super().__init__()
        self.name = name
        self.columns = columns

    def execute(self):
        col_types = {col[0]: col[1] for col in self.columns}
        col_constraints = {col[0]: col[2] for col in self.columns}

        data_manager.add_table(self.name)
        data_manager.add_column_types(self.name, col_types)
        data_manager.add_column_constraints(self.name, col_constraints)
