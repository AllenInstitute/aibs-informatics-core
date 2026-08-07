"""Tests for per-parameter include/exclude filters on demand execution resolvables.

See OCSDV-453. The hash regression tests here are the primary guard for the
riskiest part of that change: ``DemandExecution.get_execution_hash`` hashes the
*sanitized* params, and that hash drives ``job_definition_name`` (strict=False)
and ``job_name`` (strict=True) for every demand execution. If unfiltered
executions serialize even slightly differently, every job definition in the
system silently re-registers.
"""

from pytest import mark, param

from aibs_informatics_core.models.data_sync import DataSyncFilterConfig
from aibs_informatics_core.models.demand_execution.job_param import (
    DownloadableJobParam,
    UploadableJobParam,
)
from aibs_informatics_core.models.demand_execution.job_param_resolver import JobParamResolver
from aibs_informatics_core.models.demand_execution.model import DemandExecution
from aibs_informatics_core.models.demand_execution.parameters import DemandExecutionParameters
from aibs_informatics_core.models.demand_execution.resolvables import Resolvable, Uploadable

# ---------------------------------------------------------------------------
# Pinned payload + hashes
# ---------------------------------------------------------------------------

# A fixed, fully-specified payload. Nothing here may change -- the expected
# hashes below were captured by running get_execution_hash against this exact
# payload on the commit BEFORE filters were introduced. If you need a different
# payload for a new test, add one; do not edit this.
UNFILTERED_PAYLOAD: dict = {
    "execution_type": "demand",
    "execution_id": "ocsdv-453-hash-regression",
    "execution_image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/demand:1.0.0",
    "execution_parameters": {
        "command": ["run", "--input", "${ALIGNED}", "--output", "${RESULTS}"],
        "params": {
            "aligned": {"remote": "s3://bucket/run1/", "local": "aligned"},
            "results": {"remote": "s3://bucket/out/", "local": "results"},
            "threads": "4",
        },
        "inputs": ["aligned"],
        "outputs": ["results"],
    },
}

# Captured pre-change. Literal on purpose: a computed expectation would drift
# silently alongside a serialization regression, which is the exact failure
# these tests exist to catch.
EXPECTED_HASH_STRICT = "ca65e4158c37e10287213783c1ce477ab53f25d875bb3d36018311d2fdad4e76"
EXPECTED_HASH_NON_STRICT = "44a99a3987f95c176580af70cab1231c518f280a1edc3f5e4fdcba6cfb5f661c"

# The same execution built with actual Resolvable/Uploadable *objects* in params
# rather than plain dicts. This is the path that goes through to_str(), and so
# the path the conditional in sanitize_serialized_params actually guards.
EXPECTED_RESOLVABLE_HASH_STRICT = (
    "f60365cee2c2312e2ddde6faa74a4312574e7a46b39fd5737defbe2943212026"
)
EXPECTED_RESOLVABLE_HASH_NON_STRICT = (
    "44a99a3987f95c176580af70cab1231c518f280a1edc3f5e4fdcba6cfb5f661c"
)


def build_resolvable_execution(
    include=None, exclude=None, output_include=None, output_exclude=None
) -> DemandExecution:
    """Build the pinned execution with real Resolvable objects in params."""
    return DemandExecution(
        execution_type=UNFILTERED_PAYLOAD["execution_type"],
        execution_id=UNFILTERED_PAYLOAD["execution_id"],
        execution_image=UNFILTERED_PAYLOAD["execution_image"],
        execution_parameters=DemandExecutionParameters(
            command=list(UNFILTERED_PAYLOAD["execution_parameters"]["command"]),
            params={
                "aligned": Resolvable(
                    local="aligned",
                    remote="s3://bucket/run1/",
                    include=include,
                    exclude=exclude,
                ),
                "results": Uploadable(
                    local="results",
                    remote="s3://bucket/out/",
                    include=output_include,
                    exclude=output_exclude,
                ),
                "threads": "4",
            },
            inputs=["aligned"],
            outputs=["results"],
        ),
    )


# ---------------------------------------------------------------------------
# Hash regression -- the load-bearing tests
# ---------------------------------------------------------------------------


