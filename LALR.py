import re

from Nodes import *
from Token import Token

# Things that will NOT be supported:
# JOINS, FUNCTIONS, SUB-QUERIES, DATA SIZE (e.g VARCHAR(100))
# Statement optimizations
# and a loot more


def format_options(options):
    """Formats a list like ['ADD', 'DROP', 'RENAME'] into: 'ADD', 'DROP' or 'RENAME'"""
    quoted = [f"'{opt}'" for opt in options]
    if len(quoted) == 1:
        return quoted[0]
    return ", ".join(quoted[:-1]) + " or " + quoted[-1]

class Tokenizer:
    def __init__(self):
        token_specification = [
            ('NUMBER', r'\b\d+(?:\.\d*)?'),  # Integer or decimal number (non-capturing decimal)
            ('STRING', r"'([^']*)'"),  # Single-quoted string (capture inside)
            ('IDENT', r'[A-Za-z_][A-Za-z_0-9]*'),  # Identifiers
            ('OP', r'<=|>=|<>|!=|=|<|>'),  # Operators
            ('STAR', r'\*'),
            ('COMMA', r','),
            ('LPAREN', r'\('),
            ('RPAREN', r'\)'),
            ('SEMI', r';'),
            ('SKIP', r'[ \t\n\r]+'),  # Skip whitespace
            ('DOT', r'\.'),
            ('MISMATCH', r'.'),  # Any other character
        ]
        self. tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
        self.column_types = [
            'TEXT', 'NUMBER', 'BLOB'
        ]
        self.keywords = [
            'SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'ORDER', 'BY', 'ASC', 'DESC',
            'INSERT', 'INTO', 'VALUES',
            'UPDATE', 'SET',
            'DELETE',
            'CREATE', 'TABLE',
            'DROP',
            'ALTER', 'ADD', 'DROP', 'RENAME', 'MODIFY', 'CASCADE', 'RESTRICT,'
            'AND', 'OR', 'IS', 'NOT', 'NULL',  # operators
            'PRIMARY', 'FOREIGN', 'KEY', 'UNIQUE', 'DEFAULT'  # constraints
        ] + self.column_types

    def tokenize(self, sql):
        get_token = re.compile(self.tok_regex).match
        pos = 0
        tokens = []
        while pos < len(sql):
            m = get_token(sql, pos)
            if not m:
                raise SyntaxError(f"Illegal character at position {pos}")
            typ = m.lastgroup
            lexeme = m.group(typ)
            if typ == 'STRING':
                # Strip the quotes: lexeme includes the quotes, m.group(1) is content
                tokens.append(Token('STRING', lexeme[1:-1], pos))
            elif typ == 'IDENT':
                val = lexeme.upper()
                # Recognize SQL keywords (we store the type as the uppercase keyword)
                if val in self.keywords:
                    tokens.append(Token(val, val, pos))
                else:
                    tokens.append(Token('IDENT', lexeme, pos))
            elif typ == 'SKIP':
                pass  # ignore whitespace
            elif typ != 'MISMATCH':
                tokens.append(Token(typ, lexeme, pos))
            else:  # MISMATCH
                raise SyntaxError(f"Unexpected character {lexeme!r} at position {pos}")
            pos = m.end()
        return tokens


