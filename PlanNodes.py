class PlanNode:
    def execute(self):
        raise NotImplementedError()


class TableScan(PlanNode):
    def __init__(self, table):
        self.table = table

    def execute(self):
        pass


class Filter(PlanNode):
    def __init__(self, source, condition):
        self.source = source
        self.condition = condition

    def execute(self):
        # filter rows from self.source.execute()
        pass


class Project(PlanNode):
    def __init__(self, source, columns):
        self.source = source
        self.columns = columns

    def execute(self):
        # return only selected columns
        pass


class Sort(PlanNode):
    def __init__(self, source, order_by):
        self.source = source
        self.order_by = order_by

    def execute(self):
        # return rows sorted by order_by
        pass

class Insert(PlanNode):
    def __init__(self, table, columns, values):
        self.table = table
        self.columns = columns
        self.values = values

    def execute(self):
        pass

class Delete(PlanNode):
    def __init__(self, table, where_expr):
        self.table = table
        self.where_expr = where_expr

    def execute(self):
        pass

class CreateTable(PlanNode):
    def __init__(self, db, name, columns):
        self.db = db
        self.name = name
        self.columns = columns  # List of (name, type, constraints)

    def execute(self):
        pass

class DropTable(PlanNode):
    def __init__(self, db, table_name):
        self.db = db
        self.table_name = table_name

    def execute(self):
        pass


class AlterTable(PlanNode):
    def __init__(self, db, table_name, action, details):
        self.db = db
        self.table_name = table_name
        self.action = action  # 'ADD', 'DROP', 'RENAME', 'MODIFY'
        self.details = details

    def execute(self):
        pass

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