def test__get_execution_hash__unfiltered_dict_params_matches_pinned_hash():
    """An unfiltered execution must hash exactly as it did before filters existed."""
    execution = DemandExecution.from_dict(UNFILTERED_PAYLOAD)

    assert execution.get_execution_hash(True) == EXPECTED_HASH_STRICT
    assert execution.get_execution_hash(False) == EXPECTED_HASH_NON_STRICT


def test__get_execution_hash__unfiltered_resolvable_params_matches_pinned_hash():
    """Unfiltered Resolvable objects must still serialize via to_str()."""
    execution = build_resolvable_execution()

    assert execution.get_execution_hash(True) == EXPECTED_RESOLVABLE_HASH_STRICT
    assert execution.get_execution_hash(False) == EXPECTED_RESOLVABLE_HASH_NON_STRICT


def test__sanitize_serialized_params__unfiltered_resolvable_uses_to_str():
    """The string form is what unfiltered params serialized to before this change."""
    params = build_resolvable_execution().execution_parameters
    sanitized = params.sanitize_serialized_params(params.params)

    assert sanitized["aligned"] == "s3://bucket/run1/ @ aligned"
    assert sanitized["results"] == "results @ s3://bucket/out/"
    assert sanitized["threads"] == "4"


def test__sanitize_serialized_params__filtered_resolvable_uses_to_dict():
    """Filters only survive the dict form, so a filtered param must use it."""
    params = build_resolvable_execution(exclude=[r".*\.bam"]).execution_parameters
    sanitized = params.sanitize_serialized_params(params.params)

    assert isinstance(sanitized["aligned"], dict)
    assert sanitized["aligned"]["exclude"] == [r".*\.bam"]
    assert sanitized["aligned"]["local"] == "aligned"
    assert sanitized["aligned"]["remote"] == "s3://bucket/run1/"
    # The unfiltered sibling is untouched and still collapses to a string.
    assert sanitized["results"] == "results @ s3://bucket/out/"


@mark.parametrize(
    "kwargs",
    [
        param({"exclude": [r".*\.bam"]}, id="input_exclude"),
        param({"include": [r".*\.txt"]}, id="input_include"),
        param({"include": r".*\.txt", "exclude": r".*\.bam"}, id="input_both_scalar"),
        param({"output_exclude": [r".*\.tmp"]}, id="output_exclude"),
    ],
)
def test__get_execution_hash__filtered_differs_from_unfiltered(kwargs):
    """A filtered execution must hash differently from the same one unfiltered."""
    unfiltered = build_resolvable_execution()
    filtered = build_resolvable_execution(**kwargs)

    assert filtered.get_execution_hash(True) != unfiltered.get_execution_hash(True)
    # strict=False ignores params entirely, so job_definition_name is stable.
    assert filtered.get_execution_hash(False) == unfiltered.get_execution_hash(False)


@mark.parametrize(
    "empty",
    [param({"exclude": []}, id="empty_list"), param({"exclude": None}, id="none")],
)
def test__get_execution_hash__empty_filters_do_not_change_hash(empty):
    """An empty filter filters nothing, so it must not perturb the hash."""
    assert (
        build_resolvable_execution(**empty).get_execution_hash(True)
        == EXPECTED_RESOLVABLE_HASH_STRICT
    )


# ---------------------------------------------------------------------------
# Round trip
# ---------------------------------------------------------------------------


def test__DemandExecution__round_trip_without_filters():
    execution = DemandExecution.from_dict(UNFILTERED_PAYLOAD)
    round_tripped = DemandExecution.from_dict(execution.to_dict())

    assert round_tripped.to_dict() == execution.to_dict()
    assert round_tripped.get_execution_hash(True) == EXPECTED_HASH_STRICT
    # No filter keys leak into the serialized form when nothing is filtered.
    serialized_params = round_tripped.to_dict()["execution_parameters"]["params"]
    assert "include" not in serialized_params["aligned"]
    assert "exclude" not in serialized_params["aligned"]


