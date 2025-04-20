class Tokenizer:
    def __init__(self, sql):
        self.tokens = self._tokenize(sql)
        self.pos = 0

    def _tokenize(self, sql):
        tokens = []
        word = ''
        i = 0
        n = len(sql)

        while i < n:
            ch = sql[i]

            if ch.isspace():
                if word:
                    tokens.append(word)
                    word = ''
            elif ch in {',', '=', '(', ')', '<', '>', '!', '*'}:
                if word:
                    tokens.append(word)
                    word = ''
                # Handle compound operators like !=, <=, >=
                if ch in {'<', '>', '!'} and i + 1 < n and sql[i + 1] == '=':
                    tokens.append(ch + '=')
                    i += 1
                else:
                    tokens.append(ch)
            elif ch == "'":  # Handle string literals
                if word:
                    tokens.append(word)
                    word = ''
                word = ch  # Start with opening quote
                i += 1
                while i < n and sql[i] != "'":
                    word += sql[i]
                    i += 1
                if i >= n:
                    error_string = sql + "\n" + len(sql) * " " + "^"
                    raise SyntaxError(f"Unterminated string literal:\n{error_string}")
                word += sql[i]  # Add closing quote
                tokens.append(word)
                word = ''
                i += 1  # Move past closing quote
            else:
                word += ch
            i += 1

        if word:
            tokens.append(word)
        tokens.append('EOF')
        return tokens

    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        if self.pos < len(self.tokens):
            self.pos += 1

    def current(self):
        return self.peek()


