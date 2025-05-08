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
    def __init__(self, message, word=None, sql_stmt=None):
        self.message = message
        self.word = word
        self.sql_stmt = sql_stmt
        super().__init__(message)

    def __str__(self):
        if not self.word:
            return self.message
        underline = [' ' for _ in self.sql_stmt]
        word_len = len(self.word)
        idx = 0

        while idx < len(self.sql_stmt):
            idx = self.sql_stmt.find(self.word, idx)
            if idx == -1:
                break

            # Characters before and after the match
            before = self.sql_stmt[idx - 1] if idx > 0 else ''
            after = self.sql_stmt[idx + word_len] if idx + word_len < len(self.sql_stmt) else ''

            # Skip if surrounded by single quotes (string literal)
            if before == "'" and after == "'":
                idx += word_len
                continue

            # Skip if part of a longer identifier or dotted identifier
            if before in "._" or before.isalnum() or after in "._" or after.isalnum():
                idx += word_len
                continue

            # Mark the word with ^
            for i in range(word_len):
                if idx + i < len(underline):
                    underline[idx + i] = '^'

            idx += word_len

        underline_str = ''.join(underline)
        return f"{self.message}\n{self.sql_stmt}\n{underline_str}"
