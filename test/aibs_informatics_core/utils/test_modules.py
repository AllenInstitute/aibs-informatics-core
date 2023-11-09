import os
import unittest
from test.base import does_not_raise

from pytest import mark, param, raises

import aibs_informatics_core.utils.modules
from aibs_informatics_core.utils.modules import (
    get_all_subclasses,
    get_qualified_name,
    load_all_modules_from_pkg,
    load_type_from_qualified_name,
)


class ModuleUtilsTests(unittest.TestCase):
    def test_get_all_subclasses(self):
        class A(object):
            pass

        class AA(A):
            pass

        class AB(A):
            pass

        class AC(A):
            pass

        class AAA(AA):
            pass

        class ABA(AB):
            pass

        class ACA(AC):
            pass

        class ACB(AC):
            pass

        self.assertListEqual(get_all_subclasses(A), [AA, AB, AC, AAA, ABA, ACA, ACB])


class ModuleLoadUtils(unittest.TestCase):
    mod_prefix = "test.aibs_informatics_core.utils.module_utils"

    def test_load_all_modules_from_pkg_recursively_succeeds(self):
        import test.aibs_informatics_core.utils.module_utils as test_mod

        results = load_all_modules_from_pkg(test_mod, recursive=True, include_packages=True)
        self.assertEqual(len(results), 7)
        self.assertTrue(all([modpath.startswith(self.mod_prefix) for modpath in results]))

    def test_load_all_modules_from_pkg_recursively_ignore_packages_succeeds(self):
        import test.aibs_informatics_core.utils.module_utils

        results = load_all_modules_from_pkg(
            test.aibs_informatics_core.utils.module_utils, recursive=True, include_packages=False
        )
        self.assertEqual(len(results), 4)
        self.assertTrue(all([modpath.startswith(self.mod_prefix) for modpath in results]))

    def test_load_all_modules_from_pkg_ignore_packages_succeeds(self):
        import test.aibs_informatics_core.utils.module_utils

        results = load_all_modules_from_pkg(
            test.aibs_informatics_core.utils.module_utils, recursive=False, include_packages=False
        )
        self.assertEqual(len(results), 1)
        self.assertTrue(all([modpath.startswith(self.mod_prefix) for modpath in results]))


class DummyClass:
    pass


class DummyChildClass(DummyClass):
    pass


@mark.parametrize(
    "value,expected,raise_expectation",
    [
        param(None, "NoneType", does_not_raise(), id="NoneType"),
        param("mystr", "str", does_not_raise(), id="builtin object"),
        param(str, "str", does_not_raise(), id="builtin type"),
        param(os, "os", does_not_raise(), id="builtin module"),
        param(
            get_qualified_name,
            "aibs_informatics_core.utils.modules.get_qualified_name",
            does_not_raise(),
            id="custom function",
        ),
        param(
            DummyClass(),
            "test.aibs_informatics_core.utils.test_modules.DummyClass",
            does_not_raise(),
            id="custom object",
        ),
        param(
            DummyClass(),
            "test.aibs_informatics_core.utils.test_modules.DummyClass",
            does_not_raise(),
            id="custom type",
        ),
    ],
)
def test__get_qualified_name(value, expected, raise_expectation):
    with raise_expectation:
        actual = get_qualified_name(value)

    if expected:
        assert actual == expected


@mark.parametrize(
    "name, expected_type, expected, raise_expectation",
    [
        param("ValueError", Exception, ValueError, does_not_raise(), id="builtin Class"),
        param(
            "aibs_informatics_core.utils.modules",
            None,
            aibs_informatics_core.utils.modules,
            does_not_raise(),
            id="loads custom module",
        ),
        param(
            "aibs_informatics_core.utils.modules.get_qualified_name",
            None,
            get_qualified_name,
            does_not_raise(),
            id="loads custom function",
        ),
        param(
            "test.aibs_informatics_core.utils.test_modules.DummyClass",
            None,
            DummyClass,
            does_not_raise(),
            id="custom type (no expected type)",
        ),
        param(
            "test.aibs_informatics_core.utils.test_modules.DummyClass",
            None,
            DummyClass,
            does_not_raise(),
            id="loads custom type (no type check)",
        ),
        param(
            "test.aibs_informatics_core.utils.test_modules.DummyChildClass",
            DummyClass,
            DummyChildClass,
            does_not_raise(),
            id="loads custom type (expected type)",
        ),
        param(
            "test.aibs_informatics_core.utils.test_modules.DummyClass",
            DummyChildClass,
            None,
            raises(ValueError),
            id="FAILs expected type check",
        ),
        param(
            "test.aibs_informatics_core.utils.test_modules.DummyClass2",
            DummyChildClass,
            None,
            raises(ValueError),
            id="FAILs finding type in module",
        ),
    ],
)
def test__load_type_from_qualified_name(name, expected_type, expected, raise_expectation):
    with raise_expectation:
        actual = load_type_from_qualified_name(name, expected_type=expected_type)

    if expected:
        assert actual == expected
