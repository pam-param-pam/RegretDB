from DataManager import data_manager


class PlanNode:
    def __init__(self):
        self.column_constraints = data_manager.get_column_constraints()
        self.column_types = data_manager.get_column_types()
        self.table_columns = data_manager.get_table_columns()

    def execute(self):
        raise NotImplementedError()