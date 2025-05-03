class Column:
    def __init__(self, name, col_type, constraints):
        self.name = name
        self.type = col_type
        self.constraints = constraints

    def __repr__(self):
        return f"Column(name={self.name}, type={self.type}, constraints={self.constraints})"


class Table:
    def __init__(self, name, metadata, data):
        self.name = name
        self.columns = [Column(col['name'], col['type'], col['constraints']) for col in metadata['columns']]
        self.data = data  # List of dicts representing rows

    def get_column_names(self):
        return [col.name for col in self.columns]

    def as_matrix(self):
        """Returns the table as a list-of-tuples matrix, suitable for display."""
        headers = tuple(self.get_column_names())
        rows = [tuple(row[col] for col in headers) for row in self.data]
        return [headers] + rows

    def __repr__(self):
        return f"<Table name={self.name} columns={self.get_column_names()} rows={len(self.data)}>"
