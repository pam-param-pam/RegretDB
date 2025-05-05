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
    def __init__(self, message, word, sql_stmt=None):
        self.message = message
        self.word = word
        self.sql_stmt = sql_stmt
        super().__init__(message)

    def __str__(self):
        underline = [' ' for _ in self.sql_stmt]
        word_len = len(self.word)
        idx = 0

        while idx < len(self.sql_stmt):
            idx = self.sql_stmt.find(self.word, idx)
            if idx == -1:
                break

            before = self.sql_stmt[idx - 1] if idx > 0 else ''
            after = self.sql_stmt[idx + word_len] if idx + word_len < len(self.sql_stmt) else ''
            if before == "'" and after == "'":
                idx += word_len
                continue

            for i in range(word_len):
                if idx + i < len(underline):
                    underline[idx + i] = '^'
            idx += word_len

        underline_str = ''.join(underline)
        return f"{self.message}\n{self.sql_stmt}\n{underline_str}"
