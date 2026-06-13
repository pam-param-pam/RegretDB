from PlanNodes.BasePlanNode import PlanNode


class AlterTable(PlanNode):
    def __init__(self, table_name, action, details):
        self.table_name = table_name
        self.action = action  # 'ADD', 'DROP', 'RENAME', 'MODIFY'
        self.details = details

    def execute(self):
        pass
        # todo, oh lol i never finioshed it XD
