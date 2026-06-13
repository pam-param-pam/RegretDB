from typing import List, Optional
from ASTNodes.BaseNode import ASTNode, QualifiedColumn, QualifiedTable
from DataManager import data_manager
from Exceptions import PreProcessorError
from TokenTypes import Identifier, Literal


class InsertStmt(ASTNode):
    def __init__(self, table: Identifier, columns: Optional[List[Identifier]], values: List[Literal]) -> None:
        self._table: Identifier = table
        self._columns: Optional[List[Identifier]] = columns
        self._values: List[Literal] = values

        self.qualified_table: Optional[QualifiedTable] = None
        self.qualified_columns: Optional[List[QualifiedColumn]] = None
        self.qualified_values = None
        super().__init__()

    def __repr__(self) -> str:
        return f"InsertStmt(table={self._table}, columns={self._columns}, values={self._values})"

    def perform_checks(self) -> None:
        # 1. Validate and get qualified table
        self.qualified_table = self.check_table(self._table.value, self._table.position)

        # 2. Handle implicit column list (all columns in table order)
        all_columns_in_table = data_manager.get_columns_for_table(self.qualified_table.name)

        if self._columns is None:
            # No column list provided → assume all columns in their natural order
            self.qualified_columns = [QualifiedColumn(table=self.qualified_table, column=col)for col in all_columns_in_table]
        else:
            # check_columns expects a list of QualifiedTable (here just one) and returns list of QualifiedColumn
            self.qualified_columns = self.check_columns([self.qualified_table], self._columns)

        # 3. Check that number of values matches number of columns
        if len(self.qualified_columns) != len(self._values):
            raise PreProcessorError(f"Columns length({len(self.qualified_columns)}) != values length({len(self._values)})")

        # 4. Type checking for each (column, value) pair
        for qualified_col, val in zip(self.qualified_columns, self._values):
            self.check_type(qualified_col, val)

        self.qualified_values = self._values

        inserted_column_names = {qcol.column for qcol in self.qualified_columns}
        table_obj = data_manager.get_table(self.qualified_table.name)

        # 5. Check for NOT NULL violations on omitted columns
        for col_name, col in table_obj.columns.items():
            if col_name not in inserted_column_names:
                # Column omitted: must be nullable or have a default
                if not col.nullable and col.default is None:
                    raise PreProcessorError(f"Column '{col_name}' must be specified (NOT NULL constraint, no default)", position=self._table.position)  # todo fix the position here

