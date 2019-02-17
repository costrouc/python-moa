import ast

from ..ast import MOANodeTypes, postorder_replacement


def python_backend(tree):
    return postorder_replacement(tree, _ast_replacement)


def _ast_replacement(node):
    _NODE_AST_MAP = {
        MOANodeTypes.ARRAY: _ast_array,
        MOANodeTypes.PSI: _ast_psi,
        MOANodeTypes.PLUS: _ast_plus
    }
    return _NODE_AST_MAP[node.node_type](node)


def _ast_psi(node):
    return ast.Subscript(value=node.right_node,
                         slice=ast.Index(value=node.left_node),
                         ctx=ast.Load())


def _ast_array(node):
    if node.name is None: # materialize view
        indicies = [ast.Str(i) if isinstance(i, str) else ast.Num(i) for i in node.value]
        return ast.Tuple(elts=indicies, ctx=ast.Load())
    return ast.Name(id=node.name, ctx=ast.Load())


def _ast_plus(node):
    return ast.BinOp(left=node.left_node, op=ast.Add(), right=node.right_node)
