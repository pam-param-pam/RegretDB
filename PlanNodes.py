from DataManager import data_manager
from Exceptions import ExecutingError
from utility import indent


class PlanNode:
    def __init__(self):
        self.column_constraints = data_manager.get_column_constraints()
        self.column_types = data_manager.get_column_types()
        self.table_columns = data_manager.get_table_columns()

    def execute(self):
        raise NotImplementedError()

class CreateTable(PlanNode):
    def __init__(self, name, columns):
        super().__init__()
        self.name = name
        self.columns = columns

    def execute(self):

        col_names = [col[0].value for col in self.columns]
        col_types = {f"{self.name}.{col[0].value}": col[1] for col in self.columns}
        col_constraints = {
            f"{self.name}.{col[0].value}": col[2]
            for col in self.columns
        }

        data_manager.add_table_columns(self.name, col_names)
        data_manager.add_column_types(col_types)
        data_manager.add_column_constraints(col_constraints)

        data_manager.tables[self.name] = []

class Insert(PlanNode):
    def __init__(self, table_name, columns, values):
        super().__init__()
        self.table_name = table_name
        self.values = values
        self.columns = columns

    def execute(self):
        # Build row as dictionary {col_name: value}
        row = {}
        table = data_manager.tables[self.table_name]

        for col_name, value in zip(self.columns, self.values):
            col_key = col_name  # already fully qualified like 'users.id'
            row[col_key] = value.value  # assign early for check to access

            constraints = data_manager.column_constraints[col_key]

            print(constraints)
            for constraint in constraints:
                if constraint in ['PRIMARY KEY', 'UNIQUE']:
                    if self._check_unique_constraint(table, col_key, value.value):
                        raise ExecutingError(f"Violation of {constraint} constraint on column {col_key}")

        # No violations, safe to insert
        table = data_manager.tables[self.table_name]
        table.append(row)

    def _check_unique_constraint(self, table, column, value):
        """
        Check if `value` already exists in `column` for any row in `table`.
        """
        for existing_row in table:
            print(existing_row)

            if existing_row.get(column) == value:
                return True
        return False

class TableScan(PlanNode):
    def __init__(self, table):
        super().__init__()
        self.table = table

    def execute(self):
        return data_manager.tables[self.table]

    def __str__(self, level=0):
        return f"TableScan('{self.table}')"


class Filter(PlanNode):
    def __init__(self, source, condition):
        super().__init__()
        self.source = source
        self.condition = condition

    def execute(self):
        filtered_rows = []
        for row in self.source.execute():
            if self.condition.execute(row):
                filtered_rows.append(row)
        return filtered_rows

    def __str__(self, level=0):
        return f"FilterPlan(\n{indent(level)}condition={self.condition},\n{indent(level)}source={self.source.__str__(level + 1)}\n{indent(level - 1)})"

class Visualize(PlanNode):
    def __init__(self, source):
        super().__init__()
        self.headers = None
        self.data = None
        self.source = source

    def execute(self):
        self.data = self.source.execute()
        if self.data:
            self.headers = list(self.data[0].keys())
        else:
            self.headers = []
        self.visualize_table()
        return self.data

    def __str__(self, level=0):
        return f"Visualize(\n{indent(level)}source={self.source.__str__(level + 1)}\n{indent(level - 1)})"

    def visualize_table(self):
        """
        Displays the table data in a readable tabular format.
        """
        if not self.data:
            print("\nNo data to display.")
            return

        headers = self.headers
        rows = [[row[h] for h in headers] for row in self.data]

        # Determine column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        def divider():
            return '+' + '+'.join(['-' * (w + 2) for w in col_widths]) + '+'

        def format_row(row_data):
            return '| ' + ' | '.join(f"{str(row_data[i]).ljust(col_widths[i])}" for i in range(len(row_data))) + ' |'

        print(f"\nResult: ")
        print(divider())
        print(format_row(headers))
        print(divider())
        for row in rows:
            print(format_row(row))
        print(divider())

class Project(PlanNode):
    """This plan filters each row from unneeded columns"""
    def __init__(self, source, columns):
        super().__init__()
        self.source = source
        self.columns = columns

    def execute(self):
        input_rows = self.source.execute()
        projected_rows = []
        for row in input_rows:
            new_row = {}
            for col in self.columns:
                new_row[col] = row[col]
            projected_rows.append(new_row)

        return projected_rows

    def __str__(self, level=0):
        return f"SelectPlan(\n{indent(level)}projection={self.columns},\n{indent(level)}source={self.source.__str__(level + 1)}\n{indent(level - 1)})"


class Sort(PlanNode):
    def __init__(self, source, order_by):
        super().__init__()
        self.source = source
        self.order_by = order_by

    def execute(self):
        rows = self.source.execute()

        for column, direction in reversed(self.order_by):
            reverse = direction.upper() == 'DESC'

            def sort_key(row):
                value = row.get(column)
                # Put None at the end for ASC, at the start for DESC
                return (value is None, value) if not reverse else (value is not None, value)

            rows.sort(key=sort_key, reverse=False)  # reverse handled in key
        return rows

    def __str__(self, level=0):
        return f"SortPlan(\n{indent(level)}keys={self.order_by},\n{indent(level)}source={self.source.__str__(level + 1)}\n{indent(level - 1)})"


class CrossJoin(PlanNode):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

    def execute(self):
        """Performs a Cartesian product (cross join) between the left and right sources."""
        left_data = self.left.execute()  # Get data from the left source
        right_data = self.right.execute()  # Get data from the right source

        # Perform cross join (Cartesian product)
        result = []
        for left_row in left_data:
            for right_row in right_data:
                # Combine the rows from left and right into one row (merged)
                merged_row = {**left_row, **right_row}
                result.append(merged_row)
        return result

    def __str__(self, level=0):
        return f"CrossJoinPlan(\n{indent(level)}left={self.left},\n{indent(level)}right={self.right}\n{indent(level - 1)})"


# class Insert(PlanNode):
#     def __init__(self, table, columns, values):
#         self.table = table
#         self.columns = columns
#         self.values = values
#
#     def execute(self, db):
#         pass
#
#
# class Delete(PlanNode):
#     def __init__(self, table, where_expr):
#         self.table = table
#         self.where_expr = where_expr
#
#     def execute(self, db):
#         pass
#
#

#
#
# class DropTable(PlanNode):
#     def __init__(self, db, table_name):
#         self.db = db
#         self.table_name = table_name
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
