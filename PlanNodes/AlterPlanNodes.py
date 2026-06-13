from typing import List, Tuple

from ASTNodes.Qualified import QualifiedTable, QualifiedColumn
from PlanNodes.BasePlanNode import PlanNode
from DataManager import data_manager, Column, FkAction, ForeignKey
from TokenTypes import ConstraintSpec


class AlterAdd(PlanNode):
    def __init__(self, table: QualifiedTable, column_spec: Tuple[QualifiedColumn, str, List[ConstraintSpec]]):
        self.table = table
        self.column_spec = column_spec
        super().__init__()

    def __str__(self):
        qcol, col_type, constraints = self.column_spec
        return f"AlterAdd(table={self.table.name}, column={qcol.column}, type={col_type})"

    def execute(self):
        qcol, col_type_str, constraints = self.column_spec
        col_name = qcol.column

        nullable = True
        unique = False
        primary_key = False
        default = None
        foreign_key = None

        for constraint in constraints:
            ct = constraint.type
            if ct == 'NOT NULL':
                nullable = False
            elif ct == 'UNIQUE':
                unique = True
            elif ct == 'PRIMARY KEY':
                primary_key = True
                nullable = False
            elif ct == 'DEFAULT':
                default = constraint.arg1.value
            elif ct == 'FOREIGN KEY':
                ref_qualified = constraint.arg1
                ref_table, ref_column = ref_qualified.split('.')
                on_delete_str = getattr(constraint, 'on_delete', 'RESTRICT')
                on_update_str = getattr(constraint, 'on_update', 'RESTRICT')
                fk_map = {
                    'RESTRICT': FkAction.RESTRICT,
                    'CASCADE': FkAction.CASCADE,
                    'SET NULL': FkAction.SET_NULL
                }
                foreign_key = ForeignKey(
                    column=col_name,
                    ref_table=ref_table,
                    ref_column=ref_column,
                    on_delete=fk_map.get(on_delete_str, FkAction.RESTRICT),
                    on_update=fk_map.get(on_update_str, FkAction.RESTRICT)
                )

        new_col = Column(
            name=col_name,
            data_type=col_type_str,
            nullable=nullable,
            unique=unique,
            primary_key=primary_key,
            default=default,
            foreign_key=foreign_key
        )

        data_manager.add_column(self.table.name, new_col)


class AlterRename(PlanNode):
    def __init__(self, table: QualifiedTable, old_column: QualifiedColumn, new_column: QualifiedColumn):
        self.table = table
        self.old_column = old_column
        self.new_column = new_column
        super().__init__()

    def __str__(self):
        return f"AlterRename(table={self.table.name}, old={self.old_column.column}, new={self.new_column.column})"

    def execute(self):
        data_manager.rename_column(self.table.name, self.old_column.column, self.new_column.column)

# todo finish these

class AlterDrop(PlanNode):
    def __init__(self, qualified_table, qualified_column, drop_type: str):
        self.table = qualified_table
        self.column = qualified_column
        self.drop_type = drop_type
        super().__init__()

    def __str__(self):
        return f"AlterDrop(table={self.table.name}, column={self.column.column})"

    def execute(self):
        pass

class AlterModify(PlanNode):
    def __init__(self, qualified_table, qualified_column, new_col_type_str, new_column_obj: Column):
        self.table = qualified_table
        self.column = qualified_column
        self.new_col_type = new_col_type_str
        self.new_column_obj = new_column_obj
        super().__init__()

    def __str__(self):
        return f"AlterModify(table={self.table.name}, column={self.column.column})"

    def execute(self):
        pass