class LL1Parser:
    def __init__(self, tokenizer):
        self.debug_trace = None
        self.tokenizer = tokenizer
        self.stack = ['START']
        self.table = self.build_table()
        self.parsed = ''
        self.trace = []  # list of (top, token, type)

    def build_table(self):
        return {
            'START': {
                'SELECT': ['SELECT_STMT'],
                'INSERT': ['INSERT_STMT'],
                'UPDATE': ['UPDATE_STMT'],
                'DELETE': ['DELETE_STMT'],
                'CREATE': ['CREATE_STMT']

            },
            'CREATE_STMT': {
                'CREATE': ['CREATE', 'TABLE', 'ID', '(', 'COLUMN_DEFS', ')']
            },
            'COLUMN_DEFS': {
                'identifier': ['COLUMN_DEF', 'COLUMN_DEFS_TAIL']
            },
            'COLUMN_DEFS_TAIL': {
                ',': [',', 'COLUMN_DEF', 'COLUMN_DEFS_TAIL'],
                ')': []  # ε
            },
            'COLUMN_DEF': {
                'identifier': ['ID', 'DATATYPE', 'CONSTRAINTS']
            },
            'DATATYPE': {
                'INT': ['INT'],
                'VARCHAR': ['VARCHAR', '(', 'number', ')'],
                'TEXT': ['TEXT'],
                'DATE': ['DATE'],
                'DATETIME': ['DATETIME']
            },
            'CONSTRAINTS': {
                'PRIMARY': ['PRIMARY', 'KEY', 'MORE_CONSTRAINTS'],
                'NOT': ['NOT', 'NULL', 'MORE_CONSTRAINTS'],
                'UNIQUE': ['UNIQUE', 'MORE_CONSTRAINTS'],
                ')': [],  # ε
                ',': []  # ε
            },
            'MORE_CONSTRAINTS': {
                'PRIMARY': ['CONSTRAINTS'],
                'NOT': ['CONSTRAINTS'],
                'UNIQUE': ['CONSTRAINTS'],
                ')': [],  # ε
                ',': []  # ε
            },
            'SELECT_STMT': {
                'SELECT': ['SELECT', 'COLUMNS', 'FROM', 'TABLES', 'JOIN_CLAUSE', 'WHERE_CLAUSE', 'ORDER_CLAUSE']
            },
            'INSERT_STMT': {
                'INSERT': ['INSERT', 'INTO', 'TABLES', 'VALUES', '(', 'VALS', ')']
            },
            'UPDATE_STMT': {
                'UPDATE': ['UPDATE', 'TABLES', 'SET', 'ASSIGNMENTS', 'WHERE_CLAUSE']
            },
            'DELETE_STMT': {
                'DELETE': ['DELETE', 'FROM', 'TABLES', 'WHERE_CLAUSE']
            },
            'COLUMNS': {
                '*': ['*'],
                'identifier': ['ID', 'COLUMNS_TAIL'],
                'SELECT': ['SUBQUERY', 'COLUMNS_TAIL']  # For nested SELECT
            },
            'COLUMNS_TAIL': {
                ',': [',', 'COLUMN_ITEM', 'COLUMNS_TAIL'],
                'FROM': []  # ε
            },
            'COLUMN_ITEM': {
                'identifier': ['ID'],
                'SELECT': ['SUBQUERY']
            },
            'TABLES': {
                'identifier': ['ID', 'TABLES_TAIL'],
                # 'SELECT': ['SUBQUERY', 'TABLES_TAIL']  # For derived tables
            },
            'TABLES_TAIL': {
                ',': [',', 'TABLE_ITEM', 'TABLES_TAIL'],
                'JOIN': ['JOIN_CLAUSE'],  # Allow explicit JOIN
                'INNER': ['JOIN_CLAUSE'],  # Handle INNER JOIN
                'LEFT': ['JOIN_CLAUSE'],  # Handle LEFT JOIN
                'RIGHT': ['JOIN_CLAUSE'],  # Handle RIGHT JOIN
                'FULL': ['JOIN_CLAUSE'],  # Handle FULL JOIN
                'WHERE': [],  # ε
                'ORDER': [],  # ε
                'SET': [],
                'EOF': []  # ε
            },
            'TABLE_ITEM': {
                'identifier': ['ID'],
                'SELECT': ['SUBQUERY']
            },
            'JOIN_CLAUSE': {
                'JOIN': ['JOIN', 'ID', 'ON', 'CONDITION', 'JOIN_CLAUSE'],
                'INNER': ['INNER', 'JOIN', 'ID', 'ON', 'CONDITION', 'JOIN_CLAUSE'],
                'LEFT': ['LEFT', 'JOIN', 'ID', 'ON', 'CONDITION', 'JOIN_CLAUSE'],
                'RIGHT': ['RIGHT', 'JOIN', 'ID', 'ON', 'CONDITION', 'JOIN_CLAUSE'],
                'FULL': ['FULL', 'JOIN', 'ID', 'ON', 'CONDITION', 'JOIN_CLAUSE'],
                'WHERE': [],  # ε
                'ORDER': [],  # ε
                'EOF': []  # ε
            },
            'WHERE_CLAUSE': {
                'WHERE': ['WHERE', 'CONDITION'],
                'ORDER': [],  # ε
                'EOF': []  # ε
            },
            'WHERE_TAIL': {
                'AND': ['AND', 'CONDITION', 'WHERE_TAIL'],
                'OR': ['OR', 'CONDITION', 'WHERE_TAIL'],
                'ORDER': [],  # ε
                'EOF': []  # ε
            },
            'ORDER_CLAUSE': {
                'ORDER': ['ORDER', 'BY', 'ORDER_COLUMNS'],
                'EOF': []  # ε
            },
            'ORDER_COLUMNS': {
                'identifier': ['ID', 'ORDER_DIRECTION', 'ORDER_COLUMNS_TAIL']
            },
            'ORDER_DIRECTION': {
                'ASC': ['ASC'],
                'DESC': ['DESC'],
                ',': [],  # ε
                'EOF': []  # ε
            },
            'ORDER_COLUMNS_TAIL': {
                ',': [',', 'ID', 'ORDER_DIRECTION', 'ORDER_COLUMNS_TAIL'],
                'EOF': []  # ε
            },
            'ASSIGNMENTS': {
                'identifier': ['ID', '=', 'VAL', 'ASSIGNMENTS_TAIL']
            },
            'ASSIGNMENTS_TAIL': {
                ',': [',', 'ID', '=', 'VAL', 'ASSIGNMENTS_TAIL'],
                'WHERE': []  # ε
            },
            'CONDITION': {
                'identifier': ['SIMPLE_CONDITION', 'CONDITION_TAIL'],
                '(': ['(', 'CONDITION', ')', 'CONDITION_TAIL'],
                'EOF': []
            },
            'SIMPLE_CONDITION': {
                'identifier': ['ID', 'COMPARISON_OP', 'VAL']
            },
            'CONDITION_TAIL': {
                'AND': ['AND', 'CONDITION'],
                'OR': ['OR', 'CONDITION'],
                ')': [],  # ε - allows closing parenthesis
                'EOF': [],  # ε - allows end of condition
                'ORDER': []  # ε - allows ORDER BY after WHERE
            },
            'COMPARISON_OP': {
                '=': ['='],
                '<': ['<'],
                '>': ['>'],
                '<=': ['<='],
                '>=': ['>='],
                '!=': ['!=']
            },
            'LOGICAL_OP': {
                'AND': ['AND'],
                'OR': ['OR'],
                'EOF': []  # ε
            },
            'SUBQUERY': {
                '(': ['(', 'SELECT_STMT', ')']
            },
            'ID': {
                'identifier': ['identifier']
            },
            'VALS': {
                'number': ['VAL', 'VALS_TAIL'],
                'string': ['VAL', 'VALS_TAIL'],
                'identifier': ['VAL', 'VALS_TAIL']
            },
            'VALS_TAIL': {
                ',': [',', 'VAL', 'VALS_TAIL'],
                ')': []  # ε
            },
            'VAL': {
                'number': ['number'],
                'string': ['string'],
                'identifier': ['identifier'],
                # 'SELECT': ['SUBQUERY']
            }
        }

    def classify_token(self, token):
        token_upper = token.upper()
        if token_upper in {
            'CREATE', 'TABLE', 'INT', 'VARCHAR', 'TEXT', 'DATE', 'DATETIME',
            'PRIMARY', 'KEY', 'NOT', 'NULL', 'UNIQUE', 'SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'VALUES', 'UPDATE',
            'SET', 'DELETE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'ON',
            'AND', 'OR', 'ORDER', 'BY', 'ASC', 'DESC', 'GROUP', 'HAVING'
        }:
            return token_upper
        elif token.isdigit():
            return 'number'
        elif token.startswith("'") and token.endswith("'"):
            return 'string'
        elif token in {',', '=', '(', ')', '<', '>', '<=', '>=', '!=', '*', 'EOF'}:
            return token
        elif self.is_dotted_identifier(token):
            return 'identifier'
        elif token.isidentifier():
            return 'identifier'
        else:
            raise SyntaxError(f"Unknown token: {token}")

    def is_dotted_identifier(self, token):
        # Allow something like "table.column" as a valid identifier
        parts = token.split('.')
        return all(part.isidentifier() for part in parts)

    def make_error(self, top=None, current=None):
        error_string = ""
        self.parsed = self.parsed.replace(" ,", ",").replace("( ", "(").replace(" )", ")")
        if current:
            self.parsed += current

        self.parsed += "\n" + (len(self.parsed) - 2) * " " + "^"
        error_string += self.parsed
        if top and self.table.get(top):
            expected = " or ".join(f"'{k}'" for k in self.table[top].keys())
            error_string += f"\nExpected type: {expected}"
        if current:
            error_string += f"\nInstead got: {current}"
        return error_string

    def parse(self):
        self.debug_trace = []
        derivation_path = []

        while self.stack:
            top = self.stack.pop()
            current = self.tokenizer.current()
            token_type = self.classify_token(current)

            if top == token_type:
                self.parsed += current + " "
                # Add full path and terminal
                if derivation_path:
                    self.debug_trace.append(tuple(derivation_path + [top]))
                else:
                    self.debug_trace.append((top,))
                derivation_path = []  # Reset for next terminal
                self.tokenizer.advance()
                continue

            if top in self.table:
                rule = self.table[top].get(token_type)
                if rule is None:
                    raise SyntaxError(f"No rule for {top} with token '{current}'\n{self.make_error(top, current)}")

                derivation_path.append(top)
                for sym in reversed(rule):
                    if sym != '':
                        self.stack.append(sym)
            else:
                raise SyntaxError(f"Unexpected token '{current}' at {top}\n{self.make_error(top, current)}")

        if self.tokenizer.current() != 'EOF':
            raise SyntaxError(f"Extra input after end of statement\n{self.make_error()}")

        # self.print_tuple_debug()

    def print_tuple_debug(self):
        print("\n🔍 Debug Trace (Tuple Format):")
        for item in self.debug_trace:
            print(item, ",")


