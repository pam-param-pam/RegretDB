import re

from ASTNodes import *
from Exceptions import SQLSyntaxError, RegretDBError
from Operators.LogicalOperators import OR, AND, IS_NOT_NULL, IS_NULL, LE, GE, LT, GT, NE, EG, NOT
from Token import Token
from TokenTypes import Identifier, Literal
from utility import format_options


class Tokenizer:
    def __init__(self):
        token_specification = [
            ('NUMBER', r'\b\d+(?:\.\d*)?'),  # Integer or decimal
            ('STRING', r"'([^']*)'"),  # Single-quoted string
            ('BOOLEAN', r'(?i)\bTRUE\b|\bFALSE\b'),  # Case-insensitive match
            ('BLOB', r'b\'[0-9A-Fa-f]+\'|x\'[0-9A-Fa-f]+\''),  # BLOB (e.g., b'1A2B')
            ('IDENTIFIER', r'[A-Za-z_][A-Za-z_0-9]*'),  # Identifiers
            ('OP', r'<=|>=|!=|=|<|>'),  # Comparison operators
            ('STAR', r'\*'),
            ('COMMA', r','),
            ('LPAREN', r'\('),
            ('RPAREN', r'\)'),
            ('SEMI', r';'),
            ('SKIP', r'[ \t\n\r]+'),  # Skip whitespace
            ('DOT', r'\.'),
            ('MISMATCH', r'.'),  # Any other character
        ]
        self.tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
        self.column_types = [
            'TEXT', 'NUMBER', 'BLOB', 'BOOL'
        ]
        self.keywords = [
                            'SELECT', 'FROM', 'WHERE', 'ORDER', 'BY', 'ASC', 'DESC',
                            'INSERT', 'INTO', 'VALUES',
                            'UPDATE', 'SET',
                            'DELETE',
                            'CREATE', 'TABLE',
                            'DROP',
                            'ALTER', 'ADD', 'DROP', 'RENAME', 'MODIFY', 'CASCADE', 'RESTRICT',
                            'AND', 'OR', 'IS', 'NOT', 'NULL', 'FALSE', 'TRUE',  # operators
                            'PRIMARY', 'FOREIGN', 'KEY', 'UNIQUE', 'DEFAULT'  # constraints
                        ] + self.column_types

    def tokenize(self, sql):
        get_token = re.compile(self.tok_regex).match
        pos = 0
        tokens = []
        while pos < len(sql):
            m = get_token(sql, pos)
            if not m:
                raise SQLSyntaxError(f"Illegal character at position {pos}", adjust_pos=pos)
            typ = m.lastgroup
            lexeme = m.group(typ)
            if typ == 'STRING':
                # Strip the quotes: lexeme includes the quotes, m.group(1) is content
                tokens.append(Token('STRING', lexeme[1:-1], pos))
            elif typ == 'IDENTIFIER':
                val = lexeme.upper()
                # Recognize SQL keywords (we store the type as the uppercase keyword)
                if val in self.keywords:
                    tokens.append(Token(val, val, pos))
                else:
                    tokens.append(Token('IDENTIFIER', lexeme, pos))
            elif typ == 'SKIP':
                pass  # ignore whitespace
            elif typ != 'MISMATCH':
                tokens.append(Token(typ, lexeme, pos))
            else:  # MISMATCH
                raise SQLSyntaxError(f"Unexpected character {lexeme!r} at position {pos}", adjust_pos=pos)
            pos = m.end()
        return tokens


