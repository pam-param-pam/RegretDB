import json

from Table import Table


def load_tables_from_json(json_data):
    """
    Converts the JSON structure into a memory structure.
    """
    tables = []

    for table_name, table_data in json_data["tables"].items():
        columns = table_data["metadata"]["columns"]
        rows = [tuple(row.values()) for row in table_data["data"]]
        table = Table(table_name, columns, rows)

        tables.append(table)

    return tables


def visualize_table(tables):
    """
    Displays each table in a human-readable format.
    """
    for table_name, table in tables.items():
        columns = table[0]
        rows = table[1:]

        col_widths = [len(col) for col in columns]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        def divider():
            return '+' + '+'.join(['-' * (w + 2) for w in col_widths]) + '+'

        def format_row(row_data):
            return '| ' + ' | '.join(f"{str(val).ljust(col_widths[i])}" for i, val in enumerate(row_data)) + ' |'

        print(f"\nTable: {table_name}")
        print(divider())
        print(format_row(columns))
        print(divider())
        for row in rows:
            print(format_row(row))
        print(divider())


file_path = "tables.json"

with open(file_path, 'r') as file:
    json_data = json.load(file)

tables = load_tables_from_json(json_data)
for table in tables:
    table.visualize_metadata()

