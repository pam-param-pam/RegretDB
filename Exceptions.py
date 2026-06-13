from utility import get_pretty_error


class RegretDBError(Exception):
    """Base class for all exceptions"""
    def __init__(self, message, token=None, line=None):
        super().__init__(message)
        self.token = token
        self.line = line

    def __str__(self):
        base = super().__str__()
        if self.token or self.line:
            return f"{base} (Token: {self.token}, Line: {self.line})"
        return base

class SimpleSQLSyntaxError(RegretDBError):
    def __init__(self, message, adjust_pos=0, tokens_num=1):
        self.message = message
        self.adjust_pos = adjust_pos
        self.tokens_num = tokens_num
        super().__init__(message)

    def __str__(self):
        return self.message

class SQLSyntaxError(RegretDBError):
    def __init__(self, message, sql, tokens, pos, adjust_pos=0, tokens_num=1):
        self.message = message
        self.sql = sql
        self.tokens = tokens
        self.pos = pos
        self.adjust_pos = adjust_pos
        self.tokens_num = tokens_num
        super().__init__(message)

    def __str__(self):
        return self.message + "\n" + get_pretty_error(self.sql, self.tokens, self.pos, self.adjust_pos, self.tokens_num)

class ExecutingError(RegretDBError):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class IntegrityError(RegretDBError):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class PreProcessorError(RegretDBError):
    def __init__(self, message, position=None):
        self.message = message
        self.position = position
        self.sql_stmt = None
        super().__init__(message)

    def __str__(self):
        if not self.position or not self.sql_stmt:
            return self.message
        return self.message + "\n" + self.sql_stmt + "\n" + self.position.offset * " " + "^" * self.position.length


