import unittest
from dataclasses import dataclass
from typing import ClassVar, Pattern

from aibs_informatics_core.collections import (
    BaseEnum,
    DeepChainMap,
    OrderedEnum,
    OrderedStrEnum,
    PostInitMixin,
    Tree,
    ValidatedStr,
)


class DeepChainMapTests(unittest.TestCase):
    def test__merges_and_updates(self):
        d1 = {"a": [1, 2, 3], "b": {1: {"1": [1]}, "2": ["a"]}}
        d2 = {"a": 1, "b": {0: False, 1: {"1": {1: 1}}, 1: ["a"]}}
        merged = {
            "a": 1,
            "b": {0: False, 1: {"1": {1: 1}}, 1: ["a"], "2": ["a"]},
        }

        self.assertDictEqual(DeepChainMap(d2, d1).to_dict(), merged)


class AlphaNumericStr(ValidatedStr):
    regex_pattern: ClassVar[Pattern] = r"^([\w]*)$"  # type: ignore


class TwoParts(ValidatedStr):
    regex_pattern: ClassVar[Pattern] = r"([\w]+)-([\w]+)"  # type: ignore


class MinMaxStr(ValidatedStr):
    max_len: ClassVar[int] = 10
    min_len: ClassVar[int] = 2


class ValidatedStrTests(unittest.TestCase):
    def test__AlphaNumericStr__initialized_with_valid_pattern(self):
        s = "a1234aadfjghasdijfahs"
        val_s = AlphaNumericStr(s)
        self.assertEqual(s, val_s)

    def test__AlphaNumericStr__fails_to_initialize_with_invalid_pattern(self):
        s = "!2asdfe"
        with self.assertRaises(ValueError):
            AlphaNumericStr(s)

    def test__TwoParts__initializes_and_match_groups_returns_parts(self):
        region = TwoParts("part1-part2")
        self.assertTupleEqual(("part1", "part2"), region.get_match_groups())

    def test__MinMaxStr__match_groups_fails_due_to_missing_pattern_defined(self):
        s = "1234"
        val_s = MinMaxStr(s)
        with self.assertRaises(ValueError):
            val_s.get_match_groups()

    def test__MinMaxStr__initialized_with_valid_length_str(self):
        s = "1234"
        val_s = MinMaxStr(s)
        self.assertEqual(s, val_s)

    def test__MinMaxStr__fails_to_initialize_with_invalid_length_str(self):
        with self.assertRaises(ValueError):
            MinMaxStr("*" * 1)

        with self.assertRaises(ValueError):
            MinMaxStr("*" * 11)

    def test__TwoParts__is_prefixed(self):
        self.assertTrue(TwoParts.is_prefixed("wer-wer!"))
        self.assertTrue(TwoParts.is_prefixed("wer-wer!wer-wer"))
        self.assertTrue(TwoParts.is_prefixed("wer-wer"))
        self.assertFalse(TwoParts.is_prefixed("!wer-wer"))
        self.assertFalse(TwoParts.is_prefixed("werwer!"))

    def test__TwoParts__is_suffixed(self):
        self.assertTrue(TwoParts.is_suffixed("!wer-wer"))
        self.assertTrue(TwoParts.is_suffixed("wer-wer!wer-wer"))
        self.assertTrue(TwoParts.is_suffixed("wer-wer"))
        self.assertFalse(TwoParts.is_suffixed("wer-wer!"))
        self.assertFalse(TwoParts.is_suffixed("!werwer"))

    def test__TwoParts__findall_returns_all_instances(self):
        two_parts_matches = TwoParts.findall("part1-part2/part3-part4")
        self.assertListEqual(["part1-part2", "part3-part4"], two_parts_matches)
        two_parts_matches = TwoParts.findall("part1-part2-part3-part4")
        self.assertListEqual(["part1-part2", "part3-part4"], two_parts_matches)


class BaseTreeTests(unittest.TestCase):
    def test__subclass__dataclass_type(self):
        @dataclass(frozen=True)
        class Coord:
            x: int
            y: int

        tree = Tree[Coord]()

        coord1 = Coord(0, 0)
        coord2 = Coord(1, 0)
        coord3 = Coord(1, 1)

        tree.add_sequence(coord1, coord2, coord3)
        self.assertIsNotNone(tree.get_sequence(coord1, coord2, coord3))

    def test__add_sequence(self):
        str_tree = Tree[str]()
        sequence = list("abc")
        self.assertFalse(str_tree.has_sequence(*sequence))
        str_tree.add_sequence(*sequence)
        self.assertTrue(str_tree.has_sequence(*sequence))

    def test__get_sequence__returns_expected_results(self):
        str_tree = Tree[str]()
        sequence = list("abc")
        self.assertEqual(str_tree.get_sequence(*sequence), None)
        str_tree.add_sequence(*sequence)
        self.assertEqual(str_tree.get_sequence(*sequence), Tree[str]())


