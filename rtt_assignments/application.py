from datetime import datetime, timedelta
from functools import partial
from typing import Optional, Type
from rtt_assignments.paths import DATE, SHIFT_DIR
from rtt_assignments.shift.shift import Shift
from rtt_assignments.shift.shift_manager import ShiftManager
from rtt_assignments.timetable.service_manager import ServiceManager
from abc import abstractmethod
from colorama import Fore, Back, Style


from rtt_assignments.timetable.timetable import Timetable


class Application:
    def __init__(self, shift_manager: ShiftManager, service_manager: ServiceManager) -> None:
        self.shift_manager = shift_manager
        self.service_manager = service_manager
        self._active_shift: Shift | None = None

        self._suggested_service: Timetable | None = None

        self._exit = False

        self._commands: list["Command"] = []

    @property
    def active_shift(self) -> Shift | None:
        return self._active_shift
    
    @property
    def suggested_service(self) -> Timetable | None:
        return self._suggested_service

    def command_exit(self) -> None:
        self._exit = True

    def _do_exit(self) -> None:
        self.shift_manager.to_file(SHIFT_DIR)

    def command_set_active_shift(self, shift: Shift | None):
        self._active_shift = shift
        self.shift_manager.to_file(SHIFT_DIR)

    def command_set_suggested_service(self, service: Timetable | None = None) -> None:
        self._suggested_service = service

    def enqueue_command(self, command: "Command") -> None:
        self._commands.append(command)

    def _next_command(self) -> Optional["Command"]:
        try:
            return self._commands.pop(0)
        except IndexError:
            return None

    def get_main_menu_option(self) -> None:
        if self._active_shift:
            print()
            print(f"Active shift: {self._active_shift.full_id} {self._active_shift.train_type}")
            print(f"Last service: {str(self._active_shift.last_service)}")

        user_input = input("> ").split(" ")
        print()

        command = user_input[0].lower()
        args = user_input[1:]

        command_type: Type[Command] = NoCommand

        if command == "a":
            command_type = AddToShiftCommand
        elif command == "b":
            command_type = ShowShiftBalanceCommand
        elif command == "c":
            command_type = CreateShiftCommand
        elif command == "d":
            command_type = DeleteFromShiftCommand
        elif command == "e":
            command_type = PrintAllShiftsCommand
        elif command == "f":
            command_type = FinaliseShiftCommand
        elif command == "i":
            command_type = SetTrainTypeCommand
        elif command == "j":
            command_type = MarkTimetabledCommand
        elif command == "l":
            command_type = LoadShiftCommand
        elif command == "n":
            command_type = NextForShiftCommand
        elif command == "p":
            command_type = PrintShiftCommand
        elif command == "q":
            command_type = ExitCommand
        elif command == "s":
            command_type = partial(StationListCommand, remaining_only=False)
        elif command == "r":
            command_type = partial(StationListCommand, remaining_only=True)
        elif command == "t":
            command_type = ShowTimetableCommand
        elif command == "w":
            command_type = FindShiftCommand
        elif command == "x":
            command_type = SplitServiceCommand
        elif command == "y":
            command_type = AcceptSuggestedServiceCommand
        elif command == "z":
            command_type = AddCommentCommand
        elif command == "ff":
            command_type = FormsFromCommand
        elif command == "ft":
            command_type = FormsToCommand
        elif command == "dff":
            command_type = DeleteFormsFromCommand
        elif command == "dft":
            command_type = DeleteFormsToCommand
        elif command == "cf":
            command_type = CreateShiftFormsFromCommand
        elif command == "?":
            command_type = HelpCommand
        else:
            print("Unrecognised command")
        
        self.enqueue_command(command_type(self, args))

    def run(self) -> None:
        HelpCommand(self, []).execute()

        while not self._exit:
            self.get_main_menu_option()
            while command := self._next_command():
                command.execute()
            
        self._do_exit()


class Command:
    def __init__(self, app: Application, args: list[str]) -> None:
        self.app = app
        self.args = args

    @abstractmethod
    def execute(self) -> None:
        pass

    def check_arg_count(self, minimum_count: int) -> bool:
        if len(self.args) < minimum_count:
            print("Invalid input")
            return False
        
        return True


