from __future__ import annotations

from pydantic import BaseModel

from .location import Location

class Timetable(BaseModel):
    locations: list[Location]
    td: str
    uid: str | None = None
    operator: str | None = None

    @classmethod
    def from_filepath(cls, filepath: str) -> "Timetable":
        with open(filepath) as f:
            return cls.model_validate_json(f.read())

    def __str__(self) -> str:
        if self.origin.platform:
            origin_plat = f" {self.origin.platform:3s}"
        else:
            origin_plat = "    "

        origin_str = f"{self.origin.format_time(self.origin.departure_time, include_fractional=False).replace(':', '')} {self.origin.timetable_code}{origin_plat}"

        if self.destination.platform:
            dest_plat = f" {self.destination.platform:3s}"
        else:
            dest_plat = "   "

        dest_str = f"{self.destination.format_time(self.destination.arrival_time, include_fractional=False).replace(':', '')} {self.destination.timetable_code}{dest_plat}"

        return f"{self.td} {self.uid} {origin_str} - {dest_str}"
    
    @property
    def origin(self) -> Location:
        return self.locations[0]
    
    @property
    def destination(self) -> Location:
        return self.locations[-1]