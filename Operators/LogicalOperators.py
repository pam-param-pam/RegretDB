from abc import ABC, abstractmethod


class Operator(ABC):
    def __init__(self, left, right=None):
        self.left = left
        self.right = right

    def __str__(self):
        if self.right:
            return f"{self.__class__.__name__}({self.left}, {self.right})"
        return f"{self.__class__.__name__}({self.left})"

    @abstractmethod
    def execute(self, row: dict) -> bool:
        pass

    def resolve(self, operand, row):
        if isinstance(operand, Operator):
            return operand.execute(row)
        if isinstance(operand, str) and operand in row:
            return row[operand]
        return operand


class NOT(Operator):
    def __init__(self, operand):
        self.operand = operand
        super().__init__(left=operand)

    def execute(self, row):
        return not self.resolve(self.operand, row)


class AND(Operator):
    def execute(self, row):
        return self.resolve(self.left, row) and self.resolve(self.right, row)


class OR(Operator):
    def execute(self, row):
        return self.resolve(self.left, row) or self.resolve(self.right, row)


class GT(Operator):
    def execute(self, row):
        return self.resolve(self.left, row) > self.resolve(self.right, row)


class LT(Operator):
    def execute(self, row):
        return self.resolve(self.left, row) < self.resolve(self.right, row)


class GE(Operator):
    def execute(self, row):
        return self.resolve(self.left, row) >= self.resolve(self.right, row)


class LE(Operator):
    def execute(self, row):
        return self.resolve(self.left, row) <= self.resolve(self.right, row)


class EG(Operator):
    def execute(self, row):
        return self.resolve(self.left, row) == self.resolve(self.right, row)


class NE(Operator):
    def execute(self, row):
        return self.resolve(self.left, row) != self.resolve(self.right, row)


class IS_NULL(Operator):
    def execute(self, row):
        return self.resolve(self.left, row) is None


class IS_NOT_NULL(Operator):
    def execute(self, row):
        return self.resolve(self.left, row) is not None


where = OR(
    AND(GT("orders.amount", 100), EG("ala", "name")),
    AND(GT("orders.amount", 200), NOT(EG("ala", "ala")))
)

row = {
    "orders.amount": 150, "ala": "name"
}

print(where.execute(row))
