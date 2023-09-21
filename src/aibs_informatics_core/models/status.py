from aibs_informatics_core.collections import StrEnum


class Status(StrEnum):
    AWAITING_TRIGGER = "AWAITING_TRIGGER"
    SUBMITTED = "SUBMITTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"

    def is_complete(self) -> bool:
        return self == Status.COMPLETED or self == Status.FAILED or self == Status.ABORTED