class NoCommand(Command):
    def execute(self) -> None:
        return


class ExitCommand(Command):
    def execute(self) -> None:
        self.app.command_exit()


class LoadShiftCommand(Command):
    def execute(self) -> None:
        if not self.check_arg_count(1):
            return
        
        shift_id = self.args[0]
        shift = self.app.shift_manager.get_shift(shift_id)
        if not shift:
            print("Shift not found")
            return

        self.app.command_set_active_shift(shift)
        self.app.enqueue_command(PrintShiftCommand(self.app, []))

class FormsFromCommand(Command):
    def execute(self) -> None:
        if not self.check_arg_count(1):
            return
        
        if not (active_shift := self.app.active_shift):
            print("No active shift")
            return
        
        shift_id = self.args[0]
        shift = self.app.shift_manager.get_shift(shift_id)
        if not shift:
            print("Shift not found")
            return
        
        active_shift.add_forms_from(shift)
        shift.add_forms_to(active_shift)


class FormsToCommand(Command):
    def execute(self) -> None:
        if not self.check_arg_count(1):
            return
        
        if not (active_shift := self.app.active_shift):
            print("No active shift")
            return
        
        shift_id = self.args[0]
        shift = self.app.shift_manager.get_shift(shift_id)
        if not shift:
            print("Shift not found")
            return
        
        active_shift.add_forms_to(shift)
        shift.add_forms_from(active_shift)



class DeleteFormsFromCommand(Command):
    def execute(self) -> None:
        if not self.check_arg_count(1):
            return
        
        if not (active_shift := self.app.active_shift):
            print("No active shift")
            return
        
        shift_id = self.args[0]
        shift = self.app.shift_manager.get_shift(shift_id)
        if not shift:
            print("Shift not found")
            return
        
        active_shift.delete_forms_from(shift)
        shift.delete_forms_to(active_shift)


class DeleteFormsToCommand(Command):
    def execute(self) -> None:
        if not self.check_arg_count(1):
            return
        
        if not (active_shift := self.app.active_shift):
            print("No active shift")
            return
        
        shift_id = self.args[0]
        shift = self.app.shift_manager.get_shift(shift_id)
        if not shift:
            print("Shift not found")
            return
        
        active_shift.delete_forms_to(shift)
        shift.delete_forms_from(active_shift)



class CreateShiftCommand(Command):
    def execute(self) -> None:
        if not self.check_arg_count(2):
            return
        
        uid = self.args[0]
        train_type = self.args[1]
        
        service = self.app.service_manager.get_by_uid(uid)

        if not service:
            print("UID not found")
            return
        
        if self.app.service_manager.is_assigned(service):
            print("Service already assigned")
            return
        
        self.app.service_manager.mark_assigned(service)
        shift = self.app.shift_manager.create_shift(service, train_type)
        self.app.command_set_active_shift(shift)
        self.app.enqueue_command(NextForShiftCommand(self.app, []))


class CreateShiftFormsFromCommand(Command):
    def execute(self) -> None:
        if not self.check_arg_count(2):
            return
        
        uid = self.args[0]
        train_type = self.args[1]

        if len(self.args) == 3:
            forms_from_shift = self.args[2]
        elif self.app.active_shift:
            forms_from_shift = self.app.active_shift.full_id
        else:
            print("No forms from shift specified and none is active")
            return

        self.app.enqueue_command(CreateShiftCommand(self.app, [uid, train_type]))
        self.app.enqueue_command(FormsFromCommand(self.app, [forms_from_shift]))


