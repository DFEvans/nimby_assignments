from datetime import datetime
from glob import glob
import os
import shutil
from rtt_assignments.shift.shift import Shift
from rtt_assignments.timetable.timetable import Timetable


class ShiftManager:
    def __init__(self, shifts: list[Shift]) -> None:
        self._shifts = shifts

        self._operator_shift_indices = self._get_shift_indices()

    @classmethod
    def from_dir(cls, shift_dir: str) -> "ShiftManager":
        if os.path.exists(shift_dir):
            shifts = [
                Shift.from_file(filepath) for filepath in glob(os.path.join(shift_dir, "*.json"))
            ]
        else:
            shifts = []

        return cls(shifts)
    
    def to_file(self, shift_dir: str) -> None:
        backup_dir_name = os.path.basename(shift_dir) + f"_{datetime.now().strftime(r'%Y%m%dT%H%M%S')}"
        backup_dir = os.path.join(os.path.dirname(shift_dir), backup_dir_name)

        try:
            shutil.move(shift_dir, backup_dir)
        except FileNotFoundError:
            pass
        os.makedirs(shift_dir, exist_ok=True)
        for shift in self._shifts:
            shift.to_file(os.path.join(shift_dir, shift.full_id + ".json"))

    @property
    def shifts(self) -> list[Shift]:
        return self._shifts.copy()

    def _get_shift_indices(self) -> dict[str, int]:
        operator_shift_indices = {}

        for shift in self._shifts:
            existing_index = operator_shift_indices.setdefault(shift.operator, 0)
            if shift.id > existing_index:
                operator_shift_indices[shift.operator] = shift.id
        
        return operator_shift_indices
    
    def next_shift_index(self, operator: str) -> int:
        next_index = self._operator_shift_indices.setdefault(operator, 0) + 1
        self._operator_shift_indices[operator] = next_index

        return next_index
    
    def create_shift(self, service: Timetable, train_type: str) -> Shift:
        shift_index = self.next_shift_index(service.operator)
        shift = Shift(
            services=[service],
            operator=service.operator,
            id=shift_index,
            train_type=train_type,
            forms_from_ids=set(),
            forms_to_ids=set(),
        )

        self._shifts.append(shift)

        return shift
    
    def delete_shift(self, shift: Shift) -> None:
        for shift_id in list(shift.forms_from_ids):
            if other_shift := self.get_shift(shift_id):
                shift.delete_forms_from(other_shift)
                other_shift.delete_forms_to(shift)
        for shift_id in list(shift.forms_to_ids):
            if other_shift := self.get_shift(shift_id):
                shift.delete_forms_to(other_shift)
                other_shift.delete_forms_from(shift)

        self._shifts.remove(shift)
    
    def get_shift(self, full_id: str) -> Shift | None:
        for shift in self._shifts:
            if shift.full_id == full_id:
                return shift
            
        return None
    
    def get_assigned_uids(self) -> set[str]:
        uids = set()
        for shift in self._shifts:
            for service in shift.services:
                uids.add(service.uid)
        
        return uids

    def get_operator_shifts(self, operator: str) -> list[Shift]:
        return [
            shift for shift in self._shifts if shift.operator == operator
        ]