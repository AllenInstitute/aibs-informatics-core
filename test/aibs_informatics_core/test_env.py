import os
from enum import Enum
from test.base import BaseTest

from aibs_informatics_core.env import (
    ENV_BASE_KEY,
    ENV_BASE_KEY_ALIAS,
    ENV_LABEL_KEY,
    ENV_LABEL_KEY_ALIAS,
    ENV_TYPE_KEY,
    ENV_TYPE_KEY_ALIAS,
    LABEL_KEY,
    LABEL_KEY_ALIAS,
    EnvBase,
    EnvBaseEnumMixins,
    EnvBaseMixins,
    EnvType,
    ResourceNameBaseEnum,
    get_env_base,
    get_env_label,
    get_env_type,
)


class EnvBaseTests(BaseTest):

    reset_environ = True

    def setUp(self) -> None:
        super().setUp()
        self.env_base = EnvBase("prod-marmot")

    def test__properties__returns_expected_values(self):
        self.assertEqual(self.env_base.env_type, EnvType.PROD)
        self.assertEqual(self.env_base.env_label, "marmot")

        self.assertEqual(EnvBase("prod").env_label, None)

    def test__get_construct_id__returns_prefixed_value(self):
        self.assertEqual(
            self.env_base.get_construct_id("construct", "x"), "prod-marmot-construct-x"
        )

    def test__get_stage_name__returns_prefixed_value(self):
        self.assertEqual(self.env_base.get_stage_name("construct", "x"), "prod-marmot-construct-x")

    def test__get_stack_name__returns_prefixed_value(self):
        self.assertEqual(self.env_base.get_stack_name("construct", "x"), "prod-marmot-construct-x")

    def test__get_pipeline_name__returns_prefixed_value(self):
        self.assertEqual(
            self.env_base.get_pipeline_name("construct", "x"), "prod-marmot-construct-x"
        )

    def test__prefixed__prefixes_with_explicit_delim(self):
        self.assertEqual(
            self.env_base.prefixed("construct", "x", delim="/"),
            "prod-marmot/construct/x",
        )

    def test__prefixed__does_not_prefix_if_already_prefixed(self):
        self.assertEqual(
            self.env_base.prefixed(f"{self.env_base}-construct", "x", delim="/"),
            "prod-marmot/prod-marmot-construct/x",
        )
        self.assertEqual(
            self.env_base.prefixed(f"{self.env_base}-construct", "x", delim="-"),
            "prod-marmot-construct-x",
        )
        self.assertEqual(
            self.env_base.prefixed(f"{self.env_base}construct", "x", delim="-"),
            "prod-marmot-prod-marmotconstruct-x",
        )
        self.assertEqual(
            self.env_base.prefixed(self.env_base, "construct", "x", delim="-"),
            "prod-marmot-construct-x",
        )

    def test__suffixed__does_not_suffix_if_already_suffixed(self):
        self.assertEqual(
            self.env_base.suffixed(f"construct", f"x-{self.env_base}", delim="/"),
            "construct/x-prod-marmot/prod-marmot",
        )
        self.assertEqual(
            self.env_base.suffixed(f"construct", f"x-{self.env_base}", delim="-"),
            "construct-x-prod-marmot",
        )
        self.assertEqual(
            self.env_base.suffixed(f"construct", f"x{self.env_base}", delim="-"),
            "construct-xprod-marmot-prod-marmot",
        )
        self.assertEqual(
            self.env_base.suffixed("construct", "x", self.env_base, delim="-"),
            "construct-x-prod-marmot",
        )

    def test__suffixed__prefixes_with_explicit_delim(self):
        self.assertEqual(
            self.env_base.suffixed("construct", "x", delim="/"),
            "construct/x/prod-marmot",
        )

    def test__get_table_name__returns_prefixed_value(self):
        self.assertEqual(self.env_base.get_table_name("table-x"), "prod-marmot-table-x")

    def test__get_function_name__returns_prefixed_value(self):
        self.assertEqual(self.env_base.get_function_name("table-x"), "prod-marmot-table-x")

    def test__get_job_name__returns_prefixed_value(self):
        self.assertEqual(self.env_base.get_job_name("table", "x"), "prod-marmot-table-x")

    def test__get_repository_name__returns_prefixed_value(self):
        self.assertEqual(self.env_base.get_repository_name("repo", "x"), "prod-marmot/repo-x")

    def test__get_resource_name__returns_prefixed_value(self):
        self.assertEqual(
            self.env_base.get_resource_name("resource", "x"), "prod-marmot-resource-x"
        )

    def test__get_state_machine_name__returns_prefixed_value(self):
        self.assertEqual(
            self.env_base.get_state_machine_name("state_machine-x"),
            "prod-marmot-state_machine-x",
        )

    def test__get_state_machine_log_group_name__returns_prefixed_value(self):
        self.assertEqual(
            self.env_base.get_state_machine_log_group_name("state_machine-x"),
            "/aws/vendedlogs/prod-marmot/states/state_machine-x",
        )

    def test__get_metric_namespace__returns_prefixed_value(self):
        self.assertEqual(
            self.env_base.get_metric_namespace("metric_namespace-x"),
            "AIBS/prod-marmot/metric_namespace-x",
        )

    def test__get_bucket_name__returns_prefixed_value(self):
        self.assertEqual(
            self.env_base.get_bucket_name("bucket", "account", "region"),
            "prod-marmot-bucket-region-account",
        )

    def test__get_ssm_param_name__returns_prefixed_value(self):
        self.assertEqual(
            self.env_base.get_ssm_param_name("param", "x"),
            "/prod-marmot/param-x",
        )

    def test__from_type_and_label__succeeds(self):
        expected_w_label = EnvBase("dev-marmot")
        expected_wo_label = EnvBase("dev")
        self.assertEqual(expected_w_label, EnvBase.from_type_and_label(EnvType.DEV, "marmot"))
        self.assertEqual(expected_wo_label, EnvBase.from_type_and_label(EnvType.DEV))

    def test__from_env__finds_env_base_variables(self):
        self.set_env_vars(
            *[
                (_, None)
                for _ in [
                    "ENV_BASE",
                    "env_base",
                    "ENV_TYPE",
                    "env_type",
                    "ENV_LABEL",
                    "env_label",
                    "LABEL",
                    "label",
                ]
            ]
        )
        self.set_env_vars(("ENV_BASE", "dev-marmot"), ("ENV_TYPE", "prod"))
        self.assertEqual(EnvBase("dev-marmot"), EnvBase.from_env())

        self.set_env_vars(("env_base", "prod-marmot"))
        self.assertEqual(EnvBase("prod-marmot"), EnvBase.from_env())

    def test__is_prefixed__correctly_determines_if_string_is_suffixed(self):
        # With Labels -- Positive Matches
        self.assertTrue(EnvBase.is_prefixed("dev-marmot"))
        self.assertTrue(EnvBase.is_prefixed("dev-marmot-asdfasdf"))
        self.assertTrue(EnvBase.is_prefixed("dev-marmot/asfasd/sdfsdf"))
        self.assertTrue(EnvBase.is_prefixed("dev-marmot_asdfasd_fgfgd"))
        self.assertTrue(EnvBase.is_prefixed("dev_dev-marmot"))
        self.assertTrue(EnvBase.is_prefixed("dev-marmot/blahblah/blah-dev-marmot"))
        # Without labels -- Positive Matches
        self.assertTrue(EnvBase.is_prefixed("dev"))
        self.assertTrue(EnvBase.is_prefixed("dev-blahblah/blah"))
        self.assertTrue(EnvBase.is_prefixed("dev/blahblah/blah"))
        self.assertTrue(EnvBase.is_prefixed("dev_blahblah/blah"))
        self.assertTrue(EnvBase.is_prefixed("devblahblah/blah"))
        self.assertTrue(EnvBase.is_prefixed("dev-blahblah/blah-dev-marmot"))
        self.assertTrue(EnvBase.is_prefixed("prod/blahblah/blah/dev"))

        # With Labels -- Negative Matches
        self.assertFalse(EnvBase.is_prefixed("villa-dev-marmot"))
        self.assertFalse(EnvBase.is_prefixed("_dev-marmot"))
        self.assertFalse(EnvBase.is_prefixed("ddev-marmot"))
        # Without labels -- Negative Matches
        self.assertFalse(EnvBase.is_prefixed("ddev"))
        self.assertFalse(EnvBase.is_prefixed("_dev"))
        self.assertFalse(EnvBase.is_prefixed(" dev"))

    def test__is_suffixed__correctly_determines_if_string_is_suffixed(self):
        # With Labels -- Positive Matches
        self.assertTrue(EnvBase.is_suffixed("dev-marmot"))
        self.assertTrue(EnvBase.is_suffixed("blahblah/blah-dev-marmot"))
        self.assertTrue(EnvBase.is_suffixed("blahblah/blah/dev-marmot"))
        self.assertTrue(EnvBase.is_suffixed("blahblah/blahdev-marmot"))
        self.assertTrue(EnvBase.is_suffixed("blahblah/dev_dev-marmot"))
        self.assertTrue(EnvBase.is_suffixed("dev-marmot/blahblah/blah-dev-marmot"))
        # Without labels -- Positive Matches
        self.assertTrue(EnvBase.is_suffixed("dev"))
        self.assertTrue(EnvBase.is_suffixed("blahblah/blah-dev"))
        self.assertTrue(EnvBase.is_suffixed("blahblah/blah/dev"))
        self.assertTrue(EnvBase.is_suffixed("blahblah/blahdev"))
        self.assertTrue(EnvBase.is_suffixed("prod/blahblah/blah/dev"))

        # With Labels -- Negative Matches
        self.assertFalse(EnvBase.is_suffixed("dev-marmotdsfsdf-"))
        self.assertFalse(EnvBase.is_suffixed("dev-marmot_/"))
        self.assertFalse(EnvBase.is_suffixed("dev-marmot/dsfsdf"))
        # Without labels -- Negative Matches
        self.assertFalse(EnvBase.is_suffixed("dev/dsfsdf"))
        self.assertFalse(EnvBase.is_suffixed("devdsfsdf"))
        self.assertFalse(EnvBase.is_suffixed("dev_dsfsdf"))

    def test__from_env__finds_env_type_and_labels_variables_and_selects_vars_by_priority(
        self,
    ):
        self.set_env_vars(
            *[
                (_, None)
                for _ in [
                    "ENV_BASE",
                    "env_base",
                    "ENV_TYPE",
                    "env_type",
                    "ENV_LABEL",
                    "env_label",
                    "LABEL",
                    "label",
                ]
            ]
        )

        self.set_env_vars(("ENV_TYPE", "prod"))
        self.assertEqual(EnvBase("prod"), EnvBase.from_env())

        self.set_env_vars(("env_type", "dev"))
        self.assertEqual(EnvBase("dev"), EnvBase.from_env())

        self.set_env_vars(("LABEL", "MARMOT"))
        self.assertEqual(EnvBase("dev-MARMOT"), EnvBase.from_env())

        self.set_env_vars(("label", "marmot"))
        self.assertEqual(EnvBase("dev-marmot"), EnvBase.from_env())

        self.set_env_vars(("ENV_LABEL", "MARMOTDEV"))
        self.assertEqual(EnvBase("dev-MARMOTDEV"), EnvBase.from_env())

        self.set_env_vars(("env_label", "marmotdev"))
        self.assertEqual(EnvBase("dev-marmotdev"), EnvBase.from_env())

        self.set_env_vars(("ENV_BASE", "prod-marmot"))
        self.assertEqual(EnvBase("prod-marmot"), EnvBase.from_env())

        self.set_env_vars(("env_base", "test"))
        self.assertEqual(EnvBase("test"), EnvBase.from_env())

    def test__from_env__raises_exception_if_no_env_vars(self):
        self.reset_all_env_vars()
        with self.assertRaises(Exception):
            EnvBase.from_env()

    def test__load_env_type__from_env__priority_works(self):
        self.reset_all_env_vars()
        self.set_env_vars(
            (ENV_TYPE_KEY_ALIAS, "prod"),
        )
        self.assertEqual(EnvType.PROD, EnvBase.load_env_type__from_env())
        self.set_env_vars(
            (ENV_TYPE_KEY_ALIAS, "test"),
            (ENV_TYPE_KEY, "prod"),
        )
        self.assertEqual(EnvType.PROD, EnvBase.load_env_type__from_env())

    def test__load_env_type__from_env__raises_exception_if_no_env_vars(self):
        self.reset_all_env_vars()
        with self.assertRaises(Exception):
            EnvBase.load_env_type__from_env()

    def test__load_env_label__from_env__priority_works(self):
        self.reset_all_env_vars()
        self.assertEqual(None, EnvBase.load_env_label__from_env())
        self.set_env_vars((LABEL_KEY_ALIAS, "label1"))
        self.assertEqual("label1", EnvBase.load_env_label__from_env())
        self.set_env_vars((LABEL_KEY, "label2"))
        self.assertEqual("label2", EnvBase.load_env_label__from_env())
        self.set_env_vars((ENV_LABEL_KEY_ALIAS, "label3"))
        self.assertEqual("label3", EnvBase.load_env_label__from_env())
        self.set_env_vars((ENV_LABEL_KEY, "label4"))
        self.assertEqual("label4", EnvBase.load_env_label__from_env())

    def test__to_env__sets_env_var(self):
        self.reset_all_env_vars()
        self.assertFalse(ENV_BASE_KEY in os.environ)
        env_base = EnvBase("test")
        env_base.to_env()
        self.assertEqual(os.environ[ENV_BASE_KEY], "test")
        env_base2 = EnvBase("test-label")
        env_base2.to_env()
        self.assertEqual(os.environ[ENV_BASE_KEY], "test-label")

    def test__get_env_base__works_as_expected(self):
        self.reset_all_env_vars()
        self.set_env_vars((ENV_BASE_KEY, "test"))
        self.assertEqual(get_env_base(), EnvBase("test"))
        self.assertEqual(get_env_base("test"), EnvBase("test"))
        self.assertEqual(get_env_base(EnvBase("test")), EnvBase("test"))

    def test__get_env_type__works_as_expected(self):
        self.reset_all_env_vars()

        # No default and no env vars
        with self.assertRaises(Exception):
            get_env_type()

        self.assertEqual(get_env_type(default_env_type=EnvType.TEST), EnvType.TEST)
        self.assertEqual(get_env_type(EnvType.TEST), EnvType.TEST)
        self.assertEqual(get_env_type("test"), EnvType.TEST)

    def test__get_env_label__works_as_expected(self):
        self.reset_all_env_vars()

        # No default and no env vars
        self.assertEqual(get_env_label(), None)

        # No default and env vars for label
        self.set_env_vars((ENV_LABEL_KEY, "foo"))
        self.assertEqual(get_env_label(), "foo")

        # No default and env vars for env base
        self.set_env_vars((ENV_BASE_KEY, "dev-bar"))
        self.assertEqual(get_env_label(), "bar")

        # Default supersedes env vars
        self.assertEqual(get_env_label("qaz"), "qaz")
        self.assertEqual(get_env_label(None), None)

    def test__EnvBaseMixins__works(self):
        self.reset_all_env_vars()
        self.set_env_vars((ENV_BASE_KEY, "dev-marmot"))

        class RandomClass(EnvBaseMixins):
            pass

        rc = RandomClass()
        self.assertEqual(rc.env_base, EnvBase("dev-marmot"))

        rc.env_base = EnvBase("prod-marmot")
        self.assertEqual(rc.env_base, EnvBase("prod-marmot"))

    def test__EnvBaseEnumMixins__works(self):
        self.reset_all_env_vars()
        self.set_env_vars((ENV_BASE_KEY, "dev-marmot"))

        class RandomEnum(EnvBaseEnumMixins, Enum):
            A = "a"

        self.assertEqual(RandomEnum.A.prefix_with(), "dev-marmot-a")
        self.assertEqual(RandomEnum.A.prefix_with("prod-marmot"), "prod-marmot-a")

    def test__ResourceNameBaseEnum__works(self):
        self.reset_all_env_vars()
        self.set_env_vars((ENV_BASE_KEY, "dev-marmot"))

        class RandomEnum(ResourceNameBaseEnum):
            A = "a"

        self.assertEqual(RandomEnum.A.prefix_with(), "dev-marmot-a")
        self.assertEqual(str(RandomEnum.A), "a")

    def reset_all_env_vars(self):
        self.set_env_vars(
            (ENV_BASE_KEY, None),
            (ENV_BASE_KEY_ALIAS, None),
            (ENV_TYPE_KEY, None),
            (ENV_TYPE_KEY_ALIAS, None),
            (ENV_LABEL_KEY, None),
            (ENV_LABEL_KEY_ALIAS, None),
            (LABEL_KEY, None),
            (LABEL_KEY_ALIAS, None),
        )
