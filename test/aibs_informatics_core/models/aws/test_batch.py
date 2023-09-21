from re import S

from marshmallow import ValidationError
from pytest import raises

from aibs_informatics_core.models.aws.batch import BatchJobDetail, KeyValuePairType


def test__KeyValuePairType__from_dict():
    data = dict(Name="asdf", Value="asdf")
    KeyValuePairType.from_dict(data)


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
