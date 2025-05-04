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

class SQLSyntaxError(RegretDBError):
    def __init__(self, message, sql=None, tokens=None, pos=None, adjust_pos=None):
        self.message = message
        self.sql = sql
        self.tokens = tokens
        self.pos = pos
        self.adjust_pos = adjust_pos or 0
        super().__init__(message)

    def __str__(self):
        return self.message + "\n" + get_pretty_error(self.sql, self.tokens, self.pos, self.adjust_pos)


class PreProcessorError(RegretDBError):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message