class StationListCommand(Command):
    def __init__(self, app: Application, args: list[str], remaining_only: bool) -> None:
        super().__init__(app, args)
        self.remaining_only = remaining_only

    def execute(self) -> None:
        if not self.check_arg_count(1):
            return
        
        station_code = self.args[0]

        if len(self.args) > 1:
            operator = self.args[1]
        elif self.app.active_shift:
            operator = self.app.active_shift.operator
        else:
            operator = None

        if len(self.args) > 2:
            reference_time = datetime.strptime(f"{DATE}T{self.args[2]}", r"%Y-%m-%dT%H%M")
        else:
            reference_time = None

        timetables = self.app.service_manager.get_originating_terminating(station_code=station_code, operator=operator, reference_time=reference_time)

        for _, tt, is_originating in timetables:

            color = Style.RESET_ALL

            if self.app.service_manager.is_assigned(tt):
                if self.remaining_only:
                    continue
                suffix = " ***"
                color = Fore.RED

                for shift in self.app.shift_manager.shifts:
                    if tt in shift.services:
                        suffix += f"  {shift.full_id:5s} {shift.train_type}"
            else:
                suffix = ""

            prefix = "" if is_originating else " "
            
            print(color + f"{prefix + str(tt):60s}{suffix}" + Style.RESET_ALL)


class NextForShiftCommand(Command):
    def execute(self) -> None:
        if not (shift := self.app.active_shift):
            print("No active shift")
            return
        
        destination = shift.last_service.destination

        platform = destination.platform
        
        timetables = self.app.service_manager.get_originating_terminating(station_code=destination.timetable_code, operator=shift.operator, reference_time=destination.arrival_time, time_limit=timedelta(hours=2))

        print(f"{shift.last_service.td} arr {shift.last_service.destination.format_time(shift.last_service.destination.arrival_time).replace(':', '')} {shift.last_service.destination.timetable_code} {shift.last_service.destination.platform or ''}:")

        is_first_suggestion = True

        counter = 0
        for _, tt, is_originating in timetables:
            counter += 1
            if self.app.service_manager.is_assigned(tt):
                continue

            color = Style.RESET_ALL
            
            prefix = "" if is_originating else " "

            suffix = ""
            if is_originating and platform == tt.origin.platform:
                suffix = " <"
                color = Fore.GREEN
                if is_first_suggestion:
                    self.app.command_set_suggested_service(tt)
                    is_first_suggestion = False
            elif not is_originating and platform == tt.destination.platform:
                color = Fore.RED
                suffix = " !"

            print(color + prefix + str(tt) + suffix + Style.RESET_ALL)

            if (counter > 30 and not is_first_suggestion) or (counter > 40):
                break


class AddToShiftCommand(Command):
    def execute(self) -> None:
        if not self.check_arg_count(1):
            return
        
        uid = self.args[0]

        if not (shift := self.app.active_shift):
            print("No active shift")
            return

        service = self.app.service_manager.get_by_uid(uid)

        if not service:
            print(f"UID {uid} not found")
            return
        
        if self.app.service_manager.is_assigned(service):
            print("Service already assigned")
            return
        
        self.app.service_manager.mark_assigned(service)
        shift.add(service)

        self.app.enqueue_command(NextForShiftCommand(self.app, []))


class PrintShiftCommand(Command):
    def execute(self) -> None:
        if len(self.args) == 1:
            shift_id = self.args[0]
            if not (shift := self.app.shift_manager.get_shift(shift_id)):
                print("Shift not found")
                return
        else:
            if not (shift := self.app.active_shift):
                print("No active shift")
                return
             
        print(f"Services assigned to {shift.full_id} ({shift.train_type})")

        if shift.forms_from_ids:
            print(f"Forms from {', '.join(shift.forms_from_ids)}")

        for service in shift.services:
            print(str(service))
        
        if shift.forms_to_ids:
            print(f"Forms to {', '.join(shift.forms_to_ids)}")

        if shift.comment:
            print("Comment:", shift.comment)


class FinaliseShiftCommand(Command):
    def execute(self) -> None:
        print("Shift finalised")
        self.app.command_set_active_shift(None)


class DeleteFromShiftCommand(Command):
    def execute(self) -> None:
        if not self.check_arg_count(1):
            return
        
        uid = self.args[0]

        if not (shift := self.app.active_shift):
            print("No active shift")
            return

        service = self.app.service_manager.get_by_uid(uid)

        if not service:
            print("UID not found")
            return
        
        if shift.delete(service):
            self.app.service_manager.mark_unassigned(service)

        if not shift.services:
            self.app.shift_manager.delete_shift(shift)
            self.app.command_set_active_shift(None)

        self.app.enqueue_command(PrintShiftCommand(self.app, []))


