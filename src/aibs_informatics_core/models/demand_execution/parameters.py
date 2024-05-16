import logging
import os
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast

import marshmallow as mm

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.aws.s3 import S3URI
from aibs_informatics_core.models.base import (
    DictField,
    ListField,
    SchemaModel,
    StringField,
    custom_field,
)
from aibs_informatics_core.models.base.custom_fields import UnionField
from aibs_informatics_core.models.demand_execution.job_param import (
    DownloadableJobParam,
    JobParam,
    JobParamEnvName,
    JobParamRef,
    ResolvableJobParam,
    UploadableJobParam,
)
from aibs_informatics_core.models.demand_execution.job_param_resolver import JobParamResolver
from aibs_informatics_core.models.demand_execution.param_pair import (
    JobParamPair,
    JobParamSetPair,
    ParamPair,
    ParamSetPair,
)
from aibs_informatics_core.models.demand_execution.resolvables import (
    Resolvable,
    StringifiedUploadable,
    Uploadable,
    get_resolvable_from_value,
)
from aibs_informatics_core.utils.hashing import sha256_hexdigest
from aibs_informatics_core.utils.json import JSON

logger = logging.getLogger(__name__)


class refresh_params:
    def __init__(
        self, func: Optional[Callable] = None, force: bool = True, pre_validate: bool = False
    ):
        self.force = force
        self.pre_validate = pre_validate
        self.func = func

    def __get__(self, instance, owner):
        return partial(self.__call__, instance)

    def __call__(self, *args, **kwargs):
        # If function has not been set, the __call__ is passing in the function
        # Result: we set self.func and return self
        if not self.func:
            self.func = cast(Callable, args[0])
            return self
        # Otherwise, we call refresh once the already set function has finished
        obj = cast(DemandExecutionParameters, args[0])
        if self.pre_validate:
            obj._refresh(force=False)
        value = self.func(*args, **kwargs)
        obj._refresh(force=self.force)
        return value


