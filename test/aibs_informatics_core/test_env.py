from test.base import BaseTest

from aibs_informatics_core.env import EnvBase, EnvType


class EnvBaseTests(BaseTest):
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
