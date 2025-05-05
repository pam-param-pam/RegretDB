import csv
import json

from LALR import Parser


# Things that will NOT be supported:
# JOINS, FUNCTIONS, SUB-QUERIES, DATA SIZE (e.g VARCHAR(100))
# Statement optimizations, indexes
# It supports only 1 process, it won't detect metadata changes happening outside the process

class RegretDB:
    def __init__(self, metadata_file='metadata.json', data_directory='data'):
        self.metadata_file = metadata_file
        self.data_directory = data_directory
        self.metadata = self.load_metadata()
        self.parser = None
        self.statement = None

    def execute_order_66(self, sql_stmt):
        self.parser = Parser(sql_stmt)
        self.statement = self.parser.parse()
        print(self.statement)
        self.statement.verify(sql_stmt, self.metadata)

    def load_metadata(self):
        with open(self.metadata_file, 'r') as file:
            metadata = json.load(file)
            tables = metadata.get("tables", {})

            table_columns = {}
            column_types = {}
            column_constraints = {}

            for table_name, table_data in tables.items():
                columns = table_data.get("columns", [])
                column_names = []

                for column in columns:
                    col_name = column["name"]
                    qualified_col = f"{table_name}.{col_name}"
                    column_names.append(col_name)

                    column_types[qualified_col] = column["type"]
                    column_constraints[qualified_col] = column.get("constraints", [])

                table_columns[table_name] = column_names

            return table_columns, column_types, column_constraints

    def load_table_metadata(self, table_name):
        if table_name in self.metadata['tables']:
            return self.metadata['tables'][table_name]['metadata']
        else:
            raise ValueError(f"Table '{table_name}' not found in metadata.")

    def load_table_data(self, table_name):
        table_file = f"{self.data_directory}/{table_name}.csv"
        with open(table_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            table_data = [row for row in reader]
        return table_data

    def save_table_data(self, table_name, data):
        table_file = f"{self.data_directory}/{table_name}.csv"
        with open(table_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)


# Example usage:
db_engine = RegretDB()

db_engine.execute_order_66("SELECT users.id, orders.amount FROM users WHERE (orders.amount > 100 and ala = 'name') or (orders.amount > 200 and ala = 'amount') ORDER BY orders.amount ASC, orders.name DESC")




