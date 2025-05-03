import math
import re

from Nodes import *
from Token import Token


# Tokenizer function
def tokenize(sql):
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
        ('DOT', r'\.'),  # <-- Add this line
        ('MISMATCH', r'.'),  # Any other character
    ]
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
    get_token = re.compile(tok_regex).match
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
            keywords = {
                'SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'ORDER', 'BY', 'ASC', 'DESC',
                'INSERT', 'INTO', 'VALUES',
                'UPDATE', 'SET',
                'DELETE',
                'CREATE', 'TABLE',
                'DROP',
                'ALTER',
            }
            if val in keywords:
                tokens.append(Token(val, val, pos))
            else:
                tokens.append(Token('IDENT', lexeme, pos))
        elif typ in ('NUMBER', 'OP', 'STAR', 'COMMA', 'LPAREN', 'RPAREN', 'SEMI', 'DOT'):
            tokens.append(Token(typ, lexeme, pos))
        elif typ == 'SKIP':
            pass  # ignore whitespace
        else:  # MISMATCH
            raise SyntaxError(f"Unexpected character {lexeme!r} at position {pos}")
        pos = m.end()
    return tokens


class Parser:
    def __init__(self, sql):
        self.tokens = tokenize(sql)
        self.pos = 0
        self.sql = sql

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token('EOF', 'EOF', self.pos)

    def advance(self):
        self.pos += 1

    def expect(self, type_or_value):
        """Expect a token of given type or value, and consume it."""
        token = self.peek()
        if token.type == type_or_value or token.value == type_or_value:
            self.advance()
            return token
        else:
            raise SyntaxError(f"Expected {type_or_value}, found {token}\n{self.get_pretty_error()}")

    def get_pretty_error(self):
        try:
            offset = self.tokens[self.pos].offset

            if self.pos + 1 < len(self.tokens):
                next_word_length = self.tokens[self.pos + 1].length
            else:
                next_word_length = self.tokens[self.pos].length
            adjust = math.ceil(next_word_length / 2)
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
        while self.peek().type == 'DOT':
            self.advance()  # skip the dot
            right = self.expect('IDENT').value
            ident = f"{ident}.{right}"
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
        while self.peek().type == ',':
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
        left = self.parse_term()
        while self.peek().type == 'OR':
            self.advance()
            right = self.parse_term()
            left = ('OR', left, right)
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.peek().type == 'AND':
            self.advance()
            right = self.parse_factor()
            left = ('AND', left, right)
        return left

    def parse_factor(self):
        token = self.peek()
        if token.type == '(':
            self.advance()
            expr = self.parse_expression()
            self.expect(')')
            return expr
        # parse comparison: <identifier> <operator> <value|identifier>
        left = self.parse_identifier()
        op_token = self.peek()
        if op_token.type == 'OP':
            op = op_token.value
            self.advance()
        else:
            raise SyntaxError(f"Expected comparison operator, found {op_token}\n{self.get_pretty_error()}")
        token = self.peek()
        if token.type == 'IDENT':
            right = self.parse_identifier()
        elif token.type in ('NUMBER', 'STRING'):
            right = token.value
            self.advance()
        else:
            raise SyntaxError(f"Expected identifier or literal after operator, found {token}\n{self.get_pretty_error()}")
        return op, left, right

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

    # ===========================================
    # ------------ Statement parsers ------------
    # ===========================================

    def parse_select(self):
        """SELECT <columns> FROM <table> [JOIN <table> ON <expr>]... [WHERE <expr>] [ORDER BY <column> [ASC|DESC]]"""
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
        self.expect('INSERT')
        if self.peek().type == 'INTO':
            self.advance()
        table = self.parse_identifier()
        columns = None
        if self.peek().type == '(':
            self.advance()
            columns = self.parse_identifier_list()
            self.expect(')')
        self.expect('VALUES')
        self.expect('(')
        values = self.parse_value_list()
        self.expect(')')
        return InsertStmt(table, columns, values)

    def parse_update(self):
        self.expect('UPDATE')
        table = self.parse_identifier()
        self.expect('SET')
        assignments = []
        # parse first assignment col=val
        col = self.parse_identifier()
        self.expect('=')
        token = self.peek()
        if token.type in ('NUMBER', 'STRING'):
            val = token.value
            self.advance()
        elif token.type == 'IDENT':
            val = self.parse_identifier()
        else:
            raise SyntaxError(f"Expected value in SET, found {token}\n{self.get_pretty_error()}")
        assignments.append((col, val))
        # parse additional assignments
        while self.peek().type == ',':
            self.advance()
            col = self.parse_identifier()
            self.expect('=')
            token = self.peek()
            if token.type in ('NUMBER', 'STRING'):
                val = token.value
                self.advance()
            elif token.type == 'IDENT':
                val = self.parse_identifier()
            else:
                raise SyntaxError(f"Expected value in SET, found {token}\n{self.get_pretty_error()}")
            assignments.append((col, val))
        where_expr = None
        if self.peek().type == 'WHERE':
            self.advance()
            where_expr = self.parse_expression()
        return UpdateStmt(table, assignments, where_expr)

    def parse_delete(self):
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
        self.expect('CREATE')
        if self.peek().type == 'TABLE':
            self.advance()
        table = self.parse_identifier()
        self.expect('(')
        columns = []
        # first column definition
        col_name = self.parse_identifier()
        col_type = self.parse_identifier()
        if self.peek().type == '(':
            self.advance()
            size = self.expect('NUMBER').value
            self.expect(')')
            col_type += f"({size})"
        columns.append((col_name, col_type))
        # additional columns
        while self.peek().type == ',':
            self.advance()
            col_name = self.parse_identifier()
            col_type = self.parse_identifier()
            if self.peek().type == '(':
                self.advance()
                size = self.expect('NUMBER').value
                self.expect(')')
                col_type += f"({size})"
            columns.append((col_name, col_type))
        self.expect(')')
        return CreateStmt(table, columns)

    def parse_drop(self):
        self.expect('DROP')
        if self.peek().type == 'TABLE':
            self.advance()
        table = self.parse_identifier()
        return DropStmt(table)

    def parse_alter(self):
        self.expect('ALTER')
        if self.peek().type == 'TABLE':
            self.advance()
        table = self.parse_identifier()
        if self.peek().type == 'ADD':
            action = 'ADD'
            self.advance()
        elif self.peek().type == 'DROP':
            action = 'DROP'
            self.advance()
        else:
            raise SyntaxError(f"Expected ADD or DROP in ALTER, found {self.peek()}\n{self.get_pretty_error()}")
        if self.peek().type == 'COLUMN':
            self.advance()
        if action == 'ADD':
            col_name = self.parse_identifier()
            col_type = self.parse_identifier()
            if self.peek().type == '(':
                self.advance()
                size = self.expect('NUMBER').value
                self.expect(')')
                col_type += f"({size})"
            return AlterStmt(table, action, (col_name, col_type))
        else:  # DROP
            col_name = self.parse_identifier()
            return AlterStmt(table, action, col_name)


sql = "SELECT users.id, orders.amount FROM users JOIN orders ON users.id = orders.user_id WHERE orders.amount > 100 ORDER BY orders.amount ASC, orders.name DESC"

ast = Parser(sql).parse()
print(ast)
