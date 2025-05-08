from ASTNodes.BaseNode import ASTNode
from DataManager import data_manager
from Exceptions import PreProcessorError


class DropStmt(ASTNode):
    def __init__(self, table):
        self.table = table
        super().__init__()

    def __repr__(self):
        return f"DropStmt(table={self.table})"

    def perform_checks(self):
        self.table = self.table.value
        self.check_table(self.table)
        for column in data_manager.get_columns_for_table(self.table):
            referenced = data_manager.foreign_key_manager.get_columns_foreign_keys(column)
            if len(referenced) > 0:
                raise PreProcessorError(f"Unable to drop table '{self.table}'. Foreign key references exist: {referenced}")
