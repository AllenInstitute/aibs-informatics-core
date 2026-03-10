from aibs_informatics_core.collections import StrEnum


class Status(StrEnum):
    """Enumeration of execution status values."""

    AWAITING_TRIGGER = "AWAITING_TRIGGER"
    SUBMITTED = "SUBMITTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"

    def is_complete(self) -> bool:
        """Check if the status represents a terminal state.

        Returns:
            True if the status is COMPLETED, FAILED, or ABORTED.
        """
        return self == Status.COMPLETED or self == Status.FAILED or self == Status.ABORTED
