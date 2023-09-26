from test.base import BaseTest

from aibs_informatics_core.utils.os_operations import expandvars, find_all_paths


class OSOperationsTests(BaseTest):
    def test__find_all_paths__returns_folders_and_files(self):
        root = self.tmp_path()
        (root / "a").mkdir()
        (root / "b").mkdir()
        (root / "a" / "x").touch()
        (root / "a" / "y").touch()
        (root / "b" / "z").touch()

        expected = [
            root / "a",
            root / "b",
            root / "a" / "x",
            root / "a" / "y",
            root / "b" / "z",
        ]
        expected = [str(p) for p in expected]

        actual = find_all_paths(root, include_dirs=True, include_files=True)
        self.assertListEqual(actual, expected)

    def test__find_all_paths__returns_folders_or_files(self):
        root = self.tmp_path()
        (root / "a").mkdir()
        (root / "b").mkdir()
        (root / "a" / "x").touch()
        (root / "a" / "y").touch()
        (root / "b" / "z").touch()

        expected_dirs = [
            root / "a",
            root / "b",
        ]
        expected_files = [
            root / "a" / "x",
            root / "a" / "y",
            root / "b" / "z",
        ]
        actual_dirs = find_all_paths(root, include_dirs=True, include_files=False)
        actual_files = find_all_paths(root, include_dirs=False, include_files=True)
        self.assertListEqual(actual_dirs, [str(p) for p in expected_dirs])
        self.assertListEqual(actual_files, [str(p) for p in expected_files])

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
