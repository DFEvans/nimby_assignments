from pydantic import BaseModel

from rtt_assignments.timetable.timetable import Timetable


class Shift(BaseModel):
    services: list[Timetable]
    operator: str
    id: int
    train_type: str
    comment: str | None = None
    forms_from_ids: set[str]
    forms_to_ids: set[str]
    is_complete: bool = False

    @property
    def full_id(self) -> str:
        return f"{self.operator}{self.id}"
    
    @classmethod
    def from_file(cls, filepath: str) -> "Shift":
        with open(filepath) as f:
            return cls.model_validate_json(f.read())
        
    def to_file(self, filepath: str) -> None:
        with open(filepath, "w") as f:
            f.write(self.model_dump_json(indent=2))

    def add(self, service: Timetable) -> None:
        if service.operator != self.operator:
            raise ValueError(f"Service {service.td} with operator {service.operator} can't be added to schedule {self.full_id}")
        
        self.services.append(service)

    def delete(self, service: Timetable) -> bool:
        try:
            self.services.remove(service)
        except ValueError:
            return False

        return True

    @property
    def first_service(self) -> Timetable:
        return self.services[0]

    @property
    def last_service(self) -> Timetable:
        return self.services[-1]
    
    def add_forms_from(self, shift: "Shift") -> None:
        self.forms_from_ids.add(shift.full_id)

    def add_forms_to(self, shift: "Shift") -> None:
        self.forms_to_ids.add(shift.full_id)

    def delete_forms_from(self, shift: "Shift") -> None:
        try:
            self.forms_from_ids.remove(shift.full_id)
        except KeyError:
            pass

    def delete_forms_to(self, shift: "Shift") -> None:
        try:
            self.forms_to_ids.remove(shift.full_id)
        except KeyError:
            pass

    @property
    def split_train_type(self) -> list[str]:
        return self.train_type.split(",")