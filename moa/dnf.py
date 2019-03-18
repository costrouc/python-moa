import itertools

from .core import MOAException
from .ast import (
    MOANodeTypes,
    Node,
    add_symbol,
    generate_unique_index_name, generate_unique_array_name,
    is_binary_operation, is_unary_operation, is_array,
    has_symbolic_elements, is_symbolic_element,
    node_traversal,
)
from .shape import dimension, is_vector, is_scalar


class MOAReductionError(MOAException):
    pass


def add_indexing_node(symbol_table, node):
    """Adds indexing into the MOA AST

    For example: <i0 i1> psi (A + B)
    """
    condition_node = None
    if node.node_type == MOANodeTypes.CONDITION:
        condition_node = node.condition_node
        node = node.right_node

    index_symbols = ()
    for bound in node.shape:
        index_name = generate_unique_index_name(symbol_table)
        symbol_table = add_symbol(symbol_table, index_name, MOANodeTypes.INDEX, (), (0, bound))
        index_symbols = index_symbols + (Node(MOANodeTypes.ARRAY, (), index_name),)

    array_name = generate_unique_array_name(symbol_table)
    symbol_table = add_symbol(symbol_table, array_name, MOANodeTypes.ARRAY, (len(index_symbols),), index_symbols)
    vector_node = Node(MOANodeTypes.ARRAY, (len(index_symbols),), array_name)
    node = Node(MOANodeTypes.PSI, node.shape, vector_node, node)

    if condition_node:
        node = Node(MOANodeTypes.CONDITION, node.shape, condition_node, node)
    return symbol_table, node


def reduce_to_dnf(symbol_table, node):
    """Preorder traversal and replacement of ast tree

    In the future the symbol table will have to be constructed earlier
    for arrays and variables for shapes.

    TODO: change exception to warning to allow for partial replacement
    """
    symbol_table, node = add_indexing_node(symbol_table, node)
    symbol_table, node = node_traversal(symbol_table, node, _reduce_replacement, traversal='pre')
    return symbol_table, node


def _reduce_replacement(symbol_table, node):
    reduction_rules = {
        (MOANodeTypes.PSI, None, MOANodeTypes.ASSIGN): _reduce_psi_assign,
        (MOANodeTypes.PSI, None, MOANodeTypes.PSI): _reduce_psi_psi,
        (MOANodeTypes.PSI, None, MOANodeTypes.TRANSPOSE): _reduce_psi_transpose,
        (MOANodeTypes.PSI, None, MOANodeTypes.TRANSPOSEV): _reduce_psi_transposev,
        (MOANodeTypes.PSI, None, (MOANodeTypes.PLUS, MOANodeTypes.MINUS, MOANodeTypes.TIMES, MOANodeTypes.DIVIDE)): _reduce_psi_plus_minus_times_divide,
        (MOANodeTypes.PSI, None, (
            (MOANodeTypes.DOT, MOANodeTypes.PLUS),
            (MOANodeTypes.DOT, MOANodeTypes.MINUS),
            (MOANodeTypes.DOT, MOANodeTypes.TIMES),
            (MOANodeTypes.DOT, MOANodeTypes.DIVIDE))): _reduce_psi_outer_plus_minus_times_divide,
        (MOANodeTypes.PSI, None, (
            (MOANodeTypes.REDUCE, MOANodeTypes.PLUS),
            (MOANodeTypes.REDUCE, MOANodeTypes.MINUS),
            (MOANodeTypes.REDUCE, MOANodeTypes.TIMES),
            (MOANodeTypes.REDUCE, MOANodeTypes.DIVIDE))): _reduce_psi_reduce_plus_minus_times_divide,
    }

    def _matches(compare_node, node_rule):
        if node_rule is not None:
            if isinstance(node_rule, tuple) and compare_node.node_type not in node_rule:
                return False
            elif not isinstance(node_rule, tuple) and compare_node.node_type != node_rule:
                return False
        return True

    if is_array(node):
        return None, None

    for rule, replacement_function in reduction_rules.items():
        root_node, left_node, right_node = rule
        if not _matches(node, root_node):
            continue
        if not is_binary_operation(node) and left_node is not None:
            continue
        if is_binary_operation(node) and not _matches(node.left_node, left_node):
            continue
        if not _matches(node.right_node, right_node):
            continue
        return replacement_function(symbol_table, node)
    return None, None


def _reduce_psi_assign(symbol_table, node):
    """<i j> psi ... assign ... => <i j> psi ... assign <i j> psi ..."""
    return symbol_table, Node(MOANodeTypes.ASSIGN, node.shape,
                                    Node(MOANodeTypes.PSI, node.shape, node.left_node, node.right_node.left_node),
                                    Node(MOANodeTypes.PSI, node.shape, node.left_node, node.right_node.right_node))



