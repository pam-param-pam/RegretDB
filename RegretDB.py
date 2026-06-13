from ExecutionPlanner import ExecutionPlanner
from LALR import Parser


# Things that will NOT be supported:
# JOINS, FUNCTIONS, SUB-QUERIES, DATA SIZE (e.g VARCHAR(100))
# Statement optimizations, indexes
# It supports only 1 process, it won't detect metadata changes happening outside the process
# It is not async safe :D
# it doesn't even support any disk writes lol

# Yea basically i just wanted to write a simple sql parser and it lwk escalated

class RegretDB:
    def __init__(self):
        self.parser = Parser()
        self.planner = ExecutionPlanner()

    def execute_order_66(self, sql_stmt):
        """May the 4th be with you"""
        statement = self.parser.parse(sql_stmt)
        statement.set_sql_text(sql_stmt)
        statement.verify()
        plan = self.planner.plan(statement)
        plan.execute()


# todo enforce FOREIGN key
# Example usage:
db_engine = RegretDB()
sql = "CREATE TABLE users (id NUMBER PRIMARY KEY, name text UNIQUE NOT NULL, isStaff BOOLEAN default false)"
db_engine.execute_order_66(sql)
sql = "CREATE TABLE orders (id NUMBER PRIMARY KEY, product text UNIQUE, user_id NUMBER FOREIGN KEY REFERENCES users(id))"
db_engine.execute_order_66(sql)


sql = "INSERT INTO users (name, id) VALUES ('Ash', 2)"
db_engine.execute_order_66(sql)
sql = "INSERT INTO orders (id, product, user_id) VALUES (1, 'computer', 2)"
db_engine.execute_order_66(sql)
# sql = "INSERT INTO users (name, id) VALUES ('A1sh', 21)"
# db_engine.execute_order_66(sql)
sql = "INSERT INTO users (name, id) VALUES ('Alice', 1)"
db_engine.execute_order_66(sql)
sql = "INSERT INTO users (name, id) VALUES ('Hughie', 4)"
db_engine.execute_order_66(sql)
sql = "INSERT INTO users (name, id) VALUES ('Leyla', 5)"
db_engine.execute_order_66(sql)


# sql = "SELECT * FROM users WHERE (user1s.name='Leyla' and id=4) or True"
# sql = "DROP TABLE users"
# db_engine.execute_order_66(sql)
sql = "Delete from users where id = 1"
db_engine.execute_order_66(sql)

# sql = "DROp table users"
# db_engine.execute_order_66(sql)

sql = "SELECT * FROm USERS"
db_engine.execute_order_66(sql)

# # sql = "SELECT users.name FROM users, orders WHERE True"
# sql = "CREATE TABLE orders (id NUMBER PRIMARY KEY, user_id NUMBER FOREIGN KEY REFERENCES users(id))"
# db_engine.execute_order_66(sql)
# # sql = "CREATE TABLE ala (id NUMBER PRIMARY KEY DEFAULT 1, user_id NUMBER FOREIGN KEY REFERENCES users(id))"
# # db_engine.execute_order_66(sql)
# # print(data_manager.table_columns)
# sql = "INSERT INTO users (id) VALUES (1)"
# db_engine.execute_order_66(sql)
# sql = "INSERT INTO users (id) VALUES (7)"
# db_engine.execute_order_66(sql)
# sql = "INSERT INTO orders (id, user_id) VALUES (1, 1)"
# db_engine.execute_order_66(sql)
# sql = "INSERT INTO orders (id, user_id) VALUES (2, 7)"
# db_engine.execute_order_66(sql)
#
# sql = "INSERT INTO users (name, id) VALUES ('Ash', 2)"
# db_engine.execute_order_66(sql)
# sql = "INSERT INTO users (name, id) VALUES ('Laura', 3)"
# db_engine.execute_order_66(sql)
# sql = "INSERT INTO users (name, id) VALUES ('Hughie', 4)"
# db_engine.execute_order_66(sql)
# sql = "INSERT INTO users (name, id) VALUES ('Leyla', 5)"
# db_engine.execute_order_66(sql)

# print(data_manager.column_constraints)

# db_engine.execute_order_66(sql)
sql = "UPDATE orders SET user_id=5 where user_id=2"
db_engine.execute_order_66(sql)
sql = "SELECT * FROM orders "
db_engine.execute_order_66(sql)

# sql = "DELETE FROM users where id=5"
# # sql = "SELECT * FROM orders"
# db_engine.execute_order_66(sql)

# sql = "SELECT * FROM users where isStaff = isStaff"
# db_engine.execute_order_66(sql)
# print(data_manager.foreign_key_manager)
# print(data_manager.foreign_key_manager.get_columns_foreign_keys('users.id'))
