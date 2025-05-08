from ASTNodes import SelectStmt, InsertStmt, UpdateStmt, DeleteStmt, CreateStmt, DropStmt, AlterAddStmt, AlterModifyStmt, AlterRenameStmt, AlterDropStmt
from Exceptions import RegretDBError
from PlanNodes import TableScan, CrossJoin, Filter, Project, Sort, CreateTable, Insert, Visualize, Update, DropTable


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
            # print(plan)
            return plan
        elif isinstance(statement, InsertStmt):
            return Insert(table_name=statement.table, columns=statement.columns, values=statement.values)
            # todo check uniqness combined with constraints
        elif isinstance(statement, UpdateStmt):
            # Step 1: Scan the target table
            scan = TableScan(statement.table.value)

            # Step 2: Filter rows using WHERE clause
            plan = scan
            if statement.where:
                plan = Filter(plan, statement.where)

            # Step 3: Apply SET operations
            plan = Update(plan, statement.assignments, table_name=statement.table.value)

            # Step 4: Visualize the plan (optional)
            plan = Visualize(plan)

            return plan
        elif isinstance(statement, DeleteStmt):
            pass
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
