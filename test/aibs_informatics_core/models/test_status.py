from aibs_informatics_core.models.status import Status


def test__Status__is_complete__works():
    assert Status.ABORTED.is_complete() is True
    assert Status.SUBMITTED.is_complete() is False
    assert Status.AWAITING_TRIGGER.is_complete() is False
    assert Status.IN_PROGRESS.is_complete() is False
    assert Status.COMPLETED.is_complete() is True
    assert Status.FAILED.is_complete() is True
