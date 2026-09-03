from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel

class Location(BaseModel):
    name: str
    arrival_time: datetime | None
    departure_time: datetime | None
    platform: str | None
    is_pass: bool
    path: str | None
    line: str | None
    path_allowance: str | None
    eng_allowance: str | None
    perf_allowance: str | None

    def format_time(self, t: datetime, is_pass: bool = False, include_fractional: bool = True) -> str:
        if not t:
            return ""
        
        separator = "/" if is_pass else ":"

        s = f"{t.hour:02d}{separator}{t.minute:02d}"

        if include_fractional:
            if t.second == 15:
                s += "¼"
            elif t.second == 30:
                s += "½"
            elif t.second == 45:
                s += "¾"
        
        return s
    
    @property
    def timetable_code(self) -> str:
        try:
            code = self.name.split("[")[1].split("]")[0]
        except IndexError:
            code = self.name
        
        return code

    def __str__(self) -> str:
        s = f"{self.name:30s} {self.format_time(self.arrival_time):6s} {self.format_time(self.departure_time, is_pass=self.is_pass):6s}"

        allowance_string = ""
        if self.eng_allowance:
            allowance_string += f" [{self.eng_allowance}]"
        if self.path_allowance:
            allowance_string += f" ({self.path_allowance})"
        if self.perf_allowance:
            allowance_string += f" <{self.perf_allowance}>"

        return s + allowance_string