class Parser:
    def __init__(self, sql):
        self.tokenizer = Tokenizer()
        self.tokens = self.tokenizer.tokenize(sql)
        self.pos = 0
        self.sql = sql

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token('EOF', 'EOF', self.pos)

    def advance(self):
        self.pos += 1
        return self.peek()

    def expect(self, type_or_value):
        """Expect a token of given type or value, and consume it."""
        token = self.peek()
        if token.type == type_or_value or token.value == type_or_value:
            self.advance()
            return token
        else:
            raise SyntaxError(f"Expected {type_or_value}, found {token}\n{self.get_pretty_error()}")

    def get_pretty_error(self, adjust_pos=0):
        try:
            offset = self.tokens[self.pos + adjust_pos].offset
            adjust = 0
        except IndexError:
            offset = len(self.sql)
            adjust = 1

        return self.sql + "\n" + (offset + adjust) * " " + "^"

    def parse(self):
        """Parse the next statement based on the leading keyword and check for extra input."""
        token = self.peek()

        if token.type == 'SELECT':
            stmt = self.parse_select()
        elif token.type == 'INSERT':
            stmt = self.parse_insert()
        elif token.type == 'UPDATE':
            stmt = self.parse_update()
        elif token.type == 'DELETE':
            stmt = self.parse_delete()
        elif token.type == 'CREATE':
            stmt = self.parse_create()
        elif token.type == 'DROP':
            stmt = self.parse_drop()
        elif token.type == 'ALTER':
            stmt = self.parse_alter()
        else:
            raise SyntaxError(f"Unknown statement start: {token}")

        # 🔒 Check for leftover tokens
        if self.peek().type != 'EOF':
            raise SyntaxError(f"Unexpected token after end of statement: {self.peek()}\n{self.get_pretty_error()}")

        return stmt

    def parse_identifier(self):
        """Parses an identifier or qualified identifier like table.column"""
        ident = self.expect('IDENT').value
        if self.peek().type == 'DOT':
            self.advance()
            second = self.expect('IDENT').value
            return f"{ident}.{second}"
        return ident

    def parse_identifier_list(self):
        """Parse a comma-separated list of identifiers."""
        ids = [self.parse_identifier()]
        while self.peek().type == 'COMMA':
            self.advance()
            ids.append(self.parse_identifier())
        return ids

    def parse_value_list(self):
        """Parse a comma-separated list of values (number or string)."""
        vals = []
        token = self.peek()
        if token.type in ('NUMBER', 'STRING'):
            vals.append(token.value)
            self.advance()
        else:
            raise SyntaxError(f"Expected literal value, found {token}\n{self.get_pretty_error()}")
        while self.peek().type == 'COMMA':
            self.advance()
            token = self.peek()
            if token.type in ('NUMBER', 'STRING'):
                vals.append(token.value)
                self.advance()
            else:
                raise SyntaxError(f"Expected literal value, found {token}\n{self.get_pretty_error()}")
        return vals

    # Expression parsing for WHERE clauses (handles AND/OR and comparisons)
    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.peek().type == 'OR':
            self.advance()
            right = self.parse_and()
            left = ('OR', left, right)
        return left

    def parse_and(self):
        left = self.parse_comparison()
        while self.peek().type == 'AND':
            self.advance()
            right = self.parse_comparison()
            left = ('AND', left, right)
        return left

    def parse_comparison(self):
        if self.peek().type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect('RPAREN')
            return expr

        left = self.parse_identifier()
        peeked = self.peek()

        # Handle IS [NOT] NULL
        if peeked.type == 'IS':
            self.advance()
            if self.peek().type == 'NOT':
                self.advance()
                self.expect('NULL')
                return 'IS NOT NULL', left
            else:
                self.expect('NULL')
                return 'IS NULL', left

        if peeked.type != 'OP':
            raise SyntaxError(f"Expected comparison operator, found {peeked}\n{self.get_pretty_error()}")
        op = peeked.value
        self.advance()

        token = self.peek()
        if token.type in ('NUMBER', 'STRING'):
            right = token.value
            self.advance()
        elif token.type == 'IDENT':
            right = self.parse_identifier()
        else:
            raise SyntaxError(f"Expected identifier or literal after operator, found {token}\n{self.get_pretty_error()}")

        return op, left, right

    def parse_constraints(self):
        """Parse one or more column constraints."""
        """It will parse nothing without a fail if there are no constraints"""
        constraints = []
        while True:
            token = self.peek()

            if token.type == 'NOT':
                self.advance()
                self.expect('NULL')
                if 'NOT NULL' in constraints:
                    raise SyntaxError(f"Duplicate constraint: NOT NULL\n{self.get_pretty_error(adjust_pos=-2)}")
                constraints.append('NOT NULL')

            elif token.type == 'PRIMARY':
                self.advance()
                self.expect('KEY')
                if 'PRIMARY KEY' in constraints:
                    raise SyntaxError(f"Duplicate constraint: PRIMARY KEY\n{self.get_pretty_error(adjust_pos=-2)}")
                constraints.append('PRIMARY KEY')

            elif token.type == 'FOREIGN':
                self.advance()
                self.expect('KEY')
                if 'FOREIGN KEY' in constraints:
                    raise SyntaxError(f"Duplicate constraint: FOREIGN KEY\n{self.get_pretty_error(adjust_pos=-2)}")
                constraints.append('FOREIGN KEY')

            elif token.type == 'UNIQUE':
                self.advance()
                if 'UNIQUE' in constraints:
                    raise SyntaxError(f"Duplicate constraint: UNIQUE\n{self.get_pretty_error(adjust_pos=-1)}")
                constraints.append('UNIQUE')
            elif token.type == 'DEFAULT':
                self.advance()
                options = ('NUMBER', 'STRING')
                if self.peek().type not in options:
                    raise SyntaxError(f"Default value must be: {format_options(options)}\n{self.get_pretty_error()}")
                default_value = self.peek().value
                self.advance()
                constraint = f'DEFAULT {default_value}'
                if any(c.startswith('DEFAULT') for c in constraints):
                    raise SyntaxError(f"Duplicate DEFAULT constraint\n{self.get_pretty_error(adjust_pos=-1)}")
                constraints.append(constraint)
            else:
                break  # No more constraints
        return constraints

    def parse_order_by(self):
        self.expect('ORDER')
        self.expect('BY')
        orderings = []
        while True:
            columns = self.parse_identifier_list()
            peeked = self.peek()
            if peeked.type not in ('ASC', 'DESC'):
                raise SyntaxError(f"Expected 'ASC' or 'DESC', found {self.peek().type}\n{self.get_pretty_error()}")
            direction = peeked.type
            self.advance()
            orderings.append((columns, direction))
            if self.peek().type != 'COMMA':
                break
            self.advance()  # skip comma
        return orderings

    def parse_assignments(self):
        assignments = []

        while True:
            col = self.parse_identifier()
            self.expect('=')
            token = self.peek()
            if token.type in ('NUMBER', 'STRING'):
                val = token.value
                self.advance()
            elif token.type == 'IDENT':
                val = self.parse_identifier()
            else:
                raise SyntaxError(f"Expected value in assignment, found {token}\n{self.get_pretty_error()}")
            assignments.append((col, val))

            if self.peek().type != 'COMMA':
                break
            self.advance()  # skip comma

        return assignments

    def parse_column_type(self):
        """Parses a simple column type without size"""
        token = self.peek()
        if token.type in self.tokenizer.column_types:
            self.advance()
            return token.type
        raise SyntaxError(f"Expected column type ({', '.join(self.tokenizer.column_types)}), found {token.type}\n{self.get_pretty_error()}")

    # ===========================================
    # ------------ Statement parsers ------------
    # ===========================================

    def parse_select(self):
        """SELECT <columns> FROM <table> [JOIN <table> ON <expr>]... [WHERE <expr>] [ORDER BY <column> ASC|DESC]"""
        self.expect('SELECT')
        if self.peek().type == 'STAR':
            self.advance()
            columns = ['*']
        else:
            columns = self.parse_identifier_list()

        self.expect('FROM')
        tables = [self.parse_identifier()]
        while self.peek().type == 'COMMA':
            self.advance()
            tables.append(self.parse_identifier())

        joins = []
        while self.peek().type == 'JOIN':
            self.advance()
            join_table = self.parse_identifier()
            self.expect('ON')
            join_condition = self.parse_expression()
            joins.append((join_table, join_condition))

        where_expr = None
        if self.peek().type == 'WHERE':
            self.advance()
            where_expr = self.parse_expression()

        order_by = None
        if self.peek().type == 'ORDER':
            order_by = self.parse_order_by()

        return SelectStmt(columns, tables, joins, where_expr, order_by)

    def parse_insert(self):
        """INSERT INTO <table> (<columns>) VALUES (<values>)"""
        self.expect('INSERT')
        self.expect('INTO')

        table = self.parse_identifier()

        self.expect('(')
        columns = self.parse_identifier_list()
        self.expect(')')

        self.expect('VALUES')

        self.expect('(')
        values = self.parse_value_list()
        self.expect(')')

        return InsertStmt(table, columns, values)

    def parse_update(self):
        """UPDATE <table> SET <column>=<value> [, <column>=<value> ...] [WHERE <condition>]"""
        self.expect('UPDATE')
        table = self.parse_identifier()
        self.expect('SET')
        assignments = self.parse_assignments()

        where_expr = None
        if self.peek().type == 'WHERE':
            self.advance()
            where_expr = self.parse_expression()
        return UpdateStmt(table, assignments, where_expr)

    def parse_delete(self):
        """DELETE FROM <table> [WHERE <condition>]"""
        self.expect('DELETE')
        if self.peek().type == 'FROM':
            self.advance()
        table = self.parse_identifier()

        where_expr = None
        if self.peek().type == 'WHERE':
            self.advance()
            where_expr = self.parse_expression()
        return DeleteStmt(table, where_expr)

    def parse_create(self):
        """CREATE TABLE <table_name> (<column_name1> <data_type1> <constraints>, <column_name2> <data_type2> <constraints> ...)"""
        self.expect('CREATE')
        self.expect('TABLE')
        table = self.parse_identifier()
        self.expect('(')

        columns = []
        while True:
            col_name = self.parse_identifier()
            col_type = self.parse_column_type()

            constraints = self.parse_constraints()
            columns.append((col_name, col_type, constraints))

            if self.peek().type != 'COMMA':
                break
            self.advance()  # skip comma

        self.expect(')')
        return CreateStmt(table, columns)

    def parse_drop(self):
        # drop index not supported
        """DROP TABLE <table_name>"""
        self.expect('DROP')
        self.expect('TABLE')
        table = self.parse_identifier()
        return DropStmt(table)

    def parse_alter(self):
        """
        ALTER TABLE <table_name>
        [ADD COLUMN <column_name> <data_type> [<constraints>]]
          | [DROP COLUMN <column_name>]
          | [RENAME COLUMN <old_name> TO <new_name>]
          | [MODIFY COLUMN <column_name> <new_data_type> [<constraints>]]
        """
        self.expect('ALTER')
        self.expect('TABLE')

        table = self.parse_identifier()
        expected = ['ADD', 'DROP', 'RENAME', 'MODIFY']
        if self.peek().type not in expected:
            raise SyntaxError(f"Expected {format_options(expected)}, found {self.peek()}\n{self.get_pretty_error()}")

        action = self.peek().type
        self.advance()
        self.expect('COLUMN')

        if action == 'ADD':
            col_name = self.parse_identifier()
            col_type = self.parse_column_type()
            constraints = self.parse_constraints()
            return AlterStmt(table, action, (col_name, col_type, constraints))

        elif action == 'DROP':
            col_name = self.parse_identifier()
            peeked = self.peek()
            drop_type = "RESTRICT"
            if peeked.type in ('CASCADE', 'RESTRICT'):
                self.advance()
                drop_type = peeked.type
            return AlterStmt(table, action, (col_name, drop_type))

        elif action == 'RENAME':
            old_name = self.parse_identifier()
            self.expect('TO')
            new_name = self.parse_identifier()
            return AlterStmt(table, action, (old_name, new_name))

        elif action == 'MODIFY':
            col_name = self.parse_identifier()
            col_type = self.parse_column_type()
            constraints = self.parse_constraints()
            return AlterStmt(table, action, (col_name, col_type, constraints))