def test__DemandExecution__round_trip_with_filters_preserves_them():
    payload = {
        **UNFILTERED_PAYLOAD,
        "execution_parameters": {
            **UNFILTERED_PAYLOAD["execution_parameters"],
            "params": {
                "aligned": {
                    "remote": "s3://bucket/run1/",
                    "local": "aligned",
                    "exclude": [r".*\.bam"],
                    "include": [r".*\.txt"],
                },
                "results": {
                    "remote": "s3://bucket/out/",
                    "local": "results",
                    "exclude": [r".*\.tmp"],
                },
                "threads": "4",
            },
        },
    }

    execution = DemandExecution.from_dict(payload)
    round_tripped = DemandExecution.from_dict(execution.to_dict())

    params = round_tripped.to_dict()["execution_parameters"]["params"]
    assert params["aligned"]["exclude"] == [r".*\.bam"]
    assert params["aligned"]["include"] == [r".*\.txt"]
    assert params["results"]["exclude"] == [r".*\.tmp"]
    assert round_tripped.to_dict() == execution.to_dict()

    # ...and they reach the job params on the far side.
    aligned = round_tripped.execution_parameters.get_input_job_param("aligned")
    assert aligned is not None
    assert aligned.exclude == [r".*\.bam"]
    assert aligned.include == [r".*\.txt"]


def test__DemandExecution__round_trip_with_resolvable_objects_preserves_filters():
    """Resolvable objects with filters survive to_dict() -> from_dict()."""
    execution = build_resolvable_execution(exclude=[r".*\.bam"], output_exclude=[r".*\.tmp"])
    round_tripped = DemandExecution.from_dict(execution.to_dict())

    params = round_tripped.to_dict()["execution_parameters"]["params"]
    assert params["aligned"]["exclude"] == [r".*\.bam"]
    assert params["results"]["exclude"] == [r".*\.tmp"]
    assert round_tripped.get_execution_hash(True) == execution.get_execution_hash(True)


# ---------------------------------------------------------------------------
# ResolvableBase behaviour
# ---------------------------------------------------------------------------


def test__ResolvableBase__action_serializer_and_validator_still_work():
    """The wrapping model_serializer/model_validator must keep round-tripping."""
    resolvable = Resolvable(local="aligned", remote="s3://bucket/run1/", exclude=[r".*\.bam"])
    data = resolvable.to_dict()

    assert data["action"] == "LOCALIZE"
    assert data["exclude"] == [r".*\.bam"]
    assert Resolvable.from_dict(data) == resolvable

    uploadable = Uploadable(local="results", remote="s3://bucket/out/", exclude=[r".*\.tmp"])
    uploadable_data = uploadable.to_dict()
    assert uploadable_data["action"] == "DELOCALIZE"
    assert Uploadable.from_dict(uploadable_data) == uploadable


def test__ResolvableBase__unfiltered_to_dict_omits_filter_keys():
    assert Resolvable(local="aligned", remote="s3://bucket/run1/").to_dict() == {
        "local": "aligned",
        "remote": "s3://bucket/run1/",
        "action": "LOCALIZE",
    }


@mark.parametrize(
    "kwargs, expected",
    [
        param({}, False, id="none"),
        param({"include": []}, False, id="empty_include"),
        param({"exclude": []}, False, id="empty_exclude"),
        param({"include": [r".*\.txt"]}, True, id="include"),
        param({"exclude": r".*\.bam"}, True, id="exclude_scalar"),
    ],
)
def test__ResolvableBase__has_filters(kwargs, expected):
    resolvable = Resolvable(local="aligned", remote="s3://bucket/run1/", **kwargs)
    assert resolvable.has_filters() is expected
    assert (resolvable.filter_config is not None) is expected


def test__ResolvableBase__filter_config_matches_data_sync_filter_config():
    resolvable = Resolvable(
        local="aligned", remote="s3://bucket/run1/", include=r".*\.txt", exclude=[r".*\.bam"]
    )
    assert resolvable.filter_config == DataSyncFilterConfig(
        include=r".*\.txt", exclude=[r".*\.bam"]
    )


def test__ResolvableBase__from_str_has_no_filters():
    """The string form carries no filters -- it cannot represent them."""
    resolvable = Resolvable.from_str("s3://bucket/run1/ @ aligned")
    assert resolvable.has_filters() is False
    assert resolvable.filter_config is None


