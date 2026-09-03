from rtt_assignments.paths import SHIFT_DIR, TRAIN_DIR
from rtt_assignments.application import Application
from rtt_assignments.shift.shift_manager import ShiftManager
from rtt_assignments.timetable.service_manager import ServiceManager

def main():
    shift_manager = ShiftManager.from_dir(SHIFT_DIR)
    service_manager = ServiceManager.from_dir(TRAIN_DIR, shift_manager.get_assigned_uids())

    app = Application(shift_manager, service_manager)
    app.run()


if __name__ == "__main__":
    main()
