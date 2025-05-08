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

class Constraint:
    def __init__(self, type, arg1=None, arg2=None):
        self.type = type  # PRIMARY KEY, NOT NULL, FOREIGN KEY, UNIQUE, DEFAULT
        self.arg1 = arg1  # Used in default and in foreign key
        self.arg2 = arg2  # Used in foreign key on update

    def __str__(self):
        if self.arg1:
            return f"{self.type}({self.arg1})"
        return f"{self.type}"

    def __repr__(self):
        return self.__str__()

    def can_be_null(self):
        pass

    def must_be_unique(self):
        pass