class PrintAllShiftsCommand(Command):
    def execute(self) -> None:
        if len(self.args) > 0:
            operator = self.args[0]
            shifts = self.app.shift_manager.get_operator_shifts(operator)
        else:
            shifts = self.app.shift_manager.shifts

        if len(self.args) > 1:
            train_type = self.args[1]
            shifts = [
                shift for shift in shifts if train_type in shift.train_type
            ]
        
        shifts.sort(key=lambda x: (x.operator, x.id))

        for shift in shifts:
            comment = ""
            if shift.forms_from_ids:
                comment += f"(From {' '.join(sorted(shift.forms_from_ids))}) "
            if shift.forms_to_ids:
                comment += f"(To {' '.join(sorted(shift.forms_to_ids))}) "
            if shift.comment:
                comment += shift.comment

            complete_marker = "x" if shift.is_complete else " "
            
            print(f"{shift.full_id:5s} {shift.train_type:20s} {complete_marker} {shift.first_service.origin.timetable_code}-{shift.last_service.destination.timetable_code}   {comment}")


class SplitServiceCommand(Command):
    def execute(self) -> None:
        if not self.check_arg_count(2):
            return
        
        uid = self.args[0]

        where = self.args[1]

        service = self.app.service_manager.get_by_uid(uid)

        if not service:
            print("UID not found")
            return
        
        if self.app.service_manager.is_assigned(service):
            print("Service is assigned, unassign first")
            return
        
        try:
            i = int(where) - 1
        except ValueError:
            for i, location in enumerate(service.locations):
                if location.timetable_code == where:
                    break
            else:
                print("Station not in route")
                return
            
        if i == 0 or i == (len(service.locations) - 1):
            print("Can't split at first or last station")
            return
        
        self.app.service_manager.split_service(service, i)
        
class ShowTimetableCommand(Command):
    def execute(self) -> None:
        if not self.check_arg_count(1):
            return
        
        uid = self.args[0]

        service = self.app.service_manager.get_by_uid(uid)

        if not service:
            print("UID not found")
            return
        
        print(str(service))
        for location in service.locations:
            print(str(location))


class FindShiftCommand(Command):
    def execute(self) -> None:
        if not self.check_arg_count(1):
            return
        
        uid = self.args[0]

        service = self.app.service_manager.get_by_uid(uid)

        if not service:
            print("UID not found")
            return
        
        if not self.app.service_manager.is_assigned(service):
            print("Service not assigned")
            return
        
        for shift in self.app.shift_manager.shifts:
            if service in shift.services:
                print(shift.full_id)


class AcceptSuggestedServiceCommand(Command):
    def execute(self) -> None:
        if not self.app.active_shift:
            print("No active shift")
            return
        
        if not (service := self.app.suggested_service):
            print("No suggested service")
            return
        
        self.app.enqueue_command(AddToShiftCommand(self.app, [service.uid]))
        self.app.command_set_suggested_service(None)

class AddCommentCommand(Command):
    def execute(self) -> None:
        if not (shift := self.app.active_shift):
            print("No active shift")
            return

        if len(self.args) == 0:
            comment = None
        else:
            comment = " ".join(self.args)

        if shift.comment:
            shift.comment += "; " + comment
        else:
            shift.comment = comment


class SetTrainTypeCommand(Command):
    def execute(self) -> None:
        if not self.check_arg_count(1):
            return
        
        if not (shift := self.app.active_shift):
            print("No active shift")
            return
        
        shift.train_type = self.args[0]



class MarkTimetabledCommand(Command):
    def execute(self) -> None:
       
        if not (shift := self.app.active_shift):
            print("No active shift")
            return
        
        shift.is_complete = True

        self.app.command_set_active_shift(None)

        print("Marked as timetabled")


