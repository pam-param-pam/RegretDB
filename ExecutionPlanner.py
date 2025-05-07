from ASTNodes import SelectStmt, InsertStmt, UpdateStmt, DeleteStmt, CreateStmt, DropStmt, AlterStmt
from Exceptions import RegretDBError
from PlanNodes import TableScan, CrossJoin, Filter, Project, Sort, CreateTable, Insert, Visualize


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
            pass
        elif isinstance(statement, DeleteStmt):
            pass
        elif isinstance(statement, CreateStmt):
            return CreateTable(name=statement.name, columns=statement.columns)

        elif isinstance(statement, DropStmt):
            pass
        elif isinstance(statement, AlterStmt):
            pass
        else:
            raise RegretDBError(f"Unexpected statement type: {type(statement)}")
