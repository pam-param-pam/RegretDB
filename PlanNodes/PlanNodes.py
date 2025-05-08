from DataManager import data_manager
from Exceptions import ExecutingError
from PlanNodes.BasePlanNode import PlanNode
from utility import indent





# class Delete(PlanNode):
#     def __init__(self, table, where_expr):
#         self.table = table
#         self.where_expr = where_expr
#
#     def execute(self, db):
#         pass
#


#
# class AlterTable(PlanNode):
#     def __init__(self, db, table_name, action, details):
#         self.db = db
#         self.table_name = table_name
#         self.action = action  # 'ADD', 'DROP', 'RENAME', 'MODIFY'
#         self.details = details
#
#     def execute(self, db):
#         pass


# TableScan('users').execute()

# plan = CrossJoin(left=TableScan('users'), right=TableScan('orders'))
# plan.execute()



"""
SelectPlan(
    projection=['users.id', 'orders.amount'],
    source=SortPlan(
        keys=[('orders.amount', 'ASC'), ('orders.name', 'DESC')],
        source=FilterPlan(
            condition=Or(
                And(Gt('orders.amount', 100), Eq('ala', 'name')),
                And(Gt('orders.amount', 200), Eq('ala', 'name1'))
            ),
            source=TableScan('users')
        )
    )
)

InsertPlan(
    table='Customers',
    columns=['CustomerName', 'ContactName', 'Address', 'City', 'Country'],
    values=['Cardinal', 'Tom B. Erichsen', 'Skagen 21', 'Stavanger', '4006', 'Norway']
)

UpdatePlan(
    table='users',
    assignments={'name': 'Alice Smith', 'email': 'alice.smith@example.com'},
    condition=('AND', ('IS NOT', 'id', None), ('=', 'name', '1'))
)

DeletePlan(
    table='users',
    condition=('<', 'age', 18)
)

CreateTablePlan(
    table='users',
    columns=[
        ColumnDef('id', 'NUMBER', ['PRIMARY KEY']),
        ColumnDef('name', 'TEXT', ['NOT NULL', 'UNIQUE']),
        ColumnDef('email', 'TEXT', ['NOT NULL', 'UNIQUE']),
        ColumnDef('age', 'NUMBER', ['DEFAULT 1']),
    ]
)

DropTablePlan(table='users')

AlterTablePlan(
    table='employees',
    action='ADD',
    details=ColumnDef('department', 'TEXT', ['NOT NULL', 'PRIMARY KEY', 'UNIQUE', 'FOREIGN KEY', "DEFAULT '1'"])
)

AlterTablePlan(
    table='employees',
    action='DROP',
    details={'column': 'salary', 'cascade': 'CASCADE1'}
)
"""
