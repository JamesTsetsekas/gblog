"""A deliberately simple reachability check for the synthetic module.

It parses a module with `ast`, starts from the names in `__all__`, follows calls to
other functions defined in the same file, and reports which functions are reachable.
It is a heuristic for a single file. It does not understand dynamic calls, imports
across modules, reflection, framework routing or configuration. A real project needs
its own entry point inventory, and in practice a human decision about exposure.
Neither __all__ nor an underscore prevents direct imports by other consumers.
An absent path in this graph is missing evidence, not proof of unreachability.
"""
import ast
import inspect


def reachable_functions(module) -> set:
    tree = ast.parse(inspect.getsource(module))
    defs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    public = set(getattr(module, "__all__", []))
    seen, stack = set(), [name for name in public if name in defs]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        for node in ast.walk(defs[name]):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in defs:
                stack.append(node.func.id)
    return seen


def defined_functions(module) -> set:
    tree = ast.parse(inspect.getsource(module))
    return {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
