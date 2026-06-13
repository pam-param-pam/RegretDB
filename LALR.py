import re
from typing import List

from ASTNodes.AlterNodes import AlterAddStmt, AlterDropStmt, AlterRenameStmt, AlterModifyStmt
from ASTNodes.CreateNode import CreateStmt
from ASTNodes.DeleteNode import DeleteStmt
from ASTNodes.DropNode import DropStmt
from ASTNodes.InsertNode import InsertStmt
from ASTNodes.SelectNode import SelectStmt
from ASTNodes.UpdateNode import UpdateStmt
from Exceptions import SQLSyntaxError, SimpleSQLSyntaxError
from Operators.LogicalOperators import OR, AND, IS_NOT_NULL, IS_NULL, LE, GE, LT, GT, NE, EG, NOT, BOOL, Like, Between
from TokenTypes import Identifier, Literal, ConstraintSpec
from utility import format_options, parse_boolean

class Position:
    def __init__(self, offset, length):
        self.offset = offset
        self.length = length

        if offset < 0:
            raise ValueError("offset cannot < 0")

        if length < 0:
            raise ValueError("length cannot < 0")

    def __str__(self):
        return f"Position[offset={self.offset}, length={self.length}]"

class Token:
    def __init__(self, type, value, offset):
        self.type = type  # e.g. 'IDENTIFIER', 'NUMBER', 'TEXT' or a keyword like 'SELECT'
        self.value = value
        self.length = len(value)
        self.offset = offset
        if self.type == 'TEXT':
            self.offset += 1

    @property
    def position(self):
        return Position(self.offset, self.length)

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
            ('MISMATCH', r'.'),  # Any other character
        ]
        self.tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
        self.column_types = [
            'TEXT', 'NUMBER', 'BOOLEAN'
        ]
        self.keywords = [
                            'SELECT', 'FROM', 'WHERE', 'ORDER', 'BY', 'ASC', 'DESC',
                            'INSERT', 'INTO', 'VALUES',
                            'UPDATE', 'SET',
                            'DELETE',
                            'CREATE', 'TABLE',
                            'DROP',
                            'ALTER', 'ADD', 'RENAME', 'MODIFY', 'CASCADE', 'RESTRICT',
                            'AND', 'OR', 'IS', 'NOT', 'NULL', 'FALSE', 'TRUE',
                            'PRIMARY', 'FOREIGN', 'KEY', 'UNIQUE', 'DEFAULT',
                            'LIKE', 'BETWEEN'
                        ] + self.column_types

    def tokenize(self, sql):
        get_token = re.compile(self.tok_regex).match
        pos = 0
        tokens = []
        while pos < len(sql):
            m = get_token(sql, pos)
            if not m:
                raise SimpleSQLSyntaxError(f"Illegal character at position {pos}", adjust_pos=pos)
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
                raise SimpleSQLSyntaxError(f"Unexpected character {lexeme!r} at position {pos}", adjust_pos=pos)
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

    def expect(self, type_or_value: str):
        """Expect a token of given type or value, and consume it."""
        token = self.peek()
        if token.type == type_or_value or token.value == type_or_value:
            self.advance()
            return token
        else:
            raise SimpleSQLSyntaxError(f"Expected '{type_or_value}' instead found {token}")

    def expect_multiple(self, type_or_values: List[str]):
        """Expect the next token to match one of the given types or values.
        Consumes and returns the token, or raises an error with the list of expected options.
        """
        token = self.peek()
        for t_or_v in type_or_values:
            if token.type == t_or_v or token.value == t_or_v:
                self.advance()
                return token
        expected = ', '.join(repr(x) for x in type_or_values)
        raise SimpleSQLSyntaxError(f"Expected one of {expected}, found {token}")

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
                raise SimpleSQLSyntaxError(f"Unknown statement start: {token}")

            # Check for leftover tokens
            if self.peek().type != 'EOF':
                raise SimpleSQLSyntaxError(f"Unexpected token after end of statement: {self.peek()}")

            return stmt
        except SimpleSQLSyntaxError as e:
            raise SQLSyntaxError(message=e.message, sql=self.sql, tokens=self.tokens, pos=self.pos, adjust_pos=e.adjust_pos, tokens_num=e.tokens_num)

    def parse_literal(self) -> Literal:
        token = self.peek()
        if token.type == 'NUMBER':
            self.advance()
            return Literal(type=token.type, value=int(token.value), position=token.position)
        elif token.type == 'BOOLEAN':
            self.advance()
            return Literal(type=token.type, value=parse_boolean(token.value), position=token.position)
        elif token.type == 'TEXT':
            self.advance()
            return Literal(type=token.type, value=token.value, position=token.position)
        elif token.type == 'NULL':
            self.advance()
            return Literal(type=token.type, value=None, position=token.position)
        else:
            raise SimpleSQLSyntaxError(f"Expected literal value, found {token}")

    def parse_column(self):
        column = self.parse_identifier('COLUMN')
        return column

    def parse_columns(self, allow_partial_dot: bool = False):
        columns = self.parse_identifier_list('COLUMN', allow_partial_dot)
        return columns

    def parse_table(self):
        return self.parse_identifier('TABLE')

    def parse_tables(self):
        return self.parse_identifier_list('TABLE')

    def parse_identifier(self, identifier_type, allow_partial_dot: bool = False):
        """Parses an identifier or qualified identifier like table.column"""
        identifier_token = self.expect('IDENTIFIER')
        if self.peek().type == 'DOT':
            self.advance()
            if self.peek().type == "STAR" and allow_partial_dot:
                token = self.peek()
                self.advance()
                position = token.position
                position.length += 2
                return Identifier(type=identifier_type, value=token.value, position=position)

            column_token = self.expect('IDENTIFIER')
            length = identifier_token.length+column_token.length+1
            return Identifier(type=identifier_type, value=f"{identifier_token.value}.{column_token.value}", position=Position(identifier_token.offset, length=length))
        return Identifier(type=identifier_type, value=identifier_token.value, position=identifier_token.position)

    def parse_identifier_list(self, identifier_type, allow_partial_dot: bool = False):
        """Parse a comma-separated list of identifiers. At least 1 must exist"""
        ids = [self.parse_identifier(identifier_type, allow_partial_dot)]
        while self.peek().type == 'COMMA':
            self.advance()
            ids.append(self.parse_identifier(identifier_type, allow_partial_dot))
        return ids

    def parse_value_list(self) -> List[Literal]:
        """Parse a comma-separated list of values"""
        literals = [self.parse_literal()]

        while self.peek().type == 'COMMA':
            self.advance()
            literals.append(self.parse_literal())
        return literals

    def _make_position(self, start_idx: int, end_idx: int) -> Position:
        """Create a Position that spans from token start_idx to token end_idx-1."""
        start_token = self.tokens[start_idx]
        end_token = self.tokens[end_idx - 1]
        start = start_token.offset
        end = end_token.offset + len(end_token.value)
        return Position(start, end - start)

    def parse_fk_actions(self) -> tuple[str, str]:
        """
        Parse optional ON DELETE and ON UPDATE clauses.
        Returns (on_delete_action, on_update_action) as strings.
        Defaults are 'RESTRICT' for both.
        """
        on_delete = 'RESTRICT'
        on_update = 'RESTRICT'

        while self.peek().value == 'ON':
            self.advance()  # consume 'ON'
            action_type_token = self.expect_multiple(['DELETE', 'UPDATE'])
            action_type = action_type_token.type

            action_token = self.expect_multiple(['RESTRICT', 'CASCADE', 'SET'])
            if action_token.value == 'SET':
                self.expect('NULL')
                action = 'SET NULL'
            else:
                action = action_token.value

            if action_type == 'DELETE':
                on_delete = action
            else:
                on_update = action

        return on_delete, on_update

    def parse_constraints(self) -> List[ConstraintSpec]:
        """Parse one or more column constraints.
           It will parse nothing without a fail if there are no constraints"""

        constraints = []
        while True:
            token = self.peek()
            if token.type == 'NOT':
                start_idx = self.pos
                self.advance()
                self.expect('NULL')
                end_idx = self.pos
                pos = self._make_position(start_idx, end_idx)
                if any(c.type == 'NOT NULL' for c in constraints):
                    raise SimpleSQLSyntaxError("Duplicate constraint: NOT NULL", adjust_pos=-2, tokens_num=2)
                constraints.append(ConstraintSpec(type='NOT NULL', position=pos))

            elif token.type == 'PRIMARY':
                start_idx = self.pos
                self.advance()
                self.expect('KEY')
                end_idx = self.pos
                pos = self._make_position(start_idx, end_idx)
                if any(c.type == 'PRIMARY KEY' for c in constraints):
                    raise SimpleSQLSyntaxError("Duplicate constraint: PRIMARY KEY", adjust_pos=-2, tokens_num=2)
                constraints.append(ConstraintSpec(type='PRIMARY KEY', position=pos))

            elif token.type == 'FOREIGN':
                start_idx = self.pos
                self.advance()
                self.expect('KEY')
                self.expect('REFERENCES')
                table = self.parse_table()
                self.expect('(')
                column = self.parse_column()
                self.expect(')')

                if any(c.type == 'FOREIGN KEY' for c in constraints):
                    raise SimpleSQLSyntaxError("Duplicate constraint: FOREIGN KEY", adjust_pos=-2, tokens_num=2)

                on_delete, on_update = self.parse_fk_actions()

                end_idx = self.pos
                pos = self._make_position(start_idx, end_idx)
                constraints.append(ConstraintSpec(
                    type='FOREIGN KEY',
                    arg1=f"{table.value}.{column.value}",
                    on_delete=on_delete,
                    on_update=on_update,
                    position=pos
                ))

            elif token.type == 'UNIQUE':
                start_idx = self.pos
                self.advance()
                end_idx = self.pos
                pos = self._make_position(start_idx, end_idx)
                if any(c.type == 'UNIQUE' for c in constraints):
                    raise SimpleSQLSyntaxError("Duplicate constraint: UNIQUE", adjust_pos=-1)
                constraints.append(ConstraintSpec(type='UNIQUE', position=pos))

            elif token.type == 'DEFAULT':
                start_idx = self.pos
                self.advance()
                default_value = self.parse_literal()
                end_idx = self.pos
                pos = self._make_position(start_idx, end_idx)
                if any(c.type == 'DEFAULT' for c in constraints):
                    raise SimpleSQLSyntaxError("Duplicate DEFAULT constraint", adjust_pos=-1)
                constraints.append(ConstraintSpec(type='DEFAULT', arg1=default_value, position=pos))

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
                raise SimpleSQLSyntaxError(f"Expected 'ASC' or 'DESC', found {self.peek().type}")
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

    def parse_column_type(self) -> Identifier:
        """Parses column type without size"""
        peeked = self.peek()
        if peeked.type in self.tokenizer.column_types:
            self.advance()
            return peeked
        raise SimpleSQLSyntaxError(f"Expected column type ({format_options(self.tokenizer.column_types)}), found {peeked}")

    def parse_expression(self):
        """not > and > or"""
        return self.parse_or()  # lowest precedence

    def parse_primary(self):
        """Parse a literal, column, or parenthesized expression."""
        if self.peek().type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect(')')
            return expr
        if self.peek().type in ('NUMBER', 'TEXT', 'NULL', 'BOOLEAN'):
            return self.parse_literal()
        return self.parse_column()

    def parse_comparison(self):
        # Handle parenthesized expression
        if self.peek().type == 'LPAREN':
            self.advance()
            expr = self.parse_expression()
            self.expect(')')
            return expr

        # Parse a primary: literal or column
        token = self.peek()
        if token.type in ('NUMBER', 'TEXT', 'NULL', 'BOOLEAN'):
            primary = self.parse_literal()
        else:
            primary = self.parse_column()

        # Handle IS NULL / IS NOT NULL
        if self.peek().type == 'IS':
            self.advance()
            if self.peek().type == 'NOT':
                self.advance()
                self.expect('NULL')
                return IS_NOT_NULL(primary)
            else:
                self.expect('NULL')
                return IS_NULL(primary)

        # Handle Like
        if self.peek().type == 'LIKE':
            self.advance()
            token = self.expect('TEXT')
            right = Literal(type=token.type, value=token.value, position=token.position)
            return Like(primary, right)

        # Handle between
        if self.peek().type == 'BETWEEN':
            self.advance()
            low = self.parse_primary()
            self.expect('AND')
            high = self.parse_primary()
            return Between(primary, low, high)

        # Handle comparison operators
        if self.peek().type == 'OP':
            op = self.peek().value
            op_class = self.OPERATOR_MAP.get(op)
            if not op_class:
                raise SimpleSQLSyntaxError(f"Unknown operator '{op}'")
            self.advance()
            right = self.parse_primary()  # right side is a primary (no AND/OR)
            return op_class(primary, right)

        # Only BOOLEAN literals are allowed as standalone
        if isinstance(primary, Literal) and primary.type == 'BOOLEAN':
            return BOOL(primary.value)

        # Everything else (column, number, text, null) is rejected
        raise SimpleSQLSyntaxError(f"Invalid expression in WHERE clause: {primary}. Expected Bool like value")

    def parse_not(self):
        if self.peek().type == 'NOT':
            self.advance()
            operand = self.parse_not()  # allow nested NOT
            return NOT(operand)
        return self.parse_comparison()

    def parse_and(self):
        left = self.parse_not()
        while self.peek().type == 'AND':
            self.advance()
            right = self.parse_not()
            left = AND(left, right)
        return left

    def parse_or(self):
        left = self.parse_and()
        while self.peek().type == 'OR':
            self.advance()
            right = self.parse_and()
            left = OR(left, right)
        return left

    # ===========================================
    # ------------ Statement parsers ------------
    # ===========================================

    def parse_select(self):
        """SELECT <columns> FROM <table> [WHERE <expr>] [ORDER BY <column> ASC|DESC]"""
        self.expect('SELECT')
        if self.peek().type == 'STAR':
            token = self.peek()
            columns = [Identifier(type='COLUMN', value="*", position=token.position)]
            self.advance()
        else:
            columns = self.parse_columns(allow_partial_dot=True)

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
        """UPDATE <table> SET <column>=<value> [, <column>=<value> ...] [WHERE <condition>] """
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

        columns_spec = []
        while True:
            col_name = self.parse_column()
            col_type = self.parse_column_type()

            constraints = self.parse_constraints()
            columns_spec.append((col_name, col_type, constraints))

            if self.peek().type != 'COMMA':
                break
            self.advance()  # skip comma

        self.expect(')')
        return CreateStmt(table, columns_spec)

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
            raise SimpleSQLSyntaxError(f"Expected {format_options(expected)}, found {self.peek()}")

        action = self.peek().type
        self.advance()
        self.expect('COLUMN')

        if action == 'ADD':
            col_name = self.parse_column()
            col_type = self.parse_column_type()
            constraints = self.parse_constraints()
            return AlterAddStmt(table, (col_name, col_type, constraints))

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

        raise ValueError("Shouldn't reach here")

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
