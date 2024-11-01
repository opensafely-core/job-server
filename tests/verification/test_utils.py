"""Tests of this test package's utils module."""

import pytest

from .utils import assert_public_method_signature_equality


#####################################################################
# Classes for tests of assert_public_method_signature_equality


class ClassA:
    def method_one(self, x, y):
        pass

    def method_two(self, z):
        pass


# The same as A.
class ClassB:
    def method_one(self, x, y):
        pass

    def method_two(self, z):
        pass


# The same as A, but a method has a different signature.
class ClassC:
    # Different signature to A.method_one.
    def method_one(self, x):
        pass

    def method_two(self, z):
        pass


# The same as A, but with an extra method.
class ClassD:
    def method_one(self, x, y):
        pass

    def method_two(self, z):
        pass

    def method_three(self):
        pass


# The same as A, but with a private method.
class ClassE:
    def method_one(self, x, y):
        pass

    def method_two(self, z):
        pass

    def _private_method(self):
        pass


#####################################################################


class TestPublicMethodSignatureEquality:
    def test_identity(cls):
        """Test when applied against the same class."""
        for cls in (ClassA, ClassB, ClassC, ClassD, ClassE):
            assert_public_method_signature_equality(cls, cls)

    def test_matching_methods(cls):
        """Test when methods match between classes."""
        assert_public_method_signature_equality(ClassA, ClassB)

    def test_signature_mismatch(cls):
        """Test when method signatures differ between classes."""
        with pytest.raises(AssertionError, match="signature mismatch"):
            assert_public_method_signature_equality(ClassA, ClassC)

    def test_extra_method(cls):
        """Test when the second class has an extra method."""
        with pytest.raises(AssertionError, match="methods mismatch"):
            assert_public_method_signature_equality(ClassA, ClassD)

    def test_missing_method(cls):
        """Test when a method is missing in the second class."""
        with pytest.raises(AssertionError, match="methods mismatch"):
            assert_public_method_signature_equality(ClassD, ClassA)

    def test_ignore_methods(cls):
        """Test when certain methods are ignored in the comparison."""
        assert_public_method_signature_equality(
            ClassA, ClassD, ignored_methods=["method_three"]
        )

    def test_ignore_private_methods(cls):
        """Test that extra private methods are ignored."""
        assert_public_method_signature_equality(ClassA, ClassE)


#####################################################################
