import pytest

from moa.ast import MOANodeTypes, ArrayNode, UnaryNode, BinaryNode
from moa.shape import (
    calculate_shapes,
    is_vector, is_scalar
)


def test_is_scalar():
    tree = ArrayNode(MOANodeTypes.ARRAY, (), None, (3,))
    assert is_scalar(tree)


def test_is_not_scalar():
    tree = ArrayNode(MOANodeTypes.ARRAY, (2,), None, (1, 2))
    assert not is_scalar(tree)


def test_is_vector():
    tree = ArrayNode(MOANodeTypes.ARRAY, (2,), None, (3, 5))
    assert is_vector(tree)


def test_is_not_vector():
    tree = ArrayNode(MOANodeTypes.ARRAY, (2, 2), None, (3, 5, 4, 5))
    assert not is_vector(tree)


@pytest.mark.parametrize("tree, result", [
    # ARRAY
    (ArrayNode(MOANodeTypes.ARRAY, (2,), None, (3, 5)),
     ArrayNode(MOANodeTypes.ARRAY, (2,), None, (3, 5))),
    # TRANSPOSE
    (UnaryNode(MOANodeTypes.TRANSPOSE, None,
               ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None)),
     UnaryNode(MOANodeTypes.TRANSPOSE, (5, 4, 3),
               ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None))),
    # TRANSPOSE VECTOR
    (BinaryNode(MOANodeTypes.TRANSPOSEV, None,
               ArrayNode(MOANodeTypes.ARRAY, (3,), None, (2, 0, 1)),
               ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None)),
     BinaryNode(MOANodeTypes.TRANSPOSEV, (4, 5, 3),
               ArrayNode(MOANodeTypes.ARRAY, (3,), None, (2, 0, 1)),
               ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None))),
    # PLUSRED
    (UnaryNode(MOANodeTypes.PLUSRED, None,
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None)),
     UnaryNode(MOANodeTypes.PLUSRED, (4, 5),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None))),
    # PSI
    (BinaryNode(MOANodeTypes.PSI, None,
                ArrayNode(MOANodeTypes.ARRAY, (2,), None, (3, 5)),
                ArrayNode(MOANodeTypes.ARRAY, (4, 5, 6), None, None)),
     BinaryNode(MOANodeTypes.PSI, (6,),
                ArrayNode(MOANodeTypes.ARRAY, (2,), None, (3, 5)),
                ArrayNode(MOANodeTypes.ARRAY, (4, 5, 6), None, None))),
    # PLUS EQUAL
    (BinaryNode(MOANodeTypes.PLUS, None,
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None)),
     BinaryNode(MOANodeTypes.PLUS, (3, 4, 5),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None))),
    # MINUS EQUAL
    (BinaryNode(MOANodeTypes.MINUS, None,
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None)),
     BinaryNode(MOANodeTypes.MINUS, (3, 4, 5),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None))),
    # DIVIDE EQUAL
    (BinaryNode(MOANodeTypes.DIVIDE, None,
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None)),
     BinaryNode(MOANodeTypes.DIVIDE, (3, 4, 5),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None))),
    # TIMES EQUAL
    (BinaryNode(MOANodeTypes.TIMES, None,
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None)),
     BinaryNode(MOANodeTypes.TIMES, (3, 4, 5),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None))),
    # PLUS SCALAR EXTENSION
    (BinaryNode(MOANodeTypes.PLUS, None,
                ArrayNode(MOANodeTypes.ARRAY, (), None, (4,)),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None)),
     BinaryNode(MOANodeTypes.PLUS, (3, 4, 5),
                ArrayNode(MOANodeTypes.ARRAY, (), None, (4,)),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None))),
    # MINUS SCALAR EXTENSION
    (BinaryNode(MOANodeTypes.MINUS, None,
                ArrayNode(MOANodeTypes.ARRAY, (), None, (4,)),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None)),
     BinaryNode(MOANodeTypes.MINUS, (3, 4, 5),
                ArrayNode(MOANodeTypes.ARRAY, (), None, (4,)),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None))),
    # TIMES SCALAR EXTENSION
    (BinaryNode(MOANodeTypes.TIMES, None,
                ArrayNode(MOANodeTypes.ARRAY, (), None, (4,)),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None)),
     BinaryNode(MOANodeTypes.TIMES, (3, 4, 5),
                ArrayNode(MOANodeTypes.ARRAY, (), None, (4,)),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None))),
    # DIVIDE SCALAR EXTENSION
    (BinaryNode(MOANodeTypes.DIVIDE, None,
                ArrayNode(MOANodeTypes.ARRAY, (), None, (4,)),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None)),
     BinaryNode(MOANodeTypes.DIVIDE, (3, 4, 5),
                ArrayNode(MOANodeTypes.ARRAY, (), None, (4,)),
                ArrayNode(MOANodeTypes.ARRAY, (3, 4, 5), None, None))),
])
def test_shape_unit(tree, result):
    new_tree = calculate_shapes(tree)
    assert new_tree == result


@pytest.mark.parametrize("tree,result", [
    # Lenore Simple Example #1 06/01/2018
    (BinaryNode(MOANodeTypes.PSI, None,
                ArrayNode(MOANodeTypes.ARRAY, (1,), None, (0,)),
                UnaryNode(MOANodeTypes.TRANSPOSE, None,
                          BinaryNode(MOANodeTypes.PLUS, None,
                                     ArrayNode(MOANodeTypes.ARRAY, (3, 4), 'A', None),
                                     ArrayNode(MOANodeTypes.ARRAY, (3, 4), 'B', None)))),
     (MOANodeTypes.PSI, (3,),
      (MOANodeTypes.ARRAY, (1,), None, (0,)),
      (MOANodeTypes.TRANSPOSE, (4, 3),
       (MOANodeTypes.PLUS, (3, 4),
        (MOANodeTypes.ARRAY, (3, 4), 'A', None),
        (MOANodeTypes.ARRAY, (3, 4), 'B', None))))),
])
def test_shape_integration(tree, result):
    new_tree = calculate_shapes(tree)
    assert new_tree == result
