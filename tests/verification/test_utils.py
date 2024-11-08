"""Tests of this test package's utils module."""

import pytest

from .utils import assert_public_method_signature_equality


pytestmark = [pytest.mark.verification, pytest.mark.disable_db]


class TestPublicMethodSignatureEquality:
    def test_identity(self):
        """Test when applied against the same class."""

        class ClassA:
            def method_one(self, x, y): ...

            def method_two(self, z): ...

        assert_public_method_signature_equality(ClassA, ClassA)

    def test_matching_methods(self):
        """Test when methods match between classes."""

        class ClassA:
            def method_one(self, x, y): ...

            def method_two(self, z): ...

        # This class is identical to Class A.
        class ClassB:
            def method_one(self, x, y): ...

            def method_two(self, z): ...

        assert_public_method_signature_equality(ClassA, ClassB)

    def test_signature_mismatch(self):
        """Test when method signatures differ between classes."""

        class ClassA:
            def method_one(self, x, y): ...

            def method_two(self, z): ...

        # The same as A, but a method has a different signature.
        class ClassC:
            # Different signature to A.method_one.
            def method_one(self, x): ...

            def method_two(self, z): ...

        with pytest.raises(AssertionError, match="signature mismatch"):
            assert_public_method_signature_equality(ClassA, ClassC)

    def test_extra_method(self):
        """Test when the second class has an extra method."""

        class ClassA:
            def method_one(self, x, y): ...

            def method_two(self, z): ...

        # The same as A, but with an extra method.
        class ClassD:
            def method_one(self, x, y): ...

            def method_two(self, z): ...

            def method_three(self): ...

        with pytest.raises(AssertionError, match="methods mismatch"):
            assert_public_method_signature_equality(ClassA, ClassD)

    def test_missing_method(self):
        """Test when a method is missing in the second class."""

        class ClassA:
            def method_one(self, x, y): ...

            def method_two(self, z): ...

        # The same as A, but with an extra method.
        class ClassD:
            def method_one(self, x, y): ...

            def method_two(self, z): ...

            def method_three(self): ...

        with pytest.raises(AssertionError, match="methods mismatch"):
            assert_public_method_signature_equality(ClassD, ClassA)

    def test_ignore_methods(self):
        """Test when certain methods are ignored in the comparison."""

        class ClassA:
            def method_one(self, x, y): ...

            def method_two(self, z): ...

        # The same as A, but with an extra method.
        class ClassD:
            def method_one(self, x, y): ...

            def method_two(self, z): ...

            def method_three(self): ...

        assert_public_method_signature_equality(
            ClassA, ClassD, ignored_methods=["method_three"]
        )

    def test_ignore_private_methods(self):
        """Test that extra private methods are ignored."""

        class ClassA:
            def method_one(self, x, y): ...

            def method_two(self, z): ...

        # The same as A, but with a private method.
        class ClassE:
            def method_one(self, x, y): ...

            def method_two(self, z): ...

            def _private_method(self): ...

        assert_public_method_signature_equality(ClassA, ClassE)
