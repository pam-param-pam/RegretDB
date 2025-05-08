from ASTNodes.AlterNodes import AlterAddStmt, AlterRenameStmt, AlterModifyStmt, AlterDropStmt
from ASTNodes.CreateNode import CreateStmt
from ASTNodes.DeleteNode import DeleteStmt
from ASTNodes.DropNode import DropStmt
from ASTNodes.InsertNode import InsertStmt
from ASTNodes.SelectNode import SelectStmt
from ASTNodes.UpdateNode import UpdateStmt
from Exceptions import RegretDBError
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
            scans = [TableScan(table) for table in statement.tables]

            # Step 2: Build cross joins
            plan = scans[0]
            for scan in scans[1:]:
                plan = CrossJoin(plan, scan)

            # Step 3: WHERE clause
            if statement.where_expr:
                plan = Filter(plan, statement.where_expr)

            # Step 4: SELECT columns
            plan = Project(plan, statement.columns)

            # Step 5: ORDER BY
            if statement.order_by:
                plan = Sort(plan, statement.order_by)

            # Step 6: Visualize
            plan = Visualize(plan)

            return plan
        elif isinstance(statement, InsertStmt):
            return Insert(table_name=statement.table, columns=statement.columns, values=statement.values)
        elif isinstance(statement, UpdateStmt):
            # Step 1: Scan the target table
            scan = TableScan(statement.table)

            # Step 2: Filter rows using WHERE clause
            plan = scan
            if statement.where_expr:
                plan = Filter(plan, statement.where_expr)

            # Step 3: Apply Update operations
            plan = Update(plan, statement.assignments, table_name=statement.table)

            return plan
        elif isinstance(statement, DeleteStmt):
            # Step 1: Scan the target table
            scan = TableScan(statement.table)

            # Step 2: Filter rows using WHERE clause
            plan = scan
            if statement.where_expr:
                plan = Filter(plan, statement.where_expr)

            # Step 3: Apply Delete operations
            plan = Delete(plan, table=statement.table, where_expr=statement.where_expr)

            return plan
        elif isinstance(statement, CreateStmt):
            return CreateTable(name=statement.name, columns=statement.columns)

        elif isinstance(statement, DropStmt):
            return DropTable(table=statement.table)
        elif isinstance(statement, AlterAddStmt):
            pass
        elif isinstance(statement, AlterModifyStmt):
            pass
        elif isinstance(statement, AlterRenameStmt):
            pass
        elif isinstance(statement, AlterDropStmt):
            pass
        else:
            raise RegretDBError(f"Unexpected statement type: {type(statement)}")
