from dataclasses import dataclass


@dataclass(frozen=True)
class QualifiedTable:
    name: str

    def __repr__(self) -> str:
        return f"QT[{self.name}]"


@dataclass(frozen=True)
class QualifiedColumn:
    table: QualifiedTable
    column: str

    @property
    def full_name(self) -> str:
        return f"{self.table.name}.{self.column}"

    def __repr__(self) -> str:
        return f"QC[{self.full_name}]"
