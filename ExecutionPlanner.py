from ASTNodes.AlterNodes import AlterAddStmt, AlterRenameStmt, AlterModifyStmt, AlterDropStmt
from ASTNodes.CreateNode import CreateStmt
from ASTNodes.DeleteNode import DeleteStmt
from ASTNodes.DropNode import DropStmt
from ASTNodes.InsertNode import InsertStmt
from ASTNodes.SelectNode import SelectStmt
from ASTNodes.UpdateNode import UpdateStmt
from Exceptions import RegretDBError
from PlanNodes.AlterPlanNodes import AlterAdd, AlterRename, AlterDrop
from PlanNodes.CreatePlanNodes import CreateTable
from PlanNodes.DeletePlanNode import Delete
from PlanNodes.DropTablePlanNode import DropTable
from PlanNodes.InsertPlanNode import Insert
from PlanNodes.SelectPlanNodes import TableScan, Filter, CrossJoin, Project, Sort, Visualize
from PlanNodes.UpdatePlanNode import Update


class ExecutionPlanner:
    def plan(self, statement):
        if isinstance(statement, SelectStmt):

            # Step 1: TableScans
            scans = [TableScan(table) for table in statement.qualified_tables]

            # Step 2: Build cross joins
            plan = scans[0]
            for scan in scans[1:]:
                plan = CrossJoin(plan, scan)

            # Step 3: WHERE clause
            if statement.qualified_where_expr:
                plan = Filter(plan, statement.qualified_where_expr)

            # Step 4: SELECT columns
            plan = Project(plan, statement.qualified_columns)

            # # Step 5: ORDER BY
            if statement.qualified_order_by:
                plan = Sort(plan, statement.qualified_order_by)

            # Step 6: Visualize
            plan = Visualize(plan)

            return plan

        elif isinstance(statement, InsertStmt):
            return Insert(table=statement.qualified_table, columns=statement.qualified_columns, values=statement.qualified_values)

        elif isinstance(statement, UpdateStmt):
            # Step 1: Scan the target table
            scan = TableScan(statement.qualified_table)

            # Step 2: Filter rows using WHERE clause
            plan = scan
            if statement.where_expr:
                plan = Filter(plan, statement.where_expr)

            # Step 3: Apply Update operations
            plan = Update(plan, statement.qualified_assignments, table=statement.qualified_table)

            return plan

        elif isinstance(statement, DeleteStmt):
            # Step 1: Scan the target table
            scan = TableScan(statement.qualified_table)

            # Step 2: Filter rows using WHERE clause
            plan = scan
            if statement.qualified_where_expr:
                plan = Filter(plan, statement.qualified_where_expr)

            # Step 3: Apply Delete operations
            plan = Delete(plan, table=statement.qualified_table)

            return plan

        elif isinstance(statement, CreateStmt):
            return CreateTable(table=statement.qualified_table, columns_spec=statement.qualified_columns_spec)

        elif isinstance(statement, DropStmt):
            return DropTable(table=statement.qualified_table)

        elif isinstance(statement, AlterAddStmt):
            return AlterAdd(table=statement.qualified_table, column_spec=statement.qualified_column_spec)

        elif isinstance(statement, AlterRenameStmt):
            return AlterRename(table=statement.qualified_table, new_column=statement.qualified_new_column, old_column=statement.qualified_old_column)

        elif isinstance(statement, AlterDropStmt):
            return AlterDrop(table=statement.qualified_table, column=statement.qualified_column, drop_type=statement.drop_type)

        elif isinstance(statement, AlterModifyStmt):
            pass

        else:
            raise RegretDBError(f"Unexpected statement type: {type(statement)}")