def _reduce_psi_psi(symbol_table, node):
    """<i j> psi <k l> psi ... => <k l i j> psi ..."""
    if not is_vector(symbol_table, node.right_node.left_node) or symbol_table[node.right_node.left_node.symbol_node].value is None:
        raise MOAReductionError('<...> PSI <...> PSI ... replacement assumes that the inner left_node is vector with defined values')

    array_name = generate_unique_array_name(symbol_table)
    array_values = symbol_table[node.right_node.left_node.symbol_node].value + symbol_table[node.left_node.symbol_node].value
    symbol_table = add_symbol(symbol_table, array_name, MOANodeTypes.ARRAY, (len(array_values),), array_values)

    return symbol_table, Node(node.node_type, node.shape,
                                    Node(MOANodeTypes.ARRAY, (len(array_values),), array_name),
                                    node.right_node.right_node)


def _reduce_psi_transpose(symbol_table, node):
    """<i j k> psi transpose ... => <k j i> psi ..."""
    array_name = generate_unique_array_name(symbol_table)
    array_values = symbol_table[node.left_node.symbol_node].value[::-1]
    symbol_table = add_symbol(symbol_table, array_name, MOANodeTypes.ARRAY, (len(array_values),), array_values)

    return symbol_table, Node(MOANodeTypes.PSI, node.shape,
                                    Node(MOANodeTypes.ARRAY, (len(array_values),), array_name),
                                    node.right_node.right_node)


def _reduce_psi_transposev(symbol_table, node):
    """<i j k> psi <2 0 1> transpose ... => <k i j> psi ..."""
    array_name = generate_unique_array_name(symbol_table)
    array_values = tuple(s for _, s in sorted(zip(symbol_table[node.right_node.left_node.symbol_node].value, symbol_table[node.left_node.symbol_node].value), key=lambda pair: pair[0]))
    symbol_table = add_symbol(symbol_table, array_name, MOANodeTypes.ARRAY, (len(array_values),), array_values)
    return symbol_table, Node(MOANodeTypes.PSI, node.shape,
                                    Node(MOANodeTypes.ARRAY, (len(array_values),), array_name),
                                    node.right_node.right_node)


def _reduce_psi_reduce_plus_minus_times_divide(symbol_table, node):
    index_name = generate_unique_index_name(symbol_table)
    symbol_table = add_symbol(symbol_table, index_name, MOANodeTypes.INDEX, (), (0, node.right_node.right_node.shape[0]))

    index_vector = (Node(MOANodeTypes.ARRAY, (), index_name),) + symbol_table[node.left_node.symbol_node].value
    array_name = generate_unique_array_name(symbol_table)
    symbol_table = add_symbol(symbol_table, array_name, MOANodeTypes.ARRAY, (len(index_vector),), index_vector)

    return symbol_table, Node(node.right_node.node_type, node.shape, index_name,
                                    Node(MOANodeTypes.PSI, node.shape,
                                               Node(MOANodeTypes.ARRAY, (len(index_vector),), array_name),
                                               node.right_node.right_node))






def _reduce_psi_outer_plus_minus_times_divide(symbol_table, node):
    left_array_name = generate_unique_array_name(symbol_table)
    left_dimension = dimension(symbol_table, node.right_node.left_node)
    symbol_table = add_symbol(symbol_table, left_array_name, MOANodeTypes.ARRAY, (left_dimension,), symbol_table[node.left_node.symbol_node].value[:left_dimension])

    right_array_name = generate_unique_array_name(symbol_table)
    right_dimension = dimension(symbol_table, node.right_node.right_node)
    symbol_table = add_symbol(symbol_table, right_array_name, MOANodeTypes.ARRAY, (right_dimension,), symbol_table[node.left_node.symbol_node].value[-right_dimension:])

    return symbol_table, Node(node.right_node.node_type[1], node.shape,
                                    Node(MOANodeTypes.PSI, node.shape,
                                               Node(MOANodeTypes.ARRAY, (left_dimension,), left_array_name),
                                               node.right_node.left_node),
                                    Node(MOANodeTypes.PSI, node.shape,
                                               Node(MOANodeTypes.ARRAY, (right_dimension,), right_array_name),
                                               node.right_node.right_node))


def _reduce_psi_plus_minus_times_divide(symbol_table, node):
    """<i j> psi (... (+-*/) ...) => (<i j> psi ...) (+-*/) (<k l> psi ...)

    Scalar Extension
      <i j> psi (scalar (+-*/) ...) = scalar (+-*/) <i j> psi ...
    """
    if is_scalar(symbol_table, node.right_node.left_node):
        left_node = node.right_node.left_node
    else:
        left_node = Node(MOANodeTypes.PSI, node.shape,
                               node.left_node,
                               node.right_node.left_node)

    if is_scalar(symbol_table, node.right_node.right_node):
        right_node = node.right_node.right_node
    else:
        right_node = Node(MOANodeTypes.PSI, node.shape,
                                node.left_node,
                                node.right_node.right_node)

    return symbol_table, Node(node.right_node.node_type, node.shape, left_node, right_node)