# ---------------------------------------------------------------------------
# Job param carriage + reference resolution
# ---------------------------------------------------------------------------


def test__job_params__carry_filters_for_inputs_and_outputs():
    params = DemandExecutionParameters(
        params={
            "aligned": {
                "remote": "s3://bucket/run1/",
                "local": "aligned",
                "exclude": [r".*\.bam"],
            },
            "results": {
                "remote": "s3://bucket/out/",
                "local": "results",
                "include": [r".*\.csv"],
            },
        },
        inputs=["aligned"],
        outputs=["results"],
    )

    aligned = params.get_input_job_param("aligned")
    results = params.get_output_job_param("results")

    assert isinstance(aligned, DownloadableJobParam)
    assert aligned.exclude == [r".*\.bam"]
    assert aligned.filter_config == DataSyncFilterConfig(exclude=[r".*\.bam"])

    assert isinstance(results, UploadableJobParam)
    assert results.include == [r".*\.csv"]
    assert results.filter_config == DataSyncFilterConfig(include=[r".*\.csv"])


def test__job_params__unfiltered_have_no_filter_config():
    params = DemandExecutionParameters(
        params={"aligned": {"remote": "s3://bucket/run1/", "local": "aligned"}},
        inputs=["aligned"],
    )
    aligned = params.get_input_job_param("aligned")
    assert aligned is not None
    assert aligned.include is None
    assert aligned.exclude is None
    assert aligned.filter_config is None


# Regexes that contain the characters ${...} substitution cares about.
PATTERN_HOSTILE_TO_SUBSTITUTION = [
    param(r".*\.bam", id="simple"),
    param(r"^data/\d{2}/.*$", id="brace_quantifier_and_anchors"),
    param(r".*\{tmp\}.*", id="literal_braces"),
    param(r"sample_[A-Z]{1,3}\$.*", id="dollar_and_quantifier"),
    param(r"(?:a|b){2,}\$\{NOT_A_REF\}", id="escaped_ref_lookalike"),
]


@mark.parametrize("pattern", PATTERN_HOSTILE_TO_SUBSTITUTION)
def test__resolve_references__does_not_mangle_filter_patterns(pattern):
    """``${...}`` substitution runs over param values; it must not touch filters.

    Regex syntax legitimately contains ``$``, ``{`` and ``}``, so a filter
    pattern must come out of reference resolution byte-identical.
    """
    params = DemandExecutionParameters(
        params={
            "prefix": "run1",
            "aligned": {
                "remote": "s3://bucket/${PREFIX}/",
                "local": "aligned",
                "exclude": [pattern],
                "include": pattern,
            },
        },
        inputs=["aligned"],
    )

    aligned = params.get_input_job_param("aligned")
    assert aligned is not None
    # The reference in remote_value did resolve...
    assert aligned.remote_value == "s3://bucket/run1/"
    # ...while the filter patterns came through untouched.
    assert aligned.exclude == [pattern]
    assert aligned.include == pattern


@mark.parametrize("pattern", PATTERN_HOSTILE_TO_SUBSTITUTION)
def test__resolve_references__filter_patterns_are_not_scanned_for_references(pattern):
    """A filter pattern must not create a phantom reference dependency."""
    job_param = DownloadableJobParam(
        name="aligned",
        value="aligned",
        remote_value="s3://bucket/run1/",
        exclude=[pattern],
        include=pattern,
    )
    assert job_param.find_references() == []

    (resolved,) = JobParamResolver.resolve_references([job_param])
    assert isinstance(resolved, DownloadableJobParam)
    assert resolved.exclude == [pattern]
    assert resolved.include == pattern


@mark.parametrize("pattern", PATTERN_HOSTILE_TO_SUBSTITUTION)
def test__round_trip__preserves_hostile_patterns(pattern):
    """Hostile patterns survive the full serialize/deserialize cycle."""
    execution = build_resolvable_execution(exclude=[pattern])
    round_tripped = DemandExecution.from_dict(execution.to_dict())

    params = round_tripped.to_dict()["execution_parameters"]["params"]
    assert params["aligned"]["exclude"] == [pattern]
