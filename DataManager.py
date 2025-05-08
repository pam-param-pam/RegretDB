from ForeignKeyManager import ForeignKeyManager

"""
How data is stored:

self.tables = {
    'table_name1': [
        {'col1': value1, 'col2': value2, ...},  # Row 1
        {'col1': value3, 'col2': value4, ...},  # Row 2
        ...
    ],
    'table_name2': [
        {'col1': value5, 'col2': value6, ...},  # Row 1
        {'col1': value7, 'col2': value8, ...},  # Row 2
        ...
    ]
    ...
}


self.column_constraints = {
    'table_name1': {
        'col1': [Constraint1, Constraint2, ...],
        'col2': [Constraint3, Constraint4, ...],
        ...
    },
    'table_name2': {
        'col3': [Constraint5, Constraint6, ...],
        'col4': [Constraint7, Constraint8, ...],
        ...
    }
    ...
}


self.column_types = {
    'table_name1': {
        'col1': 'type1',
        'col2': 'type2',
        ...
    },
    'table_name2': {
        'col3': 'type3',
        'col4': 'type4',
        ...
    }
    ...
}

"""
class DataManager:
    def __init__(self):
        self.column_constraints = {}
        self.column_types = {}
        self.table_columns = {}
        self.tables = {}
        self.foreign_key_manager = ForeignKeyManager()

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
