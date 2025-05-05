from abc import ABC


class Operator(ABC):
    def __init__(self, left, right=None):
        self.left = left
        self.right = right

    def __str__(self):
        return f"{self.__class__.__name__}({self.left}, {self.right})"

class NOT(Operator):
    def __init__(self, operand):
        self.operand = operand
        super().__init__(left=operand)


class AND(Operator):
    pass


class OR(Operator):
    pass


class GT(Operator):
    pass


class LT(Operator):
    pass


class GE(Operator):
    pass


class TE(Operator):
    pass


class EG(Operator):
    pass


class NE(Operator):
    pass


class IS_NULL(Operator):
    pass


class IS_NOT_NULL(Operator):
    pass
