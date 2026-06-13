class Identifier:
    def __init__(self, type, value, position):
        self.type = type
        self.value = value
        self.position = position

    def __str__(self):
        return f"{self.type}({self.value})"

    def __repr__(self):
        return self.value

class Literal:
    def __init__(self, type, value, position, size=None):
        self.type = type  # text, integer, blob or boolean
        self.value = value
        self.size = size  # text and blob require size
        self.position = position

    def __str__(self):
        return f"{self.type}({self.value})"

    def __repr__(self):
        return f"{self.type}({self.value})"

class ConstraintSpec:
    def __init__(self, type, position, arg1=None, arg2=None):
        self.type = type  # PRIMARY KEY, NOT NULL, FOREIGN KEY, UNIQUE, DEFAULT
        self.position = position
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


