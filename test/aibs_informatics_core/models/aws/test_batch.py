from marshmallow import ValidationError
from pytest import raises

from aibs_informatics_core.models.aws.batch import (
    AttemptContainerDetail,
    AttemptDetail,
    BatchJobDetail,
    ContainerDetail,
    KeyValuePairType,
)


def test__KeyValuePairType__from_dict():
    data = dict(Name="asdf", Value="asdf")
    KeyValuePairType.from_dict(data)


def test__AttemptDetail__properties_work():
    detail = AttemptDetail(
        Container=AttemptContainerDetail(
            ContainerInstanceArn="asdf1",
            TaskArn="asdf2",
        ),
        StartedAt=1,
        StoppedAt=2,
    )
    assert detail.duration == 1
    assert detail.container_instance_arn == "asdf1"
    assert detail.container_task_arn == "asdf2"

    detail2 = AttemptDetail(StartedAt=1)
    assert detail2.duration is None
    assert detail2.container_instance_arn is None
    assert detail2.container_task_arn is None


def test__BatchJobDetail__properties_work():
    detail = BatchJobDetail(
        JobName="JobName",
        JobId="JobId",
        JobQueue="JobQueue",
        Status="Status",
        StartedAt=1,
        StoppedAt=2,
        JobDefinition="JobDefinition",
        Container=ContainerDetail(
            Image="Image:Tag",
            ContainerInstanceArn="ContainerInstanceArn",
            TaskArn="TaskArn",
            Environment=[KeyValuePairType(Name="Name", Value="Value")],
        ),
        Attempts=[
            AttemptDetail(
                Container=AttemptContainerDetail(
                    ContainerInstanceArn="ContainerInstanceArn",
                    TaskArn="TaskArn",
                ),
                StartedAt=1,
                StoppedAt=2,
            )
        ],
    )
    assert detail.duration == 1
    assert detail.container_instance_arn == "ContainerInstanceArn"
    assert detail.container_name_and_tag == ("Image", "Tag")
    assert detail.container_tag == "Tag"
    assert detail.container_instance_arns == ["ContainerInstanceArn"]
    assert detail.container_task_arn == "TaskArn"
    assert detail.container_environment == {"Name": "Value"}

    detail2 = BatchJobDetail(
        JobName="JobName",
        JobId="JobId",
        JobQueue="JobQueue",
        Status="Status",
        JobDefinition="JobDefinition",
        StartedAt=1,
    )

    assert detail2.duration is None
    assert detail2.container_instance_arn is None
    assert detail2.container_name_and_tag == ("NotAvailable", None)
    assert detail2.container_tag is None
    assert detail2.container_instance_arns == []
    assert detail2.container_task_arn is None
    assert detail2.container_environment == {}


def test__BatchJobDetail__from_dict():
    data = dict(
        JobDefinition="asdf",
        JobName="asdf",
        TaskArn="asdf",
        JobId="asdf",
        JobQueue="asdf",
        Status="asdf",
        StartedAt=2,
        StoppedAt=42,
        Parameters=dict(asdf="asdf"),
        Container=dict(
            StartedAt=42,
            TaskArn="asdf",
            ContainerInstanceArn="asdf",
            Command=["asdf"],
            Environment=[dict(Name="asdf", Value="asdf")],
            Image="asdf",
            Memory=1,
            MountPoints=[dict(ContainerPath="asdf", ReadOnly=True, SourceVolume="asdf")],
            Privileged=True,
            ReadonlyRootFilesystem=True,
            Ulimits=[dict(hardLimit=1, name="asdf", softLimit=1)],
            User="asdf",
            Vcpus=1,
            Volumes=[dict(host=dict(sourcePath="asdf"), name="asdf")],
        ),
    )

    BatchJobDetail.from_dict(data)


def test__from_dict__invalid_container_type():
    with raises(ValidationError):
        BatchJobDetail.from_dict(
            dict(
                jobDefinition="asdf",
                jobName="asdf",
                jobQueue="asdf",
                parameters=dict(asdf="asdf"),
                container="asdf",
            )
        )
