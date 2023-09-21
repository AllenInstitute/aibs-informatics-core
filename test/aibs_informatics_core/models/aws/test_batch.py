from aibs_informatics_core.models.aws.batch import KeyValuePairType


def test__KeyValuePairType__from_dict():
    data = dict(Name="asdf", Value="asdf")
    KeyValuePairType.from_dict(data)
