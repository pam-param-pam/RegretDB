# Utility function for evaluating conditions in WHERE clause
from Nodes import SelectStmt
from Table import Table


def evaluate_condition(row, condition, table_columns):
    """Evaluates a condition on a given row. (left, op, right)"""
    left, op, right = condition
    left_value = row[table_columns.index(left)] if left in table_columns else left  # Fetch value from row or use raw value
    if isinstance(left_value, str):
        left_value = str(left_value)
    if isinstance(right, str):
        right = str(right)

    if op == '=':
        return left_value == right
    elif op == '>':
        return left_value > right
    elif op == '<':
        return left_value < right
    elif op == '!=':
        return left_value != right
    else:
        raise NotImplementedError(f"Operator {op} not supported")


# Function to evaluate WHERE condition (AND/OR)
def evaluate_where(row, where_expr, table_columns):
    """Evaluates the AND/OR logical condition in the WHERE clause"""
    if where_expr[0] == 'AND':
        left_condition = evaluate_condition(row, where_expr[1], table_columns)
        right_condition = evaluate_condition(row, where_expr[2], table_columns)
        return left_condition and right_condition
    elif where_expr[0] == 'OR':
        left_condition = evaluate_condition(row, where_expr[1], table_columns)
        right_condition = evaluate_condition(row, where_expr[2], table_columns)
        return left_condition or right_condition
    else:
        return evaluate_condition(row, where_expr, table_columns)


# Sorting function for ORDER BY
def apply_order_by(rows, order_by, table_columns):
    """Sorts rows based on the ORDER BY clause"""

    def get_sort_key(row, order):
        columns, direction = order
        column_indices = [table_columns.index(col) for col in columns]
        return tuple(row[i] for i in column_indices)

    # Sort by each column in order
    return sorted(rows, key=lambda row: get_sort_key(row, order_by[0]), reverse=(order_by[1] == 'DESC'))


# Function to execute SELECT statement
def execute_select_statement(tables, select_stmt):
    # Step 1: Get the base table and column names
    base_table = tables[select_stmt.base_table]
    base_table_columns = base_table.get_column_names()  # Get columns from base table

    # Step 2: Join the tables (in this case, we join 'users' with 'orders')
    joined_rows = []
    for user_row in base_table.data:
        for order_row in tables['orders'].data:
            # Perform join: users.id = orders.user_id
            if user_row['id'] == order_row['user_id']:
                joined_row = {**user_row, **order_row}  # Merging the two rows (dicts)
                joined_rows.append(joined_row)

    # Step 3: Apply the WHERE condition (Filtering)
    filtered_rows = []
    for row in joined_rows:
        if evaluate_where(row, select_stmt.where_expr, base_table_columns):
            filtered_rows.append(row)

    # Step 4: Apply the ORDER BY clause (Sorting)
    sorted_rows = apply_order_by(filtered_rows, select_stmt.order_by, base_table_columns)

    # Step 5: Select the required columns from the final result
    selected_rows = []
    for row in sorted_rows:
        selected_row = [row[col] for col in select_stmt.columns]
        selected_rows.append(selected_row)

    return selected_rows


# Example data (simplified)
users_data = [
    {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
    {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'}
]

orders_data = [
    {'order_id': 101, 'user_id': 1, 'amount': 200},
    {'order_id': 102, 'user_id': 2, 'amount': 150}
]

# Example Table Instances
users_table = Table(name="users", columns=[{'name': 'id', 'type': 'INTEGER', 'constraints': ['PRIMARY KEY']}, {'name': 'name', 'type': 'TEXT', 'constraints': []}, {'name': 'email', 'type': 'TEXT', 'constraints': []}], data=users_data)
orders_table = Table(name="orders", columns=[{'name': 'order_id', 'type': 'INTEGER', 'constraints': ['PRIMARY KEY']}, {'name': 'user_id', 'type': 'INTEGER', 'constraints': []}, {'name': 'amount', 'type': 'DECIMAL', 'constraints': []}], data=orders_data)

# Tables dictionary
tables = {
    'users': users_table,
    'orders': orders_table
}

# Example Select Statement
select_stmt = SelectStmt(
    columns=['users.id', 'orders.amount'],
    base_table='users',
    joins=[('orders', ('=', 'users.id', 'orders.user_id'))],
    where_expr=('AND', ('>', 'orders.amount', '100'), ('=', 'ala', 'name')),
    order_by=[(['orders.amount'], 'ASC'), (['orders.name'], 'DESC')]
)

# Execute the statement
result = execute_select_statement(tables, select_stmt)
print(result)
