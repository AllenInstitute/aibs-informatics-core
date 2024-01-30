import collections
from copy import deepcopy
from typing import Dict, List, Match, Set

from aibs_informatics_core.exceptions import ValidationError
from aibs_informatics_core.models.demand_execution.job_param import JobParam, JobParamRef
from aibs_informatics_core.utils.decorators import cache


class JobParamResolver:
    @classmethod
    @cache
    def find_collisions(cls, *job_params: JobParam) -> List[List[JobParam]]:
        # Validate params do not have conflicting envnames
        envname_job_params: Dict[str, List[JobParam]] = collections.defaultdict(list)
        for job_param in job_params:
            envname_job_params[job_param.envname].append(job_param)
        return [_ for _ in envname_job_params.values() if len(_) > 1]

    @classmethod
    def check_collisions(cls, job_params: List[JobParam]):
        colliding_job_params = cls.find_collisions(*job_params)
        if len(colliding_job_params):
            raise ValidationError(
                "Job Params have at least two parameters with conflicting envnames. "
                f"Complete List of offending job params: {colliding_job_params}"
            )

    @classmethod
    def resolve_references(cls, job_params: List[JobParam]) -> List[JobParam]:
        """Resolves param references found in values of param map

        Valid Cases:

            Example 1: Nested references
                Unresolved: [("x", "${Y}/${Z}_foo"),       ("y", "${Z}_${Z}_bar"), ("z", "qaz")]
                Resolved:   [("x", "qaz_qaz_bar/qaz_foo"), ("y", "qaz_qaz_bar"),   ("z", "qaz")]

            Example 2: Reference by unnormalized env names
                Unresolved: [("reference_a", "foo_${refERENCE_b}"), ("REFerence-B", "bar")]
                Resolved:   [("reference_a", "foo_bar"),            ("REFerence-B", "bar")]

        Invalid Cases:

            Example 1: Cyclical References
                [({"x", "${Y}"), ("y", "${X}")]

            Example 2: Self Reference
                [("X": "${X}")]

            Example 3: Reference to missing param
                [("X", "${Y}")]

        Args:
            job_params (List[JobParam]): List of job params with unresolved references in values

        Returns:
            List[JobParam]: list of job params with resolved references in values
        """

        cls.check_collisions(job_params)

        # job_param.env_name -> job_param (with resolved values)
        resolved_job_param_map: Dict[str, JobParam] = dict()

        # job_param.env_name -> job_param (with unresolved values)
        unresolved_job_param_map: Dict[str, JobParam] = dict()

        # job_param.env_name -> Set of other job_param.env_name references found in job_param.value
        job_param_dependency_map: Dict[str, Set[str]] = dict()

        for job_param in deepcopy(job_params):
            job_param_dependency_map[job_param.envname] = {
                _.envname for _ in job_param.find_references()
            }
            if job_param_dependency_map[job_param.envname]:
                unresolved_job_param_map[job_param.envname] = job_param
            else:
                resolved_job_param_map[job_param.envname] = job_param

        def replace_reference(match: Match) -> str:
            ref = JobParamRef(match.group(0))
            return resolved_job_param_map[JobParam.as_envname(ref.envname)].value

        iter_resolved_count = len(resolved_job_param_map)
        while unresolved_job_param_map:
            for job_param_envname in list(unresolved_job_param_map.keys()):
                job_param_dependencies = job_param_dependency_map[job_param_envname]
                if all([_ in resolved_job_param_map for _ in job_param_dependencies]):
                    job_param = unresolved_job_param_map[job_param_envname]
                    job_param.replace_references(reference_replacement=replace_reference)
                    resolved_job_param_map[job_param_envname] = job_param
                    unresolved_job_param_map.pop(job_param_envname)
            if iter_resolved_count == len(resolved_job_param_map):
                raise ValidationError(
                    "Could not resolve any more references: "
                    f"Resolved: {resolved_job_param_map}, "
                    f"Unresolved: {unresolved_job_param_map}, "
                    f"Reference Dependencies: {job_param_dependency_map}"
                )
        return [resolved_job_param_map[_.envname] for _ in job_params]
