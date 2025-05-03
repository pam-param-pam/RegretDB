# Example list of SelectStmt objects
from LALR import SelectStmt

queries = [
    SelectStmt(
        columns=["id", "name"],
        base_table="users",
        joins=[("orders", "users.id = orders.user_id")],
        where_expr="age >= 30",
        order_by=[("name", "ASC")]
    )
]

# Function to search by base table name
def search_by_base_table(queries, table_name):
    return [query for query in queries if query.base_table == table_name]

# Function to search by column
def search_by_column(queries, column):
    return [query for query in queries if column in query.columns]

# Example search: Search for all queries on the 'users' table
users_queries = search_by_base_table(queries, "users")
print("Queries on 'users' table:")
for query in users_queries:
    print(query)

# Example search: Search for all queries involving the 'name' column
name_column_queries = search_by_column(queries, "name")
print("\nQueries involving 'name' column:")
for query in name_column_queries:
    print(query)