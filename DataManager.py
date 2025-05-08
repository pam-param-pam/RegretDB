from Exceptions import IntegrityError
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
        self.__column_constraints = {}
        self.__column_types = {}
        self.__table_data = {}
        self.foreign_key_manager = ForeignKeyManager()

    def does_table_exist(self, table_name):
        if self.__column_types.get(table_name):
            return True
        return False

    def get_columns_for_table(self, table_name):
        return self.__column_types[table_name].keys()

    def get_constraint_for_table(self, table_name):
        return self.__column_constraints[table_name]

    def get_column_types_for_table(self, table_name):
        return self.__column_types[table_name]

    def get_tables_data(self, table_name):
        return self.__table_data[table_name]

    def insert_row(self, table_name, row):
        self.__table_data[table_name].append(row)

    # SETTERS
    def add_table(self, table_name):
        self.__table_data[table_name] = []

    def add_column_types(self, table_name, col_types):
        self.__column_types[table_name] = col_types

    def add_column_constraints(self, table_name, col_constraints):
        self.__column_constraints[table_name] = col_constraints

    def drop_table(self, table_name):
        # if self.foreign_key_manager.is_table_referenced(table_name):
        #     raise IntegrityError(f"Cannot drop table '{table_name}' because it is referenced by a foreign key")

        # Remove table data
        if table_name in self.__table_data:
            del self.__table_data[table_name]

        # Remove column types
        if table_name in self.__column_types:
            del self.__column_types[table_name]

        # Remove column constraints
        if table_name in self.__column_constraints:
            del self.__column_constraints[table_name]


data_manager = DataManager()
