class Identifier:
    def __init__(self, type, value):
        self.type = type  # column, table or NEW_COLUMN for alter rename statement
        self.value = value

    def __str__(self):
        return f"{self.type}({self.value})"

    def __repr__(self):
        return self.value

class Literal:
    def __init__(self, type, value, size=None):
        self.type = type  # text, integer, blob or boolean
        self.value = value
        self.size = size  # text and blob require size

    def __str__(self):
        return f"{self.type}({self.value})"

    def __repr__(self):
        return f"{self.type}({self.value})"
