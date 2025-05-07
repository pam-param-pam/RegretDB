class DataManager:
    def __init__(self):
        self.column_constraints = {}
        self.column_types = {}
        self.table_columns = {}
        self.tables = {}

    def get_column_constraints(self):
        return self.column_constraints

    def get_column_types(self):
        return self.column_types

    def get_table_columns(self):
        return self.table_columns

    def add_table_columns(self, table_name, columns):
        self.table_columns[table_name] = columns

    def add_column_types(self, col_types_dict):
        self.column_types.update(col_types_dict)

    def add_column_constraints(self, col_constraints_dict):
        self.column_constraints.update(col_constraints_dict)


data_manager = DataManager()
