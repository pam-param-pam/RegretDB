from typing import List, Tuple

from ASTNodes.Qualified import QualifiedTable, QualifiedColumn
from DataManager import data_manager
from PlanNodes.BasePlanNode import PlanNode
from utility import indent


class TableScan(PlanNode):
    def __init__(self, table: QualifiedTable):
        self.table = table

    def execute(self):
        return data_manager.get_qualified_rows(self.table.name)

    def __str__(self, level=0):
        return f"TableScan({self.table})"


class Filter(PlanNode):
    def __init__(self, source, condition):
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
        self.headers = None
        self.data = None
        self.source = source

    def execute(self):
        self.data = self.source.execute()
        if self.data:
            self.headers = [h for h in self.data[0].keys()]
        else:
            self.headers = []
        self.visualize_table()
        return self.data

    def __str__(self, level=0):
        return f"Visualize(\n{indent(level)}source={self.source.__str__(level + 1)}\n{indent(level - 1)})"

    def visualize_table(self):
        if not self.data:
            print("\nNo data to display.")
            return

        headers = self.headers
        rows = [[row[h] for h in headers] for row in self.data]

        prefixes = []
        for h in headers:
            if '.' in h:
                prefixes.append(h.split('.')[0])
            else:
                prefixes.append(None)

        if prefixes and all(p == prefixes[0] for p in prefixes) and prefixes[0] is not None:
            stripped_headers = [h.split('.', 1)[1] if '.' in h else h for h in headers]
            display_headers = stripped_headers
        else:
            display_headers = headers

        col_widths = [len(str(display_headers[i])) for i in range(len(display_headers))]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        def divider():
            return '+' + '+'.join(['-' * (w + 2) for w in col_widths]) + '+'

        def format_row(row_data):
            return '| ' + ' | '.join(f"{str(row_data[i]).ljust(col_widths[i])}" for i in range(len(row_data))) + ' |'

        print(f"\nResult: ")
        print(divider())
        print(format_row(display_headers))
        print(divider())
        for row in rows:
            print(format_row(row))
        print(divider())


class Project(PlanNode):
    """This plan filters each row from unneeded columns"""

    def __init__(self, source, columns: List[QualifiedColumn]):
        self.source = source
        self.columns = columns

    def execute(self):
        input_rows = self.source.execute()
        projected_rows = []
        for row in input_rows:
            new_row = {}
            for col in self.columns:
                new_row[col.full_name] = row[col.full_name]
            projected_rows.append(new_row)

        return projected_rows

    def __str__(self, level=0):
        return f"SelectPlan(\n{indent(level)}projection={self.columns},\n{indent(level)}source={self.source.__str__(level + 1)}\n{indent(level - 1)})"


class Sort(PlanNode):
    def __init__(self, source, order_by: List[Tuple[QualifiedColumn, str]]):
        self.source = source
        self.order_by = order_by

    def execute(self):
        rows = self.source.execute()
        for column, direction in reversed(self.order_by):
            reverse = (direction.upper() == 'DESC')

            def sort_key(row):
                val = row.get(column.full_name)
                return val is None, val

            rows.sort(key=sort_key, reverse=reverse)
        return rows

    def __str__(self, level=0):
        return f"SortPlan(\n{indent(level)}keys={self.order_by},\n{indent(level)}source={self.source.__str__(level + 1)}\n{indent(level - 1)})"


class CrossJoin(PlanNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def execute(self):
        """This is an extremely naive and dangerous approach. I would have made it better if I had the time"""

        left_data = self.left.execute()
        right_data = self.right.execute()

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

