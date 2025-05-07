from DataManager import data_manager
from ExecutionPlanner import ExecutionPlanner
from LALR import Parser


# Things that will NOT be supported:
# JOINS, FUNCTIONS, SUB-QUERIES, DATA SIZE (e.g VARCHAR(100))
# Statement optimizations, indexes
# It supports only 1 process, it won't detect metadata changes happening outside the process
# It is not async safe :D

class RegretDB:
    def __init__(self):
        self.parser = Parser()
        self.planner = ExecutionPlanner()
        # self.data_manager = DataManager()
        self.statement = None
        self.plan = None

        self.data = {}

    def execute_order_66(self, sql_stmt):
        """May the 4th be with you"""
        self.statement = self.parser.parse(sql_stmt)
        self.statement.set_sql_text(sql_stmt)
        print(self.statement)
        self.statement.verify()
        self.plan = self.planner.plan(self.statement)
        self.plan.execute()

        # self.statement = None
        # self.plan = None


# Example usage:
db_engine = RegretDB()
# sql = "SELECT users.name FROM users, orders WHERE True"
sql = "CREATE TABLE orders (id NUMBER PRIMARY KEY DEFAULT 1, user_id NUMBER FOREIGN KEY REFERENCES users(id) )"
# todo enforce FOREIGN key
db_engine.execute_order_66(sql)
sql = "INSERT INTO orders (id, user_id) VALUES (1, 1)"
db_engine.execute_order_66(sql)
sql = "CREATE TABLE users (name TEXT , id NUMBER PRIMARY KEY)"
db_engine.execute_order_66(sql)
sql = "INSERT INTO users (name, id) VALUES (NULL, 1)"
db_engine.execute_order_66(sql)
sql = "INSERT INTO users (name, id) VALUES ('Bob', 2)"
db_engine.execute_order_66(sql)
sql = "INSERT INTO users (name, id) VALUES ('Charlie', 3)"
db_engine.execute_order_66(sql)
sql = "INSERT INTO users (name, id) VALUES ('Hughie', 4)"
db_engine.execute_order_66(sql)
sql = "INSERT INTO users (name, id) VALUES ('Leyla', 5)"
db_engine.execute_order_66(sql)
sql = "SELECT users.id, users.name, orders.id, orders.user_id FROM users, orders WHERE users.id IS NOT NULL ORDER BY users.id ASC, users.name ASC"
db_engine.execute_order_66(sql)
print(data_manager.column_constraints)
print(data_manager.tables)