class ShowShiftBalanceCommand(Command):
    def execute(self):
        if not self.check_arg_count(1):
            return
        
        operator = self.args[0]

        shifts = self.app.shift_manager.get_operator_shifts(operator)

        train_types = set()
        locations = set()
        origin_train_type_counts: dict[str, dict[str, int]] = {}
        dest_train_type_counts: dict[str, dict[str, int]] = {}

        for shift in shifts:
            origin_code = shift.first_service.origin.timetable_code
            dest_code = shift.last_service.destination.timetable_code

            for train_type in shift.split_train_type:
                train_types.add(train_type)
                locations.add(origin_code)
                locations.add(dest_code)

                origin_count = origin_train_type_counts.setdefault(
                    origin_code, {}
                ).setdefault(
                    train_type, 0
                ) + 1

                origin_train_type_counts[origin_code][train_type] = origin_count

                dest_count = dest_train_type_counts.setdefault(
                    dest_code, {}
                ).setdefault(
                    train_type, 0
                ) + 1

                dest_train_type_counts[dest_code][train_type] = dest_count

        sorted_train_types = sorted(train_types)
        sorted_locations = sorted(locations)

        location_balance: dict[str, dict[str, int]] = {}

        # Origin
        print("Originating")
        header_line = " " * 15
        for location in sorted_locations:
            header_line += f"{location[:4]:4s} "
        print(header_line)

        for train_type in sorted_train_types:
            train_line = f"{train_type:14s} "

            for location in sorted_locations:
                loc_count = origin_train_type_counts.get(location, {}).get(train_type, 0)
                if loc_count:
                    train_line += f"{loc_count:2d}   "
                else:
                    train_line += " " * 5

                balance_count = location_balance.setdefault(location, {}).setdefault(train_type, 0) - loc_count
                location_balance[location][train_type] = balance_count
            
            print(train_line)

        # Destination
        print("\nTerminating")
        header_line = " " * 15
        for location in sorted_locations:
            header_line += f"{location[:4]:4s} "
        print(header_line)

        for train_type in sorted_train_types:
            train_line = f"{train_type:14s} "

            for location in sorted_locations:
                loc_count = dest_train_type_counts.get(location, {}).get(train_type, 0)
                if loc_count:
                    train_line += f"{loc_count:2d}   "
                else:
                    train_line += " " * 5

                balance_count = location_balance.setdefault(location, {}).setdefault(train_type, 0) + loc_count
                location_balance[location][train_type] = balance_count
            
            print(train_line)
        
        # Balance
        print("\nBalance")
        header_line = " " * 15
        for location in sorted_locations:
            header_line += f"{location[:4]:4s} "
        print(header_line)

        for train_type in sorted_train_types:
            train_line = f"{train_type:14s} "

            for location in sorted_locations:
                loc_count = location_balance.get(location, {}).get(train_type, 0)
                if loc_count:
                    train_line += f"{loc_count:2d}   "
                else:
                    train_line += " " * 5

            print(train_line)


class HelpCommand(Command):
    def execute(self) -> None:
        print()
        print("a    Add to shift <train_uid>")
        print("b    Show shift balance for <operator>")
        print("c    Create shift from train <train_uid> <train_type>")
        print("d    Delete <train_id> from shift")
        print("e    Print all shifts for <operator> <train_type>")
        print("f    Finalise shift")
        print("i    Set shift train type to <train_type>")
        print("j    Mark shift as completed in NIMBY")
        print("l    Load shift <shift_id>")
        print("n    Show possible next steps for current shift")
        print("p    Print current shift")
        print("q    Exit")
        print("s    List trains at station <station_code> <operator>")
        print("r    List remaining trains at station <station_code> <operator>")
        print("t    Show timetable for <train_id>")
        print("w    Print shift <train_id> is assigned to")
        print("x    Split service <train_id> at <station_code>")
        print("y    Accept suggested service")
        print("z    Add comment to service")
        print("cf  Create shift from train <train_uid> <train_type> forming from <shift_id>")
        print("ff   Set service as forming from <shift_id>")
        print("ft   Set service as forming to <shift_id>")
        print("dff  Unset service as forming from <shift_id>")
        print("dft  Unset service as forming to <shift_id>")
        print("?    Print this message")
