from dataclasses import dataclass


from dataclasses import dataclass

@dataclass(frozen=True)
class QualifiedTable:
    name: str

    def __post_init__(self):
        object.__setattr__(self, 'name', self.name.lower())

    def __repr__(self) -> str:
        return f"QT[{self.name}]"


@dataclass(frozen=True)
class QualifiedColumn:
    table: QualifiedTable
    column: str

    def __post_init__(self):
        object.__setattr__(self, 'column', self.column.lower())

    @property
    def full_name(self) -> str:
        return f"{self.table.name}.{self.column}"

    def __repr__(self) -> str:
        return f"QC[{self.full_name}]"
