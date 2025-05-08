from abc import ABC, abstractmethod


class Operator(ABC):
    def __init__(self, left, right=None):
        self.left = left
        self.right = right

    def __str__(self):
        if self.right is not None:
            return f"{self.__class__.__name__}({self.left}, {self.right})"
        return f"{self.__class__.__name__}({self.left})"

    @abstractmethod
    def execute(self, row: dict):
        pass

    def resolve(self, operand, row):
        if isinstance(operand, Operator):
            return operand.execute(row)
        if isinstance(operand, str) and operand in row:  # else return the value of the column identifier in the row
            return row[operand]
        return operand


class NOT(Operator):
    def __init__(self, operand):
        self.operand = operand
        super().__init__(left=operand)

    def execute(self, row):
        val = self.resolve(self.operand, row)
        if val is None:
            return None
        return not val


class BOOL(Operator):
    def __init__(self, value):
        self.value = value
        super().__init__(left=value)

    def execute(self, row):
        if self.value is None:
            return None
        return str(self.value).upper() == "TRUE"


class AND(Operator):
    def execute(self, row):
        left = self.resolve(self.left, row)
        right = self.resolve(self.right, row)
        if left is False or right is False:
            return False
        if left is None or right is None:
            return None
        return True


class OR(Operator):
    def execute(self, row):
        left = self.resolve(self.left, row)
        right = self.resolve(self.right, row)
        if left is True or right is True:
            return True
        if left is None or right is None:
            return None
        return False


class GT(Operator):
    def execute(self, row):
        left = self.resolve(self.left, row)
        right = self.resolve(self.right, row)
        if left is None or right is None:
            return None
        return left > right


class LT(Operator):
    def execute(self, row):
        left = self.resolve(self.left, row)
        right = self.resolve(self.right, row)
        if left is None or right is None:
            return None
        return left < right


class GE(Operator):
    def execute(self, row):
        left = self.resolve(self.left, row)
        right = self.resolve(self.right, row)
        if left is None or right is None:
            return None
        return left >= right


class LE(Operator):
    def execute(self, row):
        left = self.resolve(self.left, row)
        right = self.resolve(self.right, row)
        if left is None or right is None:
            return None
        return left <= right


class EG(Operator):
    def execute(self, row):
        left = self.resolve(self.left, row)
        right = self.resolve(self.right, row)
        if left is None or right is None:
            return None
        return left == right


class NE(Operator):
    def execute(self, row):
        left = self.resolve(self.left, row)
        right = self.resolve(self.right, row)
        if left is None or right is None:
            return None
        return left != right


class IS_NULL(Operator):
    def execute(self, row):
        return self.resolve(self.left, row) is None


class IS_NOT_NULL(Operator):
    def execute(self, row):
        return self.resolve(self.left, row) is not None
