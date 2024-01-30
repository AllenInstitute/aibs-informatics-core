import re
from dataclasses import dataclass
from typing import Callable, ClassVar, Dict, List, Match, Pattern, Type, TypeVar, Union

from aibs_informatics_core.collections import ValidatedStr
from aibs_informatics_core.models.demand_execution.resolvables import Resolvable, Uploadable


class JobParamEnvName(ValidatedStr):
    regex_pattern: ClassVar[Pattern] = re.compile(r"([_a-zA-Z][_a-zA-Z0-9]*)")

    def __new__(cls, value):
        normalized_value = value.replace("-", "_").replace(".", "_").upper()
        obj = super().__new__(cls, normalized_value)
        obj._raw = value
        return obj


class JobParamRef(ValidatedStr):
    regex_pattern: ClassVar[Pattern] = re.compile(r"\$\{([_a-zA-Z][_a-zA-Z0-9]*)\}")

    @property
    def raw_envname(self) -> str:
        return self.get_match_groups()[0]

    @property
    def envname(self) -> str:
        return JobParam.as_envname(self.raw_envname)

    @classmethod
    def from_name(cls, name) -> "JobParamRef":
        return JobParamRef(f"${{{JobParamEnvName(name)}}}")

    @classmethod
    def replace_references(
        cls, value: str, reference_replacement: Union[Dict[str, str], Callable[[Match], str]]
    ) -> str:
        if isinstance(reference_replacement, dict):
            reference_value_map = reference_replacement

            def replace_reference(match: Match) -> str:
                ref = JobParamRef(match.group(0))
                k = JobParam.as_envname(ref.envname)
                if k not in reference_value_map:
                    raise ValueError(f"Could not fill {ref}, no value in reference value map.")
                return reference_value_map[k]

            return JobParamRef.suball(string=value, repl=replace_reference)
        else:
            return JobParamRef.suball(string=value, repl=reference_replacement)


T = TypeVar("T")


@dataclass
class JobParam:
    name: str
    value: str

    def __hash__(self) -> int:
        return hash(self.name + str(self.value))

    @property
    def envname(self) -> JobParamEnvName:
        """Formats the name of the input to be an environment variable.
        For example: reference-path --> REFERENCE_PATH
        Replaces dashes with underscores and converts to upper case.
        """
        return self.as_envname(self.name)

    @property
    def envname_reference(self) -> JobParamRef:
        """Formats the name of the input to be used as an environment
        variable in a string. For example:
            reference-path --> ${REFERENCE_PATH}
        """
        return self.as_envname_reference(self.envname)

    def update_environment(self, environment: Dict[str, str], overwrite: bool = False):
        if (
            not overwrite
            and self.envname in environment
            and environment[self.envname] != self.value
        ):
            raise ValueError(
                f"Environment already contains {self.envname} with a different value."
            )
        environment[self.envname] = self.value

    @classmethod
    def as_envname(cls, name: str) -> JobParamEnvName:
        return JobParamEnvName(name)

    @classmethod
    def as_envname_reference(cls, name) -> JobParamRef:
        return JobParamRef.from_name(cls.as_envname(name))

    def find_references(self) -> List[JobParamRef]:
        if isinstance(self.value, str):
            return JobParamRef.findall(self.value)
        return []

    def replace_references(
        self, reference_replacement: Union[Dict[str, str], Callable[[Match], str]]
    ):
        self.value = JobParamRef.replace_references(
            value=self.value, reference_replacement=reference_replacement
        )


RP = TypeVar("RP", bound="ResolvableJobParam")


@dataclass
class ResolvableJobParam(JobParam):
    remote_value: str

    def __hash__(self) -> int:
        return hash(self.name + self.value + self.remote_value)

    def find_references(self) -> List[JobParamRef]:
        return super().find_references() + JobParamRef.findall(self.remote_value)

    def replace_references(
        self, reference_replacement: Union[Dict[str, str], Callable[[Match], str]]
    ):
        super().replace_references(reference_replacement=reference_replacement)
        self.remote_value = JobParamRef.replace_references(
            value=self.remote_value, reference_replacement=reference_replacement
        )

    @classmethod
    def from_resolvable(cls: Type[RP], name: str, resolvable: Resolvable) -> RP:
        return cls(name=name, value=resolvable.local, remote_value=resolvable.remote)


@dataclass
class DownloadableJobParam(ResolvableJobParam):
    def __hash__(self) -> int:
        return hash(self.name + self.value + self.remote_value)


@dataclass
class UploadableJobParam(ResolvableJobParam):
    def __hash__(self) -> int:
        return hash(self.name + self.value + self.remote_value)