class PostInitMixinTests(unittest.TestCase):
    def test__simple_subclass__no_post_init__add_hook_enabled__succeeds(self):
        class Simple(PostInitMixin, add_hook=True):
            pass

        simple = Simple()

        self.assertTrue(hasattr(simple, "__post_init__"))

    def test__simple_subclass__post_init__add_hook_enabled__succeeds(self):

        actual_call_list = []

        class SimpleOverride(PostInitMixin, add_hook=True):
            def __post_init__(self):
                actual_call_list.append(SimpleOverride)

        simple = SimpleOverride()

        self.assertTrue(hasattr(simple, "__post_init__"))
        self.assertListEqual(actual_call_list, [SimpleOverride])

    def test__simple_subclass__post_init__add_hook_not_specified__does_not_call(self):
        actual_call_list = []

        class SimpleOverride(PostInitMixin):
            def __post_init__(self):
                actual_call_list.append(SimpleOverride)

        simple = SimpleOverride()

        self.assertTrue(hasattr(simple, "__post_init__"))
        self.assertListEqual(actual_call_list, [])

        simple.__post_init__()
        self.assertListEqual(actual_call_list, [SimpleOverride])

    def test__simple_subclass__post_init__add_hook_disabled__does_not_call(self):
        actual_call_list = []

        class SimpleOverride(PostInitMixin, add_hook=False):
            def __post_init__(self):
                actual_call_list.append(SimpleOverride)

        simple = SimpleOverride()

        self.assertTrue(hasattr(simple, "__post_init__"))
        self.assertListEqual(actual_call_list, [])

        simple.__post_init__()
        self.assertListEqual(actual_call_list, [SimpleOverride])

    def test__nested_subclass__calls__both_post_init(self):
        actual_call_list = []

        class Parent(PostInitMixin, add_hook=True):
            def __post_init__(self):
                actual_call_list.append(Parent)

        class Child(Parent):
            def __post_init__(self):
                super().__post_init__()
                actual_call_list.append(Child)

        child = Child()

        self.assertListEqual(actual_call_list, [Parent, Child])

    def test__nested_subclass__calls__both_post_init__parent_missing(self):
        actual_call_list = []

        class Parent(PostInitMixin, add_hook=True):
            pass

        class Child(Parent):
            def __post_init__(self):
                super().__post_init__()
                actual_call_list.append(Child)

        child = Child()

        self.assertListEqual(actual_call_list, [Child])

    def test__simple_subclass__handles_dataclass_deco(self):
        @dataclass
        class SimpleOverride(PostInitMixin):
            a: int = 1

            def __post_init__(self):
                self.a += 1

        simple = SimpleOverride()
        self.assertEqual(simple.a, 2)

    def test__multi_subclass__handles_properly(self):

        actual_call_list = []

        @dataclass
        class Parent:
            def __post_init__(self):
                actual_call_list.append(Parent)

        class Child(Parent, PostInitMixin):
            def __post_init__(self):
                super().__post_init__()
                actual_call_list.append(Child)

        class Child2(PostInitMixin, Parent):
            def __post_init__(self):
                super().__post_init__()
                actual_call_list.append(Child2)

        child = Child()
        child2 = Child2()
        self.assertListEqual(actual_call_list, [Parent, Child, Parent, Child2])

    def test__nested_subclass__handles_properly(self):

        actual_call_list = []

        @dataclass
        class Parent(PostInitMixin):
            def __post_init__(self):
                actual_call_list.append(Parent)

        class Child(Parent, PostInitMixin):
            def __post_init__(self):
                super().__post_init__()
                actual_call_list.append(Child)

        child = Child()
        self.assertListEqual(actual_call_list, [Parent, Child])


class BaseEnumTests(unittest.TestCase):
    def test__eq__works_as_expected(self):
        class Ints(BaseEnum):
            ONE = 1
            UNO = 1
            TWO = "2"

        self.assertEqual(Ints.ONE, Ints.ONE)
        self.assertEqual(Ints.ONE, Ints.ONE.value)
        self.assertEqual(Ints.UNO, Ints.UNO.value)
        self.assertEqual(Ints.UNO, Ints.ONE.value)
        self.assertEqual(Ints.TWO, Ints.TWO.value)

    def test__values__returns_values(self):
        class Ints(BaseEnum):
            ONE = 1
            UNO = 1
            TWO = "2"

        self.assertListEqual(Ints.values(), [1, "2"])


class OrderedEnumTests(unittest.TestCase):
    def test__lt__works_as_intended(self):
        class Ints(OrderedEnum):
            ONE = 1
            TWO = "2"
            ZERO = 0

        self.assertLess(Ints.ONE, Ints.TWO)
        self.assertGreater(Ints.ZERO, Ints.TWO)
        self.assertLess(Ints.TWO, Ints.ZERO.value)
        with self.assertRaises(Exception):
            Ints.ONE < -1

    def test__name_order__captures_ordering(self):
        class Ints(OrderedEnum):
            ONE = 1
            TWO = "2"
            ZERO = 0

        self.assertEqual(Ints.ONE.__name_order__, 0)
        self.assertEqual(Ints.TWO.__name_order__, 1)
        self.assertEqual(Ints.ZERO.__name_order__, 2)


class OrderedStrEnumTests(unittest.TestCase):
    def test__comparisons(self):
        class ACBs(OrderedStrEnum):
            A = "a"
            C = "C"
            B = "B"

        self.assertEqual(ACBs.A, ACBs.A)
        self.assertEqual(ACBs.A, ACBs.A.value)
        self.assertLessEqual(ACBs.A, ACBs.A)
        self.assertLessEqual(ACBs.A, ACBs.A.value)
        self.assertGreaterEqual(ACBs.A, ACBs.A)
        self.assertGreaterEqual(ACBs.A, ACBs.A.value)
        self.assertLess(ACBs.A, ACBs.C)
        self.assertLess(ACBs.A, ACBs.C.value)
        self.assertLess(ACBs.A, ACBs.B)
        self.assertLess(ACBs.A, ACBs.B.value)

        self.assertGreater(ACBs.B, ACBs.A)
        self.assertGreater(ACBs.B, ACBs.A.value)
        self.assertGreater(ACBs.B, ACBs.C)
        self.assertGreater(ACBs.B, ACBs.C.value)

        self.assertGreater(ACBs.C, ACBs.A)
        self.assertGreater(ACBs.C, ACBs.A.value)
        self.assertLess(ACBs.C, ACBs.B)
        self.assertLess(ACBs.C, ACBs.B.value)
