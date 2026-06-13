from typing import List, Tuple
from ASTNodes.BaseNode import QualifiedColumn
from ASTNodes.Qualified import QualifiedTable
from PlanNodes.BasePlanNode import PlanNode
from DataManager import data_manager, Column, ForeignKey, FkAction
from TokenTypes import ConstraintSpec


class CreateTable(PlanNode):
    def __init__(self, table: QualifiedTable, columns_spec: List[Tuple['QualifiedColumn', str, List['ConstraintSpec']]]):
        self.table = table
        self.columns_spec = columns_spec

    def __str__(self):
        return f"CreateTable(table={self.table}, columns={self.columns_spec})"

    def execute(self):
        column_objs = []

        for qcol, col_type, constraints in self.columns_spec:
            col_name = qcol.column
            nullable = True
            unique = False
            primary_key = False
            default = None
            foreign_key = None

            for constraint in constraints:
                constraint_type = constraint.type
                if constraint_type == 'NOT NULL':
                    nullable = False
                elif constraint_type == 'UNIQUE':
                    unique = True
                elif constraint_type == 'PRIMARY KEY':
                    primary_key = True
                    nullable = False
                elif constraint_type == 'DEFAULT':
                    default = constraint.arg1
                    default = default.value
                elif constraint_type == 'FOREIGN KEY':
                    ref_qualified = constraint.arg1
                    ref_table, ref_column = ref_qualified.split('.')

                    on_delete_str = constraint.on_delete
                    on_update_str = constraint.on_update

                    fk_action_map = {
                        'RESTRICT': FkAction.RESTRICT,
                        'CASCADE': FkAction.CASCADE,
                        'SET NULL': FkAction.SET_NULL
                    }
                    foreign_key = ForeignKey(
                        column=col_name,
                        ref_table=ref_table,
                        ref_column=ref_column,
                        on_delete=fk_action_map[on_delete_str],
                        on_update=fk_action_map[on_update_str]
                    )

            col = Column(
                name=col_name,
                data_type=col_type,
                nullable=nullable,
                unique=unique,
                primary_key=primary_key,
                default=default,
                foreign_key=foreign_key
            )
            column_objs.append(col)

        # Create the table in the data manager
        data_manager.create_table(self.table.name, column_objs)
