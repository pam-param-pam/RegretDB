class Column:
    def __init__(self, name, col_type, constraints):
        self.name = name
        self.type = col_type
        self.constraints = constraints

    def __repr__(self):
        return f"Column(name={self.name}, type={self.type}, constraints={self.constraints})"


class Table:
    def __init__(self, name, columns, data):
        self.name = name
        self.columns = [Column(col['name'], col['type'], col['constraints']) for col in columns]
        self.data = data

    def get_column_names(self):
        return [col.name for col in self.columns]

    def as_matrix(self):
        """Returns the table as a list-of-tuples matrix, suitable for display."""
        headers = tuple(self.get_column_names())
        rows = [tuple(row[col] for col in headers) for row in self.data]
        return [headers] + rows

    def visualize_metadata(self):
        print(f"\nMetadata for Table: {self.name}")

        headers = ["Column Name", "Type", "Constraints"]
        rows = [(col.name, col.type, ', '.join(col.constraints)) for col in self.columns]

        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        def divider():
            return '+' + '+'.join(['-' * (w + 2) for w in col_widths]) + '+'

        def format_row(row_data):
            return '| ' + ' | '.join(f"{str(val).ljust(col_widths[i])}" for i, val in enumerate(row_data)) + ' |'

        print(divider())
        print(format_row(headers))
        print(divider())
        for row in rows:
            print(format_row(row))
        print(divider())

    def visualize_table(self):
        """
        Displays the table data in a readable tabular format.
        """
        headers = self.get_column_names()
        rows = self.data

        # Determine column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        def divider():
            return '+' + '+'.join(['-' * (w + 2) for w in col_widths]) + '+'

        def format_row(row_data):
            return '| ' + ' | '.join(f"{str(row_data[i]).ljust(col_widths[i])}" for i in range(len(row_data))) + ' |'

        print(f"\nTable: {self.name}")
        print(divider())
        print(format_row(headers))
        print(divider())
        for row in rows:
            print(format_row(row))
        print(divider())

    def __repr__(self):
        return f"<Table name={self.name} columns={self.get_column_names()} rows={len(self.data)}>"
