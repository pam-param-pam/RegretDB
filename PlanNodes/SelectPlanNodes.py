from DataManager import data_manager
from PlanNodes.BasePlanNode import PlanNode
from utility import indent


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
