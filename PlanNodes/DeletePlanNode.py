from PlanNodes.BasePlanNode import PlanNode


class Delete(PlanNode):
    def __init__(self, table, where_expr):
        super().__init__()
        self.table = table
        self.where_expr = where_expr

    def execute(self):
        pass