# sql = "SELECT users.id, orders.amount FROM users JOIN orders ON users.id = orders.user_id WHERE orders.amount > 100 and ala = 'name' ORDER BY orders.amount ASC, orders.name DESC"
# sql = "INSERT INTO Customers (CustomerName, ContactName, Address, City, PostalCode, Country) VALUES ('Cardinal', 'Tom B. Erichsen', 'Skagen 21', 'Stavanger', '4006', 'Norway')"
# sql = "UPDATE users SET name = 'Alice Smith', email = 'alice.smith@example.com' WHERE id is not null AND name = 1"
# sql = "DELETE FROM users WHERE age < 18"
sql = "CREATE TABLE users (id NUMBER PRIMARY KEY, name TEXT NOT NULL UNIQUE, email TEXT NOT NULL UNIQUE, age NUMBER DEFAULT 1)"
# sql = "DROP TABLE users"
# sql = "ALTER TABLE employees ADD COLUMN department TEXT NOT NULL PRIMARY KEY UNIQUE FOREIGN KEY DEFAULT '1'"
# sql = "ALTER TABLE employees DROP COLUMN salary CASCADE1"
# sql = "ALTER TABLE employees RENAME COLUMN nam1 TO name2"
# sql = "ALTER TABLE employees MODIFY COLUMN age NUMBER NOT NULL"
ast = Parser(sql).parse()
print(ast)
