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


file_path = "tables.json"

with open(file_path, 'r') as file:
    json_data = json.load(file)

tables = load_tables_from_json(json_data)
for table in tables:
    table.visualize_metadata()
    table.visualize_table()
