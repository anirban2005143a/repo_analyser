from tree_sitter import Parser
from tree_sitter_language_pack import get_language
from file_parsing.extractors.BaseParser import BaseParser
from file_parsing.extractors.type_mapping.python_type_mapping import PYTHON_TYPE_MAPPING


class PythonParser(BaseParser):
    """
    Extract meaningful Python code entities from a Tree-sitter syntax tree.

    The extractor intentionally does NOT expose every Tree-sitter AST node.
    It extracts structural/semantic entities that can later become graph
    nodes in Neo4j.

    The actual extraction methods are implemented as module-level functions
    below to keep this class scope small and focused on the public API.
    """

    def __init__(self):
        self.language = get_language("python")
        self.parser = Parser(self.language)

    def parse(self, source_code: bytes):
        """
        Parse Python source code and return the extracted file scope.
        """

        tree = self.parser.parse(source_code)

        return {
            "type": map_node_type("module"),
            "children": extract_scope(
                self,
                tree.root_node,
                source_code,
            ),
        }


# ================================================================
# SCOPE EXTRACTION
# ================================================================


def extract_scope(extractor, node, source_code):
    """
    Extract meaningful nodes from a scope.

    A scope can be:
    - module
    - class
    - function
    - if/else/elif body
    - loop body
    - try/except/finally body
    - with body
    - match/case body
    """

    children = []

    for child in node.children:

        # --------------------------------------------------------
        # Comments
        # --------------------------------------------------------

        if child.type == "comment":
            children.append({
                "type": map_node_type(child.type),
                "start_line": child.start_point[0] + 1,
                "end_line": child.end_point[0] + 1,
                "text": text(extractor, child, source_code),
            })

            continue

        # --------------------------------------------------------
        # Imports
        # --------------------------------------------------------

        if child.type in {
            "import_statement",
            "import_from_statement",
        }:
            children.append(
                extract_import(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # --------------------------------------------------------
        # Assignments
        # --------------------------------------------------------

        if child.type in {
            "assignment",
            "augmented_assignment",
            "named_expression",
            "annotated_assignment",
        }:
            children.append(
                extract_assignment(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # --------------------------------------------------------
        # Decorated definitions
        # --------------------------------------------------------

        if child.type == "decorated_definition":
            extracted = extract_decorated_definition(
                extractor,
                child,
                source_code,
            )

            if extracted:
                children.append(extracted)

            continue

        # --------------------------------------------------------
        # Normal class
        # --------------------------------------------------------

        if child.type == "class_definition":
            children.append(
                extract_class(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # --------------------------------------------------------
        # Normal function
        # --------------------------------------------------------

        if child.type in {
            "function_definition",
            "async_function_definition",
        }:
            children.append(
                extract_function(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # --------------------------------------------------------
        # IF / ELIF / ELSE
        # --------------------------------------------------------

        if child.type == "if_statement":
            children.append(
                extract_if(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # --------------------------------------------------------
        # FOR
        # --------------------------------------------------------

        if child.type in {
            "for_statement",
            "async_for_statement",
        }:
            children.append(
                extract_for(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # --------------------------------------------------------
        # WHILE
        # --------------------------------------------------------

        if child.type == "while_statement":
            children.append(
                extract_while(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # --------------------------------------------------------
        # TRY / EXCEPT / FINALLY
        # --------------------------------------------------------

        if child.type == "try_statement":
            children.append(
                extract_try(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # --------------------------------------------------------
        # WITH
        # --------------------------------------------------------

        if child.type in {
            "with_statement",
            "async_with_statement",
        }:
            children.append(
                extract_with(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # --------------------------------------------------------
        # MATCH / CASE
        # --------------------------------------------------------

        if child.type == "match_statement":
            children.append(
                extract_match(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # --------------------------------------------------------
        # Any other node
        #
        # Recurse because a meaningful construct can exist inside
        # another syntax wrapper.
        # --------------------------------------------------------

        nested = extract_scope(
            extractor,
            child,
            source_code,
        )

        if nested:
            children.extend(nested)

    return children


# ================================================================
# IMPORTS
# ================================================================


def extract_import(extractor, node, source_code):
    return {
        "type": map_node_type(node.type),
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
    }


# ================================================================
# ASSIGNMENTS
# ================================================================


def extract_assignment(extractor, node, source_code):
    return {
        "type": map_node_type(node.type),
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
    }


# ================================================================
# CLASS
# ================================================================


def extract_class(extractor, node, source_code):
    name = None

    for child in node.children:
        if child.type == "identifier":
            name = text(
                extractor,
                child,
                source_code,
            )
            break

    result = {
        "type": map_node_type(node.type),
        "name": name,
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
        "children": [],
    }

    # ------------------------------------------------------------
    # Extract class body
    # ------------------------------------------------------------

    body = find_child(node, "block")

    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    # ------------------------------------------------------------
    # Extract inheritance
    # ------------------------------------------------------------

    superclasses = []

    for child in node.children:
        if child.type == "argument_list":

            for argument in child.children:

                if argument.type not in {
                    "(",
                    ")",
                    ",",
                }:
                    superclasses.append(
                        text(
                            extractor,
                            argument,
                            source_code,
                        )
                    )

    if superclasses:
        result["bases"] = superclasses

    return result


# ================================================================
# FUNCTION
# ================================================================


def extract_function(extractor, node, source_code):
    name = None

    for child in node.children:

        if child.type == "identifier":
            name = text(
                extractor,
                child,
                source_code,
            )
            break

    result = {
        "type": map_node_type(node.type),
        "name": name,
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
        "children": [],
    }

    # ------------------------------------------------------------
    # Async function
    # ------------------------------------------------------------

    if node.type == "async_function_definition":
        result["async"] = True

    # ------------------------------------------------------------
    # Extract parameters
    # ------------------------------------------------------------

    parameters = find_child(
        node,
        "parameters",
    )

    if parameters:
        result["parameters"] = text(
            extractor,
            parameters,
            source_code,
        )

    # ------------------------------------------------------------
    # Extract return type
    # ------------------------------------------------------------

    return_type = find_child(
        node,
        "type",
    )

    if return_type:
        result["return_type"] = text(
            extractor,
            return_type,
            source_code,
        )

    # ------------------------------------------------------------
    # Extract function body
    # ------------------------------------------------------------

    body = find_child(
        node,
        "block",
    )

    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    return result


# ================================================================
# DECORATED DEFINITION
# ================================================================


def extract_decorated_definition(
    extractor,
    node,
    source_code,
):
    """
    Handles:

        @decorator
        def func():
            ...

    and:

        @decorator(...)
        class MyClass:
            ...
    """

    decorators = []
    definition = None

    for child in node.children:

        if child.type == "decorator":

            decorators.append({
                "type": map_node_type(child.type),
                "text": text(
                    extractor,
                    child,
                    source_code,
                ),
                "start_line": child.start_point[0] + 1,
                "end_line": child.end_point[0] + 1,
            })

        elif child.type in {
            "function_definition",
            "async_function_definition",
            "class_definition",
        }:
            definition = child

    if definition is None:
        return None

    # ------------------------------------------------------------
    # Extract actual definition
    # ------------------------------------------------------------

    if definition.type in {
        "function_definition",
        "async_function_definition",
    }:
        result = extract_function(
            extractor,
            definition,
            source_code,
        )

    else:
        result = extract_class(
            extractor,
            definition,
            source_code,
        )

    # ------------------------------------------------------------
    # Attach decorators
    # ------------------------------------------------------------

    if decorators:
        result["decorators"] = decorators

    # The decorated definition starts at the first decorator.
    result["start_line"] = node.start_point[0] + 1
    result["end_line"] = node.end_point[0] + 1
    result["text"] = text(
        extractor,
        node,
        source_code,
    )

    return result


# ================================================================
# IF / ELIF / ELSE
# ================================================================


def extract_if(extractor, node, source_code):
    result = {
        "type": map_node_type(node.type),
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
        "children": [],
    }

    for child in node.children:

        # --------------------------------------------------------
        # Main IF body
        # --------------------------------------------------------

        if child.type == "block":

            result["children"].extend(
                extract_scope(
                    extractor,
                    child,
                    source_code,
                )
            )

        # --------------------------------------------------------
        # ELIF
        # --------------------------------------------------------

        elif child.type == "elif_clause":

            result["children"].append(
                extract_elif(
                    extractor,
                    child,
                    source_code,
                )
            )

        # --------------------------------------------------------
        # ELSE
        # --------------------------------------------------------

        elif child.type == "else_clause":

            result["children"].append(
                extract_else(
                    extractor,
                    child,
                    source_code,
                )
            )

    return result


def extract_elif(extractor, node, source_code):
    result = {
        "type": map_node_type(node.type),
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
        "children": [],
    }

    body = find_child(
        node,
        "block",
    )

    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    return result


def extract_else(extractor, node, source_code):
    result = {
        "type": map_node_type(node.type),
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
        "children": [],
    }

    body = find_child(
        node,
        "block",
    )

    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    return result


# ================================================================
# FOR
# ================================================================


def extract_for(extractor, node, source_code):
    result = {
        "type": map_node_type(node.type),
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
        "children": [],
    }

    if node.type == "async_for_statement":
        result["async"] = True

    body = find_child(
        node,
        "block",
    )

    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    return result


# ================================================================
# WHILE
# ================================================================


def extract_while(extractor, node, source_code):
    result = {
        "type": map_node_type(node.type),
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
        "children": [],
    }

    body = find_child(
        node,
        "block",
    )

    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    return result


# ================================================================
# TRY / EXCEPT / ELSE / FINALLY
# ================================================================


def extract_try(extractor, node, source_code):
    """
    Handles:

        try:
            ...

        except ValueError:
            ...

        except Exception as e:
            ...

        else:
            ...

        finally:
            ...

    Also handles except* clauses using the same generic
    exception-clause extraction.
    """

    result = {
        "type": map_node_type(node.type),
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
        "children": [],
    }

    for child in node.children:

        # --------------------------------------------------------
        # Main try body
        # --------------------------------------------------------

        if child.type == "block":

            result["children"].extend(
                extract_scope(
                    extractor,
                    child,
                    source_code,
                )
            )

        # --------------------------------------------------------
        # except / except*
        # --------------------------------------------------------

        elif child.type in {
            "except_clause",
            "except_group_clause",
        }:

            result["children"].append(
                extract_except(
                    extractor,
                    child,
                    source_code,
                )
            )

        # --------------------------------------------------------
        # else attached to try
        # --------------------------------------------------------

        elif child.type == "else_clause":

            result["children"].append(
                extract_try_else(
                    extractor,
                    child,
                    source_code,
                )
            )

        # --------------------------------------------------------
        # finally
        # --------------------------------------------------------

        elif child.type == "finally_clause":

            result["children"].append(
                extract_finally(
                    extractor,
                    child,
                    source_code,
                )
            )

    return result


def extract_except(extractor, node, source_code):
    result = {
        "type": map_node_type(node.type),
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
        "children": [],
    }

    # ------------------------------------------------------------
    # Extract exception type / name where available
    # ------------------------------------------------------------

    exception_types = []

    for child in node.children:

        if child.type in {
            "identifier",
            "attribute",
            "tuple",
            "list",
            "as_pattern",
        }:
            exception_types.append(
                text(
                    extractor,
                    child,
                    source_code,
                )
            )

    if exception_types:
        result["exception"] = exception_types

    # ------------------------------------------------------------
    # Extract except body
    # ------------------------------------------------------------

    body = find_child(
        node,
        "block",
    )

    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    return result


def extract_try_else(extractor, node, source_code):
    result = {
        "type": map_node_type(node.type),
        "context": "try",
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
        "children": [],
    }

    body = find_child(
        node,
        "block",
    )

    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    return result


def extract_finally(extractor, node, source_code):
    result = {
        "type": map_node_type(node.type),
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
        "children": [],
    }

    body = find_child(
        node,
        "block",
    )

    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    return result


# ================================================================
# WITH
# ================================================================


def extract_with(extractor, node, source_code):
    """
    Handles:

        with open("file.txt") as f:
            ...

    and:

        with A() as a, B() as b:
            ...

    and async with.
    """

    result = {
        "type": map_node_type(node.type),
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
        "children": [],
    }

    if node.type == "async_with_statement":
        result["async"] = True

    # ------------------------------------------------------------
    # Extract with clauses
    # ------------------------------------------------------------

    items = []

    for child in node.children:

        if child.type in {
            "with_clause",
            "with_item",
        }:
            items.append({
                "type": map_node_type(child.type),
                "text": text(
                    extractor,
                    child,
                    source_code,
                ),
                "start_line": child.start_point[0] + 1,
                "end_line": child.end_point[0] + 1,
            })

    if items:
        result["items"] = items

    # ------------------------------------------------------------
    # Extract body
    # ------------------------------------------------------------

    body = find_child(
        node,
        "block",
    )

    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    return result


# ================================================================
# MATCH / CASE
# ================================================================


def extract_match(extractor, node, source_code):
    """
    Handles Python 3.10+:

        match value:
            case 1:
                ...

            case _:
                ...
    """

    result = {
        "type": map_node_type(node.type),
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
        "children": [],
    }

    for child in node.children:

        if child.type == "case_clause":

            result["children"].append(
                extract_case(
                    extractor,
                    child,
                    source_code,
                )
            )

        elif child.type == "block":

            result["children"].extend(
                extract_scope(
                    extractor,
                    child,
                    source_code,
                )
            )

    return result


def extract_case(extractor, node, source_code):
    result = {
        "type": map_node_type(node.type),
        "start_line": node.start_point[0] + 1,
        "end_line": node.end_point[0] + 1,
        "text": text(extractor, node, source_code),
        "children": [],
    }

    body = find_child(
        node,
        "block",
    )

    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    return result


# ================================================================
# HELPERS
# ================================================================


def map_node_type(node_type):
    """
    Return the canonical semantic type for a Python Tree-sitter node.
    """

    return PYTHON_TYPE_MAPPING.get(node_type, node_type)


def find_child(node, child_type):
    """
    Find the first direct child with the requested Tree-sitter
    node type.
    """

    for child in node.children:

        if child.type == child_type:
            return child

    return None


def text(extractor, node, source_code):
    """
    Return the exact source text represented by a Tree-sitter node.

    The extractor argument is intentionally accepted so this helper
    has the same calling convention as the other extraction functions.
    """

    return source_code[
        node.start_byte:node.end_byte
    ].decode(
        "utf-8",
        errors="replace",
    )