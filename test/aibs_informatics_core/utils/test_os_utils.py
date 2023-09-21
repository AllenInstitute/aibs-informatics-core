from test.base import BaseTest

from aibs_informatics_core.utils.os_operations import expandvars


class OSUtilsTests(BaseTest):
    def test__expandvars__expands_env_vars_without_brackets(self):
        self.set_env_vars(("V1", "signal"), ("V2", "the"))
        self.assertEqual(expandvars("$V1 between $V2 noise"), "signal between the noise")

    def test__expandvars__expands_env_vars_with_brackets(self):
        self.set_env_vars(("V1", "between"), ("V2", "the"))
        self.assertEqual(expandvars("signal${V1}${V2}noise"), "signalbetweenthenoise")

    def test__expandvars__fills_missing_vars_with_env(self):
        self.set_env_vars(("V1", "signal"), ("V2", None))
        self.assertEqual(expandvars("$V1 between $V2 noise"), "signal between $V2 noise")

    def test__expandvars__fills_missing_vars_with_override_default(self):
        self.set_env_vars(("V1", "signal"), ("V2", None))
        self.assertEqual(
            expandvars("${V1}between $V2 noise", default="the"),
            "signalbetween the noise",
        )

    def test__expandvars__does_not_expand_values_if_double_escaped(self):
        self.set_env_vars(("V1", "the"))
        self.assertEqual(
            expandvars("signalbetween\\${V1}noise", skip_escaped=True),
            "signalbetween\\${V1}noise",
        )
        self.assertEqual(
            expandvars("signalbetween \\$V1 noise", skip_escaped=True),
            "signalbetween \\$V1 noise",
        )
