from copy import copy
from datetime import datetime, timedelta
import os
from typing import Generator

from tqdm import tqdm
from rtt_assignments.timetable.timetable import Timetable
from glob import glob


def get_secs_difference(tt_time: datetime, reference_time: datetime | None) -> float:
    if reference_time:
        departure_secs_since_midnight = tt_time.hour * 60 * 60 + tt_time.minute * 60 + tt_time.second
        reference_secs_since_midnight = reference_time.hour * 60 * 60 + reference_time.minute * 60 + reference_time.second

        total_secs = departure_secs_since_midnight - reference_secs_since_midnight
        total_secs = total_secs % 86400
    else:
        total_secs = tt_time.hour * 60 * 60 + tt_time.minute * 60 + tt_time.second
    
    return total_secs


class ServiceSource:
    def __init__(self, timetable_dir: str) -> None:
        self._timetable_dir = timetable_dir

    def _get_filepath(self, timetable):
        return os.path.join(self._timetable_dir, f"{timetable.uid}_{timetable.td}.json")

    def load_all(self) -> list[Timetable]:
        return [Timetable.from_filepath(filepath) for filepath in tqdm(glob(os.path.join(self._timetable_dir, "*.json")), "Loading services")]
    
    def save(self, timetable: Timetable) -> None:
        with open(self._get_filepath(timetable), "w") as f:
            f.write(timetable.model_dump_json())

    def delete(self, timetable: Timetable) -> None:
        try:
            os.remove(self._get_filepath(timetable))
        except FileNotFoundError:
            pass


class ServiceManager:
    def __init__(self, source: ServiceSource, assigned_uids: set[str]) -> None:
        self._source = source
        self._timetables = source.load_all()
        self._assigned_uids = assigned_uids

    @classmethod
    def from_dir(cls, timetable_dir: str, assigned_uids: set[str]) -> "ServiceManager":
        return cls(ServiceSource(timetable_dir), assigned_uids)
    
    def is_assigned(self, service: Timetable) -> bool:
        return service.uid in self._assigned_uids
    
    def mark_assigned(self, service: Timetable) -> None:
        self._assigned_uids.add(service.uid)

    def mark_unassigned(self, service: Timetable) -> None:
        self._assigned_uids.remove(service.uid)

    def get_by_uid(self, uid: str) -> Timetable| None:
        for timetable in self._timetables:
            if timetable.uid == uid:
                return timetable
            
        return None
    

    def get_originating(self, station_code: str, operator: str | None, reference_time: datetime | None, time_limit: timedelta | None = None) -> list[Timetable]:
        checks = [
            lambda tt: tt.origin.timetable_code == station_code,
        ]

        if operator:
            checks.append(lambda tt: tt.operator == operator)
        
        if time_limit:
            checks.append(
                lambda tt: get_secs_difference(tt.origin.departure_time, reference_time) <= time_limit.total_seconds()
            )

        matches: list[Timetable] = []
        for timetable in self._timetables:
            if all((check(timetable) for check in checks)):
                matches.append(timetable)

        matches.sort(
            key=lambda tt: get_secs_difference(tt.origin.departure_time, reference_time)
        )

        return matches
    
    def get_terminating(self, station_code: str, operator: str | None, reference_time: datetime | None, time_limit: timedelta | None = None) -> list[Timetable]:
        checks = [
            lambda tt: tt.destination.timetable_code == station_code,
        ]

        if operator:
            checks.append(lambda tt: tt.operator == operator)
        
        if time_limit:
            checks.append(
                lambda tt: get_secs_difference(tt.destination.arrival_time, reference_time) <= time_limit.total_seconds()
            )

        matches: list[Timetable] = []
        for timetable in self._timetables:
            if all((check(timetable) for check in checks)):
                matches.append(timetable)

        matches.sort(
            key=lambda tt: get_secs_difference(tt.destination.arrival_time, reference_time)
        )

        return matches

    def get_originating_terminating(self, station_code: str, operator: str | None, reference_time: datetime | None, time_limit: timedelta | None = None) -> list[tuple[float, Timetable, bool]]:
        originating = self.get_originating(station_code, operator=operator, reference_time=reference_time, time_limit=time_limit)
        terminating = self.get_terminating(station_code, operator=operator, reference_time=reference_time, time_limit=time_limit)

        originating_indexed = [
            (get_secs_difference(tt.origin.departure_time, reference_time), tt, True) for tt in originating
        ]
        terminating_indexed = [
            (get_secs_difference(tt.destination.arrival_time, reference_time), tt, False) for tt in terminating
        ]

        indexed = originating_indexed + terminating_indexed
        indexed.sort(key=lambda tup: tup[0])

        return indexed

    def split_service(self, service: Timetable, idx: int) -> None:
        if self.is_assigned(service):
            raise ValueError("Can't split an assigned service")

        locations_a = [
            copy(l) for l in service.locations[:idx + 1]
        ]
        locations_b = [
            copy(l) for l in service.locations[idx:]
        ]

        locations_a[-1].departure_time = None
        locations_b[0].arrival_time = None

        service_a = Timetable(
            locations=locations_a,
            td=service.td,
            uid=service.uid + "a",
            operator=service.operator,
        )

        service_b = Timetable(
            locations=locations_b,
            td=service.td,
            uid=service.uid + "b",
            operator=service.operator,
        )

        self.delete_service(service)
        self.add_service(service_a)
        self.add_service(service_b)

    def delete_service(self, timetable: Timetable) -> None:
        self._timetables.remove(timetable)
        self._source.delete(timetable)
    
    def add_service(self, timetable: Timetable) -> None:
        self._timetables.append(timetable)
        self._source.save(timetable)