invalid_queries = [
    # "SELECT users.name, admins.id FROM users, admins WHERE id = 1", ##ambiguous id check for later
    "SELECT * FROM orders LEFT JOIN customers ON orders.customer_id",
    "SELECT name, id FROM users WHERE name = 'ala' AND id > 21 ORDER BY ASC",
    "SELECT * FROM products WHERE category ==",
    "SELECT name, id WHERE id > 21",
    "SELECT * FROM products WHERE category = 'ala",
    "CREATE TABLE users (id INT, name VARCHAR)",
    "SELECT * FROM a, b LEFT JOIN c ON b.id = c.id",
]
# Test cases
test_queries = [
    "SELECT Orders.OrderID, Customers.CustomerName, Orders.OrderDate FROM Orders INNER JOIN Customers ON Orders.CustomerID=Customers.CustomerID",
    "SELECT * FROM products WHERE category = 'ala AND WHERE id = 2137' AND name = 1",
    "UPDATE Clans SET ClanName = 'aaa' WHERE ClanId = 2137",
    "SELECT users.name, admins.id FROM users, admins WHERE id = 1",  # hard to catch
    "SELECT * FROM orders LEFT JOIN customers ON orders.customer_id = customers.id",
    "SELECT name, id FROM users WHERE name = 'ala' AND id > 21 ORDER BY name DESC",
    "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(255) NOT NULL, email VARCHAR(255) UNIQUE, created_at DATETIME)",
    "SELECT * FROM products WHERE category = 'ala'",
    "CREATE TABLE users (id INT, name VARCHAR(255))",

    # "SELECT a.name, b.address FROM a INNER JOIN b ON a.id = b.user_id WHERE a.age > 21 ORDER BY a.name DESC",
    # "SELECT * FROM (SELECT id, name FROM users WHERE active = 1) AS active_users WHERE name LIKE 'A%'",
    # "UPDATE products SET price = 19.99 WHERE category = 'electronics'",
    # "DELETE FROM logs WHERE timestamp < '2023-01-01'",
    # "SELECT id, (SELECT COUNT(*) FROM orders WHERE orders.user_id = users.id) AS order_count FROM users",
    # "SELECT * FROM products WHERE price > 100 AND (category = 'electronics' OR category = 'furniture') ORDER BY price ASC, name"
]
# for sql in invalid_queries:
for sql in test_queries:
    print(f"\nTesting query: {sql}")
    tokenizer = Tokenizer(sql)
    parser = LL1Parser(tokenizer)
    try:
        parser.parse()
        print("✅ Query parsed successfully!")
    except SyntaxError as e:
        print(f"❌ Error: {e}")


## add suport for ; spliting statements