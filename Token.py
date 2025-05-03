class Token:
    def __init__(self, type, value, offset):
        self.type = type  # e.g. 'IDENT', 'NUMBER', 'STRING' or a keyword like 'SELECT'
        self.value = value
        self.length = len(value)
        self.offset = offset

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"