class Parser:
    def __init__(self, sql):
        self.tokenizer = Tokenizer()
        self.tokens = []
        self.pos = 0
        self.sql = sql
        self.OPERATOR_MAP = {
            '=': EG,
            '!=': NE,
            '>': GT,
            '<': LT,
            '>=': GE,
            '<=': LE
        }

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
            raise SQLSyntaxError(f"Expected '{type_or_value}' instead found {token}")

    def parse(self):
        """Parse the next statement based on the leading keyword and check for extra input."""
        try:
            self.tokens = self.tokenizer.tokenize(self.sql)
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
                raise SQLSyntaxError(f"Unknown statement start: {token}")

            # 🔒 Check for leftover tokens
            if self.peek().type != 'EOF':
                raise SQLSyntaxError(f"Unexpected token after end of statement: {self.peek()}")

            return stmt
        except RegretDBError as e:
            e.sql = self.sql
            e.tokens = self.tokens
            e.pos = self.pos
            raise e

    def parse_literal(self):
        token = self.peek()
        if token.type in ('NUMBER', 'STRING', 'BOOLEAN'):
            self.advance()
            return Literal(type=token.type, value=token.value)
        else:
            raise SQLSyntaxError(f"Expected literal value, found {token}")

    def parse_identifier(self, identifier_type):
        """Parses an identifier or qualified identifier like table.column"""
        identifier = self.expect('IDENTIFIER').value
        if self.peek().type == 'DOT':
            self.advance()
            second = self.expect('IDENTIFIER').value
            return Identifier(type=identifier_type, value=f"{identifier}.{second}")
        return Identifier(type=identifier_type, value=identifier)

    def parse_identifier_list(self, identifier_type):
        """Parse a comma-separated list of identifiers."""
        ids = [self.parse_identifier(identifier_type)]
        while self.peek().type == 'COMMA':
            self.advance()
            ids.append(self.parse_identifier(identifier_type))
        return ids

    def parse_value_list(self):
        """Parse a comma-separated list of values"""
        values = []
        literal = self.parse_literal()
        values.append(literal)

        while self.peek().type == 'COMMA':
            self.advance()
            literal = self.parse_literal()
            values.append(literal)
        return values

    def parse_constraints(self):
        """Parse one or more column constraints.
           It will parse nothing without a fail if there are no constraints"""
        constraints = []
        while True:
            token = self.peek()

            if token.type == 'NOT':
                self.advance()
                self.expect('NULL')
                if 'NOT NULL' in constraints:
                    raise SQLSyntaxError(f"Duplicate constraint: NOT NULL", adjust_pos=-2)
                constraints.append('NOT NULL')

            elif token.type == 'PRIMARY':
                self.advance()
                self.expect('KEY')
                if 'PRIMARY KEY' in constraints:
                    raise SQLSyntaxError(f"Duplicate constraint: PRIMARY KEY", adjust_pos=-2)
                constraints.append('PRIMARY KEY')

            elif token.type == 'FOREIGN':
                self.advance()
                self.expect('KEY')
                if 'FOREIGN KEY' in constraints:
                    raise SQLSyntaxError(f"Duplicate constraint: FOREIGN KEY", adjust_pos=-2)
                constraints.append('FOREIGN KEY')

            elif token.type == 'UNIQUE':
                self.advance()
                if 'UNIQUE' in constraints:
                    raise SQLSyntaxError(f"Duplicate constraint: UNIQUE", adjust_pos=-1)
                constraints.append('UNIQUE')
            elif token.type == 'DEFAULT':
                self.advance()
                default_value = self.parse_literal()
                self.advance()
                constraint = f'DEFAULT {default_value}'
                if any(c.startswith('DEFAULT') for c in constraints):
                    raise SQLSyntaxError(f"Duplicate DEFAULT constraint", adjust_pos=-1)
                constraints.append(constraint)
            else:
                break  # No more constraints
        return constraints

    def parse_order_by(self):
        self.expect('ORDER')
        self.expect('BY')
        orderings = []
        while True:
            columns = self.parse_identifier_list('COLUMN')
            peeked = self.peek()
            if peeked.type not in ('ASC', 'DESC'):
                raise SQLSyntaxError(f"Expected 'ASC' or 'DESC', found {self.peek().type}")
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
            column = self.parse_identifier('COLUMN')
            self.expect('=')
            literal = self.parse_literal()
            assignments.append((column, literal))

            if self.peek().type != 'COMMA':
                break
            self.advance()  # skip comma

        return assignments

    def parse_column_type(self):
        """Parses column type with size if required"""
        peeked = self.peek()
        if peeked.type in self.tokenizer.column_types:
            self.advance()
            if peeked.type in ('TEXT', 'BLOB'):  # need size
                self.expect("(")
                peeked2 = self.peek()
                if peeked2.type != 'NUMBER':
                    raise SQLSyntaxError(f"Expected size, found {peeked2}")
                self.advance()
                size = peeked2.value
                self.expect(")")
                return peeked.type, size
            return peeked.type

        raise SQLSyntaxError(f"Expected column type ({format_options(self.tokenizer.column_types)}), found {peeked}")

    def parse_expression(self):
        """not > and > or"""
        return self.parse_or()  # lowest precedence

    def parse_or(self):
        left = self.parse_and()
        while self.peek().type == 'OR':
            self.advance()
            right = self.parse_and()
            left = OR(left, right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.peek().type == 'AND':
            self.advance()
            right = self.parse_not()
            left = AND(left, right)
        return left

    def parse_not(self):
        if self.peek().type == 'NOT':
            self.advance()
            operand = self.parse_not()
            return NOT(operand)
        return self.parse_comparison()

    def parse_comparison(self):
        if self.peek().type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect(')')
            return expr

        token = self.peek()

        if token.type == 'BOOLEAN':
            self.advance()
            return Literal(type='BOOLEAN', value=token.value)

        left = self.parse_identifier('COLUMN')
        peeked = self.peek()

        if peeked.type == 'IS':
            self.advance()
            if self.peek().type == 'NOT':
                self.advance()
                self.expect('NULL')
                return IS_NOT_NULL(left)
            else:
                self.expect('NULL')
                return IS_NULL(left)

        if peeked.type != 'OP':
            raise SQLSyntaxError(f"Expected comparison operator, found {peeked}")

        op = peeked.value
        op_class = self.OPERATOR_MAP.get(op)
        if not op_class:
            raise SQLSyntaxError(f"Unknown operator '{op}'")

        self.advance()

        token = self.peek()
        try:
            right = self.parse_literal()
        except SQLSyntaxError:
            if token.type == 'IDENTIFIER':
                right = self.parse_identifier('COLUMN')
            else:
                raise SQLSyntaxError(f"Expected identifier or literal after operator, found {token}")

        return op_class(left, right)

    # ===========================================
    # ------------ Statement parsers ------------
    # ===========================================

    def parse_select(self):
        """SELECT <columns> FROM <table> [WHERE <expr>] [ORDER BY <column> ASC|DESC]"""
        self.expect('SELECT')
        if self.peek().type == 'STAR':
            self.advance()
            columns = ['*']
        else:
            columns = self.parse_identifier_list('COLUMN')

        self.expect('FROM')
        tables = self.parse_identifier_list('TABLE')

        where_expr = None
        if self.peek().type == 'WHERE':
            self.advance()
            where_expr = self.parse_expression()

        order_by = None
        if self.peek().type == 'ORDER':
            order_by = self.parse_order_by()

        return SelectStmt(columns, tables, where_expr, order_by)

    def parse_insert(self):
        """INSERT INTO <table> (<columns>) VALUES (<values>)"""
        self.expect('INSERT')
        self.expect('INTO')

        table = self.parse_identifier('TABLE')

        self.expect('(')
        columns = self.parse_identifier_list('COLUMN')
        self.expect(')')

        self.expect('VALUES')

        self.expect('(')
        values = self.parse_value_list()
        self.expect(')')

        return InsertStmt(table, columns, values)

    def parse_update(self):
        """UPDATE <table> SET <column>=<value> [, <column>=<value> ...] [WHERE <condition>]"""
        self.expect('UPDATE')
        table = self.parse_identifier('TABLE')
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
        table = self.parse_identifier('TABLE')

        where_expr = None
        if self.peek().type == 'WHERE':
            self.advance()
            where_expr = self.parse_expression()
        return DeleteStmt(table, where_expr)

    def parse_create(self):
        """CREATE TABLE <table_name> (<column_name1> <data_type1> <constraints>, <column_name2> <data_type2> <constraints> ...)"""
        self.expect('CREATE')
        self.expect('TABLE')
        table = self.parse_identifier('TABLE')
        self.expect('(')

        columns = []
        while True:
            col_name = self.parse_identifier('COLUMN')
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
        """DROP TABLE <table_name> [, <table_name2> ...]"""
        self.expect('DROP')
        self.expect('TABLE')
        tables = self.parse_identifier_list('TABLE')
        return DropStmt(tables)

    def parse_alter(self):
        """ALTER TABLE <table_name> [ADD COLUMN <column_name> <data_type> [<constraints>]]
          | [DROP COLUMN <column_name>]
          | [RENAME COLUMN <old_name> TO <new_name>]
          | [MODIFY COLUMN <column_name> <new_data_type> [<constraints>]]
        """
        self.expect('ALTER')
        self.expect('TABLE')

        table = self.parse_identifier('TABLE')
        expected = ['ADD', 'DROP', 'RENAME', 'MODIFY']
        if self.peek().type not in expected:
            raise SQLSyntaxError(f"Expected {format_options(expected)}, found {self.peek()}")

        action = self.peek().type
        self.advance()
        self.expect('COLUMN')

        if action == 'ADD':
            col_name = self.parse_identifier('COLUMN')
            col_type = self.parse_column_type()
            constraints = self.parse_constraints()
            return AlterStmt(table, action, (col_name, col_type, constraints))

        elif action == 'DROP':
            col_name = self.parse_identifier('COLUMN')
            peeked = self.peek()
            drop_type = "RESTRICT"
            if peeked.type in ('CASCADE', 'RESTRICT'):
                self.advance()
                drop_type = peeked.type
            return AlterStmt(table, action, (col_name, drop_type))

        elif action == 'RENAME':
            old_name = self.parse_identifier('COLUMN')
            self.expect('TO')
            new_name = self.parse_identifier('NEW_COLUMN')
            return AlterStmt(table, action, (old_name, new_name))

        elif action == 'MODIFY':
            col_name = self.parse_identifier('COLUMN')
            col_type = self.parse_column_type()
            constraints = self.parse_constraints()
            return AlterStmt(table, action, (col_name, col_type, constraints))

# sql = "SELECT users.id, orders.amount FR1OM users WHERE (orders.amount > 100 and ala = 'name') or (orders.amount > 200 and ala = 'name1') ORDER BY orders.amount ASC, orders.name DESC"
# sql = "INSERT INTO Customers (CustomerName, ContactName, Address, City, Country) VALUES ('Cardinal', 'Tom B. Erichsen', 'Skagen 21', 'Stavanger', '4006', 'Norway')"
# sql = "UPDATE users SET name = 'Alice Smith', email = 'alice.smith@example.com' WHERE id is not null AND name = 1"
# sql = "DELETE FROM users WHERE age < 18"
# sql = "CREATE TABLE users (id NUMBER PRIMARY KEY, name TEXT NOT NULL UNIQUE, email TEXT NOT NULL UNIQUE, age NUMBER DEFAULT 1)"
# sql = "DROP TABLE users"
# sql = "ALTER TABLE employees ADD COLUMN department TEXT NOT NULL PRIMARY KEY UNIQUE FOREIGN KEY DEFAULT '1'"
# sql = "ALTER TABLE employees DROP COLUMN salary CASCADE1"
# sql = "ALTER TABLE employees RENAME COLUMN nam1 TO name2"
# sql = "ALTER TABLE employees MODIFY COLUMN age TEXT(1) NOT NULL"
# sql = "SELECT users.id, users.name FROM users WHERE false"
# ast = Parser(sql).parse()
# print(ast)