@dataclass
class DemandExecutionParameters(SchemaModel):
    command: List[str] = custom_field(default_factory=list, mm_field=ListField(StringField))
    params: Dict[str, Any] = custom_field(default_factory=dict, mm_field=DictField(StringField))
    inputs: List[str] = custom_field(default_factory=list, mm_field=ListField(StringField))
    outputs: List[str] = custom_field(default_factory=list, mm_field=ListField(StringField))
    outputs_metadata: Dict[str, Dict[str, JSON]] = custom_field(
        default_factory=dict, mm_field=DictField(keys=StringField(), values=DictField(StringField))
    )
    output_s3_prefix: Optional[S3URI] = custom_field(default=None, mm_field=S3URI.as_mm_field())
    param_pair_overrides: Optional[List[Union[ParamSetPair, ParamPair]]] = custom_field(
        default=None,
        mm_field=ListField(
            UnionField(
                [(ParamSetPair, ParamSetPair.as_mm_field()), (ParamPair, ParamPair.as_mm_field())]
            )
        ),
    )
    verbosity: bool = custom_field(default=False)

    def __post_init__(self):
        self._refresh_hash = self._compute_refresh_hash()
        self._refresh(True)

    def validate_parameters(
        self, check_input_output_params: bool = True, check_param_pairs: bool = True
    ):
        """Validates Parameters

        Validation Steps:
            * Validate params do not have conflicting envnames
            * Validate inputs/outputs do not overlap
            * Validate that inputs/outputs are found in params
            * TODO: Validate that command only references valid parameters
        """
        # Validate params
        if check_input_output_params:
            self._validate_params()

        # Validate input_output_map
        if check_param_pairs:
            self._validate_param_pairs()

        # TODO: we need to check command

    def _validate_params(self):
        # Validate that input/output job env name parameters do not collide
        inp_envnames = [JobParam.as_envname(_) for _ in self.inputs]
        out_envnames = [JobParam.as_envname(_) for _ in self.outputs]
        envname_intersection = set(inp_envnames).intersection(out_envnames)
        if envname_intersection:
            raise ValidationError(
                f"Job inputs and outputs have overlapping env variable names: "
                f"{envname_intersection}"
            )

        # Validate that inputs/outputs are found in params
        param_map = self.job_param_map
        missing_param_envnames = set(inp_envnames).union(out_envnames).difference(param_map.keys())
        if len(missing_param_envnames) > 0:
            raise ValidationError(
                f"Batch Job inputs/outputs not found in param envnames: "
                f"{missing_param_envnames}"
            )

    def _validate_param_pairs(self):
        # Validate that all param pairs are inputs/outputs
        all_input_output_set = set().union(
            *[_.inputs.union(_.outputs) for _ in self.param_set_pairs]
        )
        diff = all_input_output_set.difference(set(self.inputs).union(set(self.outputs)))
        if len(diff) > 0:
            raise ValidationError(
                "input_output_mapping contained value(s) not found in params: " f"{diff}"
            )

        # Validate no duplicate output sets
        seen = set()
        duplicate_output_sets = []
        for s in self.param_set_pairs:
            if s.outputs in seen:
                duplicate_output_sets.append(s.outputs)
            if s.outputs:
                seen.add(s.outputs)
        if len(duplicate_output_sets) > 0:
            raise ValidationError(
                "Duplicate output set(s) in input_output_map: " f"{duplicate_output_sets}"
            )

    @refresh_params(force=False)
    def add_inputs(self, *param_keys, **param_key_values):
        """Add new input keys to the execution parameters.

        Inputs provided without values are assumed to be in params already
        """
        for i in [*param_keys, *param_key_values.keys()]:
            if i not in self.inputs:
                self.inputs.append(i)
        self.update_params(**param_key_values)

    @refresh_params(force=False)
    def add_outputs(self, *param_keys, **param_key_values):
        """Add new output keys to the execution parameters.

        Outputs provided without values are assumed to be in params already
        """
        for i in [*param_keys, *param_key_values.keys()]:
            if i not in self.outputs:
                self.outputs.append(i)
        self.update_params(**param_key_values)

    @refresh_params(force=False)
    def update_params(self, *param_pairs: Tuple[str, Any], **param_key_values: Any):
        params = dict(param_pairs)
        params.update(param_key_values)
        self.params.update(params)

    def get_param(self, envname: str) -> Optional[Any]:
        """Checks if param contains environment name or placeholder

        Args:
            envname (str): An environment name or placeholder.

        Returns:
            bool: True if param contains envname or placeholder references
        """
        envname = self._sanitize_envname(envname)
        job_param = self._job_param_map.get(envname)
        if job_param:
            return self.params.get(job_param.name)
        return None

    def has_param(self, envname: str) -> bool:
        envname = self._sanitize_envname(envname)
        # Cannot use self.get_param because it will return None if param is not found
        job_param = self._job_param_map.get(envname)
        if job_param:
            return job_param.name in self.params
        return False

    def get_job_param(self, envname: str) -> Optional[JobParam]:
        if JobParamRef.is_valid(envname):
            envname = JobParamRef(envname).envname
        return self.job_param_map.get(JobParam.as_envname(envname))

    def get_input_job_param(self, envname: str) -> Optional[DownloadableJobParam]:
        job_param = self.get_job_param(envname)
        if job_param and isinstance(job_param, DownloadableJobParam):
            return job_param
        return None

    def get_output_job_param(self, envname: str) -> Optional[UploadableJobParam]:
        job_param = self.get_job_param(envname)
        if job_param and isinstance(job_param, UploadableJobParam):
            return job_param
        return None

    @property
    def param_pairs(self) -> List[ParamPair]:
        return [p for ps in self.param_set_pairs for p in ps.to_pairs()]

    @property
    def param_set_pairs(self) -> List[ParamSetPair]:
        param_set_pairs: List[ParamSetPair] = []
        param_pairs: List[ParamPair] = []
        if self.param_pair_overrides:
            seen_outputs: Set[Union[str, None]] = set()
            for pair in self.param_pair_overrides:
                if isinstance(pair, ParamSetPair):
                    seen_outputs.update(pair.outputs)
                    param_set_pairs.append(pair)
                else:
                    seen_outputs.add(pair.output)
                    param_pairs.append(pair)
            if unseen_outputs := set(self.outputs).difference(seen_outputs):
                # NOTE: Here we are allowing for param_pair_overrides to not contain
                #       all inputs/outputs.
                #       We collect remaining
                logger.warning(
                    f"param_pair_overrides did not contain all inputs/outputs: "
                    f"outputs={unseen_outputs}. Adding param set pair to include them."
                )
                param_set_pairs.append(
                    ParamSetPair(frozenset(self.inputs), frozenset(unseen_outputs))
                )
        else:
            param_pairs.extend(ParamPair.from_sets(inputs=self.inputs, outputs=self.outputs))
        param_set_pairs.extend(ParamSetPair.from_pairs(*param_pairs))
        return param_set_pairs

    @property
    def job_param_pairs(self) -> List[JobParamPair]:
        set_pairs: List[JobParamPair] = []
        for pair in self.param_pairs:
            inp_job_param = self.get_input_job_param(pair.input) if pair.input else None
            out_job_param = self.get_output_job_param(pair.output) if pair.output else None
            set_pairs.append(JobParamPair(inp_job_param, out_job_param))
        return set_pairs

    @property
    def job_param_set_pairs(self) -> List[JobParamSetPair]:
        r_job_param_map = {
            k: v for k, v in self.job_param_map.items() if isinstance(v, ResolvableJobParam)
        }
        return [
            JobParamSetPair(
                inputs=frozenset({r_job_param_map[JobParam.as_envname(_)] for _ in pair.inputs}),
                outputs=frozenset({r_job_param_map[JobParam.as_envname(_)] for _ in pair.outputs}),
            )
            for pair in self.param_set_pairs
        ]

    @property
    def resolved_command(self) -> List[str]:
        environment: Dict[str, str] = dict(os.environ)
        environment.update({k: v.value for k, v in self.job_param_map.items()})
        return [
            JobParamRef.replace_references(command_part, environment)
            for command_part in self.command
        ]

    @property
    def job_params(self) -> List[JobParam]:
        return self._job_params

    @property
    def job_param_map(self) -> Dict[str, JobParam]:
        return self._job_param_map

    @property
    def job_param_inputs(self) -> List[JobParam]:
        self._refresh(force=False)
        return [self.job_param_map[JobParam.as_envname(_)] for _ in self.inputs]

    @property
    def job_param_outputs(self) -> List[JobParam]:
        self._refresh(force=False)
        return [self.job_param_map[JobParam.as_envname(_)] for _ in self.outputs]

    @property
    def downloadable_job_param_inputs(self) -> List[DownloadableJobParam]:
        return [_ for _ in self.job_param_inputs if isinstance(_, DownloadableJobParam)]

    @property
    def uploadable_job_param_outputs(self) -> List[UploadableJobParam]:
        return [_ for _ in self.job_param_outputs if isinstance(_, UploadableJobParam)]

    def _sanitize_envname(self, envname: str) -> JobParamEnvName:
        """Converts envname to JobParamEnvName

        This also converts JobParamRef to JobParamEnvName

        Args:
            envname (str): any string reference to parameter

        Returns:
            JobParamEnvName:
        """
        if JobParamRef.is_valid(envname):
            envname = JobParamRef(envname).envname
        return JobParam.as_envname(envname)

    def _param_to_job_params(self) -> List[JobParam]:
        """Convert param dictionary into List of JobParam objects

        Returns:
            List[JobParam]:
        """
        job_params: List[JobParam] = []
        input_envnames = set([JobParam.as_envname(i) for i in self.inputs])
        output_envnames = set([JobParam.as_envname(o) for o in self.outputs])
        for k, v in self.params.items():
            job_param_envname = JobParam.as_envname(k)
            if job_param_envname in input_envnames:
                job_params.append(self._param_to_job_params__build_input(k, v))
            elif job_param_envname in output_envnames:
                job_params.append(self._param_to_job_params__build_output(k, v))
            else:
                job_params.append(JobParam(k, str(v)))
        return job_params

    def _param_to_job_params__build_input(self, k: str, v: Any) -> JobParam:
        resolvable = get_resolvable_from_value(value=v, resolvable_classes=[Resolvable])
        return DownloadableJobParam(k, resolvable.local, resolvable.remote)

    def _param_to_job_params__build_output(self, k: str, v: Any) -> JobParam:
        if StringifiedUploadable.is_valid(v):
            str_uploadable = StringifiedUploadable(v)
            # This logic holds becauses remote is None if destination not found
            if not str_uploadable.remote and not self.output_s3_prefix:
                raise ValueError(
                    f"{str_uploadable} has no destination specified and no output prefix provided"
                )
            remote_value = str_uploadable.remote or S3URI(f"{self.output_s3_prefix}/{v}")
            return UploadableJobParam(k, str_uploadable.local, remote_value)
        else:
            # Only create default remote if value is string and not a stringified uploadable reference
            default_remote = (
                S3URI(f"{self.output_s3_prefix}/{v}")
                if isinstance(v, str) and self.output_s3_prefix
                else None
            )
            uploadable = Uploadable.from_any(value=v, default_remote=default_remote)
            return UploadableJobParam(k, uploadable.local, uploadable.remote)

    def _set_job_params(self, job_params: List[JobParam]):
        self._job_params = JobParamResolver.resolve_references(job_params)
        self._job_param_map = {_.envname: _ for _ in self._job_params}
        self.validate_parameters()

    # ------------------------------------------------
    #                   Refresh methods
    # ------------------------------------------------

    def _refresh(self, force: bool = False):
        if force or self._should_refresh():
            self._set_job_params(self._param_to_job_params())
            self.validate_parameters()

    def _should_refresh(self) -> bool:
        old_refresh_hash = self._refresh_hash
        new_refresh_hash = self._compute_refresh_hash()
        if old_refresh_hash != new_refresh_hash:
            self._refresh_hash = new_refresh_hash
            return True
        return False

    def _compute_refresh_hash(self) -> str:
        return sha256_hexdigest(self.to_dict(partial=True, validate=False))

    # ------------------------------------------------
    #                   Schema hooks
    # ------------------------------------------------

    @classmethod
    @mm.pre_load
    def _sanitize_param_pairs(cls, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        in_use_key = "param_pair_overrides"
        deprecated_keys = [
            "param_pairs",
            "param_set_pairs",
            "param_set_pair_overrides",
            "input_output_pairs",
            "input_output_pair_overrides",
        ]

        param_pairs = []

        if in_use_key in data:
            param_pairs.extend(data.pop(in_use_key))

        for k in deprecated_keys:
            if k in data:
                param_pairs.extend(data.pop(k))

        if param_pairs:
            data[in_use_key] = param_pairs

        return data

    @classmethod
    @mm.post_dump
    def _sanitize_params(cls, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        params = data["params"]
        for k, v in params.items():
            if isinstance(v, Resolvable):
                params[k] = v.to_str()
        return data
