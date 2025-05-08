import re

from ASTNodes import *
from Exceptions import SQLSyntaxError, RegretDBError
from Operators.LogicalOperators import OR, AND, IS_NOT_NULL, IS_NULL, LE, GE, LT, GT, NE, EG, NOT, BOOL
from TokenTypes import Identifier, Literal, Constraint
from utility import format_options, parse_boolean

class Token:
    def __init__(self, type, value, offset):
        self.type = type  # e.g. 'IDENT', 'NUMBER', 'STRING' or a keyword like 'SELECT'
        self.value = value
        self.length = len(value)
        self.offset = offset

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"

class Tokenizer:
    def __init__(self):
        token_specification = [
            ('BOOLEAN', r'\b[Tt][Rr][Uu][Ee]\b|\b[Ff][Aa][Ll][Ss][Ee]\b'),  # Case-insensitive match
            ('IDENTIFIER', r'[A-Za-z_][A-Za-z_0-9]*'),  # Identifiers
            ('OP', r'<=|>=|!=|=|<|>'),  # Comparison operators
            ('STAR', r'\*'),
            ('COMMA', r','),
            ('LPAREN', r'\('),
            ('RPAREN', r'\)'),
            ('SEMI', r';'),
            ('SKIP', r'[ \t\n\r]+'),  # Skip whitespace
            ('DOT', r'\.'),
            ('NUMBER', r'\b\d+(?:\.\d*)?'),  # Integer or decimal
            ('TEXT', r"'([^']*)'"),  # Single-quoted string
            ('BLOB', r'b\'[0-9A-Fa-f]+\'|x\'[0-9A-Fa-f]+\''),  # BLOB (e.g., b'1A2B')
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
                            'ALTER', 'ADD', 'RENAME', 'MODIFY', 'CASCADE', 'RESTRICT',
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
            if typ == 'TEXT':
                # Strip the quotes: lexeme includes the quotes, m.group(1) is content
                tokens.append(Token('TEXT', lexeme[1:-1], pos))
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
    def __init__(self):
        self.tokenizer = Tokenizer()
        self.tokens = []
        self.pos = 0
        self.sql = None
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

    def parse(self, sql_stmt):
        self.pos = 0
        """Parse the next statement based on the leading keyword and check for extra input."""
        try:
            self.sql = sql_stmt

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
        if token.type == 'NUMBER':
            self.advance()
            return Literal(type=token.type, value=int(token.value))
        elif token.type == 'BOOLEAN':
            self.advance()
            return Literal(type=token.type, value=parse_boolean(token.value))
        elif token.type == 'TEXT':
            self.advance()
            return Literal(type=token.type, value=token.value)
        elif token.type == 'NULL':
            self.advance()
            return Literal(type=token.type, value=None)
        else:
            raise SQLSyntaxError(f"Expected literal value, found {token}")

    def parse_column(self, table_name=None):
        column = self.parse_identifier('COLUMN')
        return column

    def parse_columns(self):
        columns = self.parse_identifier_list('COLUMN')
        return columns

    def parse_table(self):
        return self.parse_identifier('TABLE')

    def parse_tables(self):
        return self.parse_identifier_list('TABLE')

    def parse_identifier(self, identifier_type):
        """Parses an identifier or qualified identifier like table.column"""
        identifier = self.expect('IDENTIFIER').value
        if self.peek().type == 'DOT':
            self.advance()
            if self.peek().type == 'STAR':
                self.advance()
                return Identifier(type=identifier_type, value=f"{identifier}.*")
            else:
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
                if any(constraint.type == 'NOT NULL' for constraint in constraints):
                    raise SQLSyntaxError(f"Duplicate constraint: NOT NULL", adjust_pos=-2)
                constraints.append(Constraint(type='NOT NULL'))

            elif token.type == 'PRIMARY':
                self.advance()
                self.expect('KEY')
                if any(constraint.type == 'PRIMARY KEY' for constraint in constraints):
                    raise SQLSyntaxError(f"Duplicate constraint: PRIMARY KEY", adjust_pos=-2)
                constraints.append(Constraint(type='PRIMARY KEY'))

            elif token.type == 'FOREIGN':
                self.advance()
                self.expect('KEY')
                if any(constraint.type == 'FOREIGN KEY' for constraint in constraints):
                    raise SQLSyntaxError(f"Duplicate constraint: FOREIGN KEY", adjust_pos=-2)

                self.expect('REFERENCES')
                table = self.parse_table()
                self.expect('(')
                column = self.parse_column()
                self.expect(')')
                constraints.append(Constraint(type='FOREIGN KEY', arg1=f"{table.value}.{column.value}"))

            elif token.type == 'UNIQUE':
                self.advance()
                if any(constraint.type == 'UNIQUE' for constraint in constraints):
                    raise SQLSyntaxError(f"Duplicate constraint: UNIQUE", adjust_pos=-1)
                constraints.append(Constraint(type='UNIQUE'))

            elif token.type == 'DEFAULT':
                self.advance()
                default_value = self.parse_literal()
                if any(constraint.type == 'DEFAULT' for constraint in constraints):
                    raise SQLSyntaxError(f"Duplicate DEFAULT constraint", adjust_pos=-1)
                constraints.append(Constraint(type='DEFAULT', arg1=default_value))

            else:
                break
        return constraints

    def parse_order_by(self):
        self.expect('ORDER')
        self.expect('BY')
        orderings = []
        while True:
            column = self.parse_column()
            peeked = self.peek()
            if peeked.type not in ('ASC', 'DESC'):
                raise SQLSyntaxError(f"Expected 'ASC' or 'DESC', found {self.peek().type}")
            direction = peeked.type
            self.advance()
            orderings.append((column, direction))
            if self.peek().type != 'COMMA':
                break
            self.advance()  # skip comma
        return orderings

    def parse_assignments(self):
        assignments = []

        while True:
            column = self.parse_column()
            self.expect('=')
            literal = self.parse_literal()
            assignments.append((column, literal))

            if self.peek().type != 'COMMA':
                break
            self.advance()  # skip comma

        return assignments

    def parse_column_type(self):
        """Parses column type without size"""
        peeked = self.peek()
        if peeked.type in self.tokenizer.column_types:
            self.advance()
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
            return BOOL(token.value)

        left = self.parse_column()
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
                right = self.parse_column()
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
            columns = [Identifier(type='COLUMN', value="*")]
        else:
            columns = self.parse_columns()

        self.expect('FROM')
        tables = self.parse_tables()

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

        table = self.parse_table()

        self.expect('(')
        columns = self.parse_columns()
        self.expect(')')

        self.expect('VALUES')

        self.expect('(')
        values = self.parse_value_list()
        self.expect(')')

        return InsertStmt(table, columns, values)

    def parse_update(self):
        """UPDATE <table> SET <column>=<value> [, <column>=<value> ...] [WHERE <condition>]"""
        self.expect('UPDATE')
        table = self.parse_table()
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
        table = self.parse_table()

        where_expr = None
        if self.peek().type == 'WHERE':
            self.advance()
            where_expr = self.parse_expression()
        return DeleteStmt(table, where_expr)

    def parse_create(self):
        """CREATE TABLE <table_name> (<column_name1> <data_type1> <constraints>, <column_name2> <data_type2> <constraints> ...)"""
        self.expect('CREATE')
        self.expect('TABLE')
        table = self.parse_table()
        self.expect('(')

        columns = []
        while True:
            col_name = self.parse_column()
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
        table = self.parse_table()
        return DropStmt(table)

    def parse_alter(self):
        """ALTER TABLE <table_name> [ADD COLUMN <column_name> <data_type> [<constraints>]]
          | [DROP COLUMN <column_name>]
          | [RENAME COLUMN <old_name> TO <new_name>]
          | [MODIFY COLUMN <column_name> <new_data_type> [<constraints>]]
        """
        self.expect('ALTER')
        self.expect('TABLE')

        table = self.parse_table()
        expected = ['ADD', 'DROP', 'RENAME', 'MODIFY']
        if self.peek().type not in expected:
            raise SQLSyntaxError(f"Expected {format_options(expected)}, found {self.peek()}")

        action = self.peek().type
        self.advance()
        self.expect('COLUMN')

        if action == 'ADD':
            col_name = self.parse_column()
            col_type = self.parse_column_type()
            constraints = self.parse_constraints()
            return AlterAddStmt(table, col_name, col_type, constraints)

        elif action == 'DROP':
            col_name = self.parse_column()
            peeked = self.peek()
            drop_type = "RESTRICT"
            if peeked.type in ('CASCADE', 'RESTRICT'):
                self.advance()
                drop_type = peeked.type
            return AlterDropStmt(table, col_name, drop_type)

        elif action == 'RENAME':
            old_name = self.parse_column()
            self.expect('TO')
            new_name = self.parse_identifier('COLUMN')
            return AlterRenameStmt(table, old_name, new_name)

        elif action == 'MODIFY':
            col_name = self.parse_column()
            new_col_type = self.parse_column_type()
            new_constraints = self.parse_constraints()
            return AlterModifyStmt(table, col_name, new_col_type, new_constraints)

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
# ast = Parser().parse(sql)
# print(ast)
