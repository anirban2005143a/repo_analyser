from hashlib import sha1
from pathlib import Path
import re

from tree_sitter import Parser
from tree_sitter_language_pack import get_language
from file_parsing.extractors.BaseParser import BaseParser


# ============================================================================
# JAVASCRIPT PARSER
# ============================================================================


class JavaScriptParser(BaseParser):
    """
    Extract meaningful JavaScript code entities from a Tree-sitter syntax tree.

    This intentionally is NOT a full JavaScript AST dump.

    The parser promotes semantic / structural constructs that are useful as
    graph nodes in a code graph (for example Neo4j):

        - imports / exports
        - variable declarations
        - assignments
        - functions / arrow functions
        - classes / methods / fields / static blocks
        - if / else-if / else
        - for / for-in / for-of / while / do-while
        - try / catch / finally
        - switch / case / default
        - with / labeled statements
        - meaningful expression statements
        - comments

    It intentionally does NOT expose tiny syntax nodes such as:

        return, break, continue, commas, parentheses, semicolons, identifiers
        inside expressions, operators, argument-list elements, etc.

    The emitted tree therefore sits between a concrete syntax tree and a
    compiler CFG: it preserves useful source structure without exploding into
    token-level nodes.

    Every emitted node gets common source/file metadata:

        node_id, language, file_path, file_name,
        start_line/start_column, end_line/end_column,
        start_byte/end_byte, text

    ``parse(source_code)`` remains compatible with the Python parser style.
    ``parse(source_code, file_path=...)`` adds file-aware graph metadata.
    """

    def __init__(self, emit_control_transfer_nodes=False):
        self.language = get_language("javascript")
        self.parser = Parser(self.language)
        self.emit_control_transfer_nodes = emit_control_transfer_nodes

        # Populated for the current parse. Keeping this on the extractor keeps
        # all module-level extraction helpers consistent with PythonParser.
        self.file_path = None
        self.file_name = None
        self.file_id = None
        self.content_hash = None

    def parse(self, source_code: bytes, file_path=None):
        """
        Parse JavaScript source code and return the extracted file scope.

        Parameters
        ----------
        source_code:
            JavaScript source as UTF-8 bytes.
        file_path:
            Optional path used only as graph/source metadata. It is never
            resolved or read from disk by this parser.
        """

        if isinstance(source_code, str):
            source_code = source_code.encode("utf-8")

        if not isinstance(source_code, (bytes, bytearray)):
            raise TypeError("source_code must be bytes, bytearray, or str")

        source_code = bytes(source_code)

        self.file_path = normalize_file_path(file_path)
        self.file_name = file_name_from_path(self.file_path)
        self.file_id = make_file_id(self.file_path)
        self.content_hash = sha1(source_code).hexdigest()

        tree = self.parser.parse(source_code)

        result = make_node(
            self,
            tree.root_node,
            "file",
            source_code,
        )

        result["file_id"] = self.file_id
        result["content_hash"] = self.content_hash
        result["has_parse_errors"] = bool(tree.root_node.has_error)
        result["children"] = extract_scope(
            self,
            tree.root_node,
            source_code,
        )
        attach_parent_ids(result)

        errors = collect_parse_errors(
            self,
            tree.root_node,
            source_code,
        )
        if errors:
            result["parse_errors"] = errors
            result["parse_error_count"] = len(errors)
        else:
            result["parse_error_count"] = 0

        return result


# ============================================================================
# SCOPE EXTRACTION
# ============================================================================


def extract_scope(extractor, node, source_code):
    """
    Extract meaningful nodes from a JavaScript scope.

    A scope can be:

        - program / file
        - function body
        - arrow-function block body
        - class static block
        - if / else-if / else body
        - loop body
        - try / catch / finally body
        - switch case body
        - with body
        - labeled statement body
    """

    children = []

    for child in node.children:
        child_type = child.type

        # ------------------------------------------------------------
        # Comments
        # ------------------------------------------------------------

        if child_type == "comment":
            children.append(extract_comment(extractor, child, source_code))
            continue

        # ------------------------------------------------------------
        # Shebang / hash-bang
        # ------------------------------------------------------------

        if child_type == "hash_bang_line":
            children.append(extract_hashbang(extractor, child, source_code))
            continue

        # ------------------------------------------------------------
        # Imports
        # ------------------------------------------------------------

        if child_type == "import_statement":
            children.append(extract_import(extractor, child, source_code))
            continue

        # ------------------------------------------------------------
        # Exports
        # ------------------------------------------------------------

        if child_type == "export_statement":
            extracted = extract_export(extractor, child, source_code)
            if extracted:
                children.append(extracted)
            continue

        # ------------------------------------------------------------
        # Variables / declarations
        # ------------------------------------------------------------

        if child_type in {
            "lexical_declaration",       # const / let
            "variable_declaration",      # var
            "using_declaration",         # using / await using
        }:
            children.append(
                extract_variable_declaration(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # ------------------------------------------------------------
        # Functions
        # ------------------------------------------------------------

        if child_type in {
            "function_declaration",
            "generator_function_declaration",
            "function_expression",
            "generator_function",
            "arrow_function",
        }:
            children.append(
                extract_function(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # ------------------------------------------------------------
        # Classes
        # ------------------------------------------------------------

        if child_type in {
            "class_declaration",
            "class",
        }:
            children.append(
                extract_class(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # ------------------------------------------------------------
        # IF / ELSE-IF / ELSE
        # ------------------------------------------------------------

        if child_type == "if_statement":
            children.append(
                extract_if(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # ------------------------------------------------------------
        # FOR / FOR-IN / FOR-OF
        # ------------------------------------------------------------

        if child_type == "for_statement":
            children.append(
                extract_for(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        if child_type == "for_in_statement":
            children.append(
                extract_for_in(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # ------------------------------------------------------------
        # WHILE / DO-WHILE
        # ------------------------------------------------------------

        if child_type == "while_statement":
            children.append(
                extract_while(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        if child_type == "do_statement":
            children.append(
                extract_do_while(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # ------------------------------------------------------------
        # TRY / CATCH / FINALLY
        # ------------------------------------------------------------

        if child_type == "try_statement":
            children.append(
                extract_try(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # ------------------------------------------------------------
        # SWITCH / CASE / DEFAULT
        # ------------------------------------------------------------

        if child_type == "switch_statement":
            children.append(
                extract_switch(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # ------------------------------------------------------------
        # WITH
        # ------------------------------------------------------------

        if child_type == "with_statement":
            children.append(
                extract_with(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # ------------------------------------------------------------
        # Labeled statement
        # ------------------------------------------------------------

        if child_type == "labeled_statement":
            children.append(
                extract_labeled(
                    extractor,
                    child,
                    source_code,
                )
            )
            continue

        # ------------------------------------------------------------
        # Expression statement
        # ------------------------------------------------------------

        if child_type == "expression_statement":
            extracted = extract_expression_statement(
                extractor,
                child,
                source_code,
            )
            if extracted:
                children.append(extracted)
            continue

        # ------------------------------------------------------------
        # Small control-transfer statements
        # ------------------------------------------------------------
        # By default these are intentionally omitted to match the abstraction
        # level of PythonParser. Set emit_control_transfer_nodes=True when a
        # later CFG/control-flow pass needs them.

        if child_type in {
            "return_statement",
            "throw_statement",
            "break_statement",
            "continue_statement",
            "debugger_statement",
            "empty_statement",
        }:
            if extractor.emit_control_transfer_nodes:
                children.append(
                    extract_control_transfer(
                        extractor,
                        child,
                        source_code,
                    )
                )
            continue

        # ------------------------------------------------------------
        # Unknown wrapper / future grammar addition
        # ------------------------------------------------------------
        # Recurse only through non-statement wrappers. This keeps the parser
        # future-tolerant without accidentally turning a skipped `return foo()`
        # into a nested `call` node.

        if child_type not in {
            "program",
            "statement_block",
            "statement",
        }:
            nested = extract_scope(
                extractor,
                child,
                source_code,
            )
            if nested:
                children.extend(nested)

    return children


# ============================================================================
# IMPORTS
# ============================================================================


def extract_import(extractor, node, source_code):
    source_node = field(node, "source")
    clause = find_direct_child(node, "import_clause")

    result = make_node(
        extractor,
        node,
        "import",
        source_code,
    )

    result["source"] = text(extractor, source_node, source_code) if source_node else None

    specifiers = []
    import_kind = "side_effect"

    if clause:
        for child in clause.children:
            if child.type == "identifier":
                # Bare identifier directly in import_clause is the default
                # import: import foo from "foo".
                specifiers.append({
                    "kind": "default",
                    "local": text(extractor, child, source_code),
                })
                import_kind = "default"

            elif child.type == "namespace_import":
                local = first_named_child(child)
                specifiers.append({
                    "kind": "namespace",
                    "local": text(extractor, local, source_code) if local else text(extractor, child, source_code),
                })
                import_kind = "namespace"

            elif child.type == "named_imports":
                import_kind = "named"
                for specifier in child.children:
                    if specifier.type != "import_specifier":
                        continue

                    name_node = field(specifier, "name")
                    alias_node = field(specifier, "alias")

                    specifiers.append({
                        "kind": "named",
                        "imported": text(extractor, name_node, source_code) if name_node else None,
                        "local": text(extractor, alias_node, source_code) if alias_node else (
                            text(extractor, name_node, source_code) if name_node else None
                        ),
                    })

    if specifiers:
        result["specifiers"] = specifiers
    result["import_kind"] = import_kind

    attributes = [
        text(extractor, child, source_code)
        for child in node.children
        if child.type == "import_attribute"
    ]
    if attributes:
        result["attributes"] = attributes

    return result


# ============================================================================
# EXPORTS
# ============================================================================


def extract_export(extractor, node, source_code):
    declaration = field(node, "declaration")
    source_node = field(node, "source")
    value_node = field(node, "value")
    clause = find_direct_child(node, "export_clause")
    namespace_export = find_direct_child(node, "namespace_export")

    is_default = contains_keyword(node, "default")

    # ------------------------------------------------------------
    # export const/function/class ...
    # ------------------------------------------------------------
    # As with Python decorated definitions, avoid creating an unnecessary
    # wrapper node when the export directly decorates a meaningful declaration.

    if declaration:
        extracted = extract_semantic_declaration(
            extractor,
            declaration,
            source_code,
        )

        if extracted is None:
            return None

        extracted["exported"] = True
        extracted["default_export"] = is_default

        if source_node:
            extracted["export_source"] = text(extractor, source_node, source_code)

        decorators = extract_decorators(extractor, node, source_code)
        if decorators:
            extracted["decorators"] = decorators

        # The emitted semantic node represents the whole export statement,
        # not only the nested declaration.
        replace_span_metadata(
            extractor,
            extracted,
            node,
            source_code,
        )
        return extracted

    # ------------------------------------------------------------
    # export default expression
    # ------------------------------------------------------------

    result = make_node(
        extractor,
        node,
        "export",
        source_code,
    )
    result["default_export"] = is_default

    if source_node:
        result["source"] = text(extractor, source_node, source_code)

    if value_node:
        result["value"] = text(extractor, value_node, source_code)
        result["value_type"] = value_node.type

    if clause:
        result["specifiers"] = extract_export_specifiers(
            extractor,
            clause,
            source_code,
        )
        result["export_kind"] = "named"

    elif namespace_export:
        result["namespace"] = text(extractor, namespace_export, source_code)
        result["export_kind"] = "namespace"

    elif value_node:
        result["export_kind"] = "default_expression" if is_default else "expression"

    else:
        result["export_kind"] = "unknown"

    decorators = extract_decorators(extractor, node, source_code)
    if decorators:
        result["decorators"] = decorators

    return result


def extract_export_specifiers(extractor, node, source_code):
    specifiers = []

    for child in node.children:
        if child.type != "export_specifier":
            continue

        name_node = field(child, "name")
        alias_node = field(child, "alias")

        specifiers.append({
            "name": text(extractor, name_node, source_code) if name_node else None,
            "alias": text(extractor, alias_node, source_code) if alias_node else None,
        })

    return specifiers


# ============================================================================
# VARIABLES
# ============================================================================


def extract_variable_declaration(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "variable",
        source_code,
    )

    kind = None
    if node.type == "lexical_declaration":
        kind_node = field(node, "kind")
        kind = text(extractor, kind_node, source_code) if kind_node else None
    elif node.type == "variable_declaration":
        kind = "var"
    elif node.type == "using_declaration":
        kind = "using"

    if kind:
        result["kind"] = kind

    # `await using` is represented by an anonymous `await` token in the
    # current JavaScript grammar.
    if any(child.type == "await" for child in node.children):
        result["await"] = True

    declarations = []
    embedded_children = []

    for declarator in node.children:
        if declarator.type != "variable_declarator":
            continue

        name_node = field(declarator, "name")
        value_node = field(declarator, "value")

        item = {
            "name": text(extractor, name_node, source_code) if name_node else None,
        }

        if value_node:
            item["value"] = text(extractor, value_node, source_code)
            item["value_type"] = value_node.type

        declarations.append(item)

        # Named function/arrow/class expressions assigned to a variable are
        # important graph entities. Promote them as children instead of
        # emitting every expression node underneath the initializer.
        if value_node and value_node.type in {
            "function_expression",
            "generator_function",
            "arrow_function",
        }:
            embedded_children.append(
                extract_function(
                    extractor,
                    value_node,
                    source_code,
                    name_override=(
                        text(extractor, name_node, source_code)
                        if name_node else None
                    ),
                    origin="variable_initializer",
                )
            )

        elif value_node and value_node.type == "class":
            embedded_children.append(
                extract_class(
                    extractor,
                    value_node,
                    source_code,
                    name_override=(
                        text(extractor, name_node, source_code)
                        if name_node else None
                    ),
                    origin="variable_initializer",
                )
            )

    result["declarations"] = declarations

    if embedded_children:
        result["children"] = embedded_children

    return result


# ============================================================================
# FUNCTIONS
# ============================================================================


def extract_function(
    extractor,
    node,
    source_code,
    name_override=None,
    origin=None,
):
    result = make_node(
        extractor,
        node,
        "function",
        source_code,
    )

    name_node = field(node, "name")
    name = (
        name_override
        if name_override is not None
        else (text(extractor, name_node, source_code) if name_node else None)
    )

    if name:
        result["name"] = name

    function_kind = {
        "function_declaration": "declaration",
        "generator_function_declaration": "declaration",
        "function_expression": "expression",
        "generator_function": "expression",
        "arrow_function": "arrow",
    }.get(node.type, node.type)

    result["function_kind"] = function_kind

    if origin:
        result["origin"] = origin

    if node.type in {
        "generator_function",
        "generator_function_declaration",
    }:
        result["generator"] = True

    if re.match(r"\s*async\b", text(extractor, node, source_code)):
        result["async"] = True

    parameters = field(node, "parameters")
    if parameters:
        result["parameters"] = text(extractor, parameters, source_code)
    else:
        single_parameter = field(node, "parameter")
        if single_parameter:
            result["parameters"] = text(extractor, single_parameter, source_code)

    body = field(node, "body")
    if body and body.type == "statement_block":
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )
    elif body:
        # Arrow functions can have expression bodies. Keep that expression as
        # metadata instead of recursively exposing every tiny expression node.
        result["expression_body"] = text(extractor, body, source_code)
        result["expression_body_type"] = body.type

    decorators = extract_decorators(extractor, node, source_code)
    if decorators:
        result["decorators"] = decorators

    return result


# ============================================================================
# CLASSES
# ============================================================================


def extract_class(
    extractor,
    node,
    source_code,
    name_override=None,
    origin=None,
):
    result = make_node(
        extractor,
        node,
        "class",
        source_code,
    )

    name_node = field(node, "name")
    name = (
        name_override
        if name_override is not None
        else (text(extractor, name_node, source_code) if name_node else None)
    )

    if name:
        result["name"] = name

    if origin:
        result["origin"] = origin

    heritage = find_direct_child(node, "class_heritage")
    if heritage:
        result["extends"] = text(extractor, heritage, source_code)

    decorators = extract_decorators(extractor, node, source_code)
    if decorators:
        result["decorators"] = decorators

    body = field(node, "body")
    if body and body.type == "class_body":
        members = []

        for member in body.children:
            if member.type == "method_definition":
                members.append(
                    extract_method(
                        extractor,
                        member,
                        source_code,
                    )
                )

            elif member.type == "field_definition":
                members.append(
                    extract_field_definition(
                        extractor,
                        member,
                        source_code,
                    )
                )

            elif member.type == "class_static_block":
                members.append(
                    extract_class_static_block(
                        extractor,
                        member,
                        source_code,
                    )
                )

        if members:
            result["children"] = members

    return result


def extract_method(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "method",
        source_code,
    )

    name_node = field(node, "name")
    name = text(extractor, name_node, source_code) if name_node else None
    if name:
        result["name"] = name

    if name_node and name_node.type == "computed_property_name":
        result["computed"] = True

    if has_child_type(node, "static"):
        result["static"] = True

    if has_child_type(node, "async"):
        result["async"] = True

    if has_child_type(node, "*"):
        result["generator"] = True

    method_kind = "method"
    if name == "constructor":
        method_kind = "constructor"
    elif has_child_type(node, "get"):
        method_kind = "getter"
    elif has_child_type(node, "set"):
        method_kind = "setter"

    result["method_kind"] = method_kind

    parameters = field(node, "parameters")
    if parameters:
        result["parameters"] = text(extractor, parameters, source_code)

    decorators = extract_decorators(extractor, node, source_code)
    if decorators:
        result["decorators"] = decorators

    body = field(node, "body")
    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    return result


def extract_field_definition(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "field",
        source_code,
    )

    property_node = field(node, "property")
    value_node = field(node, "value")

    if property_node:
        result["name"] = text(extractor, property_node, source_code)
        if property_node.type == "computed_property_name":
            result["computed"] = True

    if has_child_type(node, "static"):
        result["static"] = True

    if value_node:
        result["value"] = text(extractor, value_node, source_code)
        result["value_type"] = value_node.type

    decorators = extract_decorators(extractor, node, source_code)
    if decorators:
        result["decorators"] = decorators

    return result


def extract_class_static_block(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "static_block",
        source_code,
    )

    body = field(node, "body")
    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    return result


# ============================================================================
# IF / ELIF / ELSE
# ============================================================================


def extract_if(extractor, node, source_code):
    result = extract_branch_node(
        extractor,
        node,
        source_code,
        branch_type="if",
    )
    return result


def extract_elif(extractor, node, source_code):
    return extract_branch_node(
        extractor,
        node,
        source_code,
        branch_type="elif",
    )


def extract_branch_node(extractor, node, source_code, branch_type):
    result = make_node(
        extractor,
        node,
        branch_type,
        source_code,
    )

    condition = field(node, "condition")
    if condition:
        result["condition"] = text(extractor, condition, source_code)

    consequence = field(node, "consequence")
    if consequence:
        result["children"] = extract_statement_or_block(
            extractor,
            consequence,
            source_code,
        )

    alternative = field(node, "alternative")
    if alternative:
        alt_statement = first_named_child(alternative)

        if alt_statement and alt_statement.type == "if_statement":
            result.setdefault("children", []).append(
                extract_elif(
                    extractor,
                    alt_statement,
                    source_code,
                )
            )
        else:
            result.setdefault("children", []).append(
                extract_else(
                    extractor,
                    alternative,
                    source_code,
                )
            )

    return result


def extract_else(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "else",
        source_code,
    )

    statement = first_named_child(node)
    if statement:
        result["children"] = extract_statement_or_block(
            extractor,
            statement,
            source_code,
        )

    return result


# ============================================================================
# FOR / FOR-IN / FOR-OF
# ============================================================================


def extract_for(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "for",
        source_code,
    )

    initializer = field(node, "initializer")
    increment = field(node, "increment")
    conditions = field_nodes(node, "condition")
    body = field(node, "body")

    if initializer:
        result["initializer"] = text(extractor, initializer, source_code)
        result["initializer_type"] = initializer.type

    # The grammar exposes semicolons as anonymous field children. We retain
    # only the actual condition expressions.
    actual_conditions = [
        child for child in conditions
        if child.type != ";"
    ]
    if actual_conditions:
        result["conditions"] = [
            text(extractor, child, source_code)
            for child in actual_conditions
        ]

    if increment:
        result["increment"] = text(extractor, increment, source_code)

    if body:
        result["children"] = extract_statement_or_block(
            extractor,
            body,
            source_code,
        )

    return result


def extract_for_in(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "for_in",
        source_code,
    )

    left = field(node, "left")
    right = field(node, "right")
    operator = field(node, "operator")
    body = field(node, "body")

    if left:
        result["left"] = text(extractor, left, source_code)

    if operator:
        result["operator"] = text(extractor, operator, source_code)

    if right:
        result["right"] = text(extractor, right, source_code)

    value = field(node, "value")
    if value:
        result["value"] = text(extractor, value, source_code)

    declaration_kind = next(
        (
            child.type
            for child in node.children
            if child.type in {"const", "let", "var", "using"}
        ),
        None,
    )
    if declaration_kind:
        result["kind"] = declaration_kind

    if has_child_type(node, "await"):
        result["await"] = True

    if operator:
        result["loop_kind"] = (
            "for_of" if text(extractor, operator, source_code) == "of" else "for_in"
        )

    if body:
        result["children"] = extract_statement_or_block(
            extractor,
            body,
            source_code,
        )

    return result


# ============================================================================
# WHILE / DO-WHILE
# ============================================================================


def extract_while(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "while",
        source_code,
    )

    condition = field(node, "condition")
    body = field(node, "body")

    if condition:
        result["condition"] = text(extractor, condition, source_code)

    if body:
        result["children"] = extract_statement_or_block(
            extractor,
            body,
            source_code,
        )

    return result


def extract_do_while(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "do_while",
        source_code,
    )

    condition = field(node, "condition")
    body = field(node, "body")

    if condition:
        result["condition"] = text(extractor, condition, source_code)

    if body:
        result["children"] = extract_statement_or_block(
            extractor,
            body,
            source_code,
        )

    return result


# ============================================================================
# TRY / CATCH / FINALLY
# ============================================================================


def extract_try(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "try",
        source_code,
    )

    children = []

    body = field(node, "body")
    if body:
        children.extend(
            extract_scope(
                extractor,
                body,
                source_code,
            )
        )

    handler = field(node, "handler")
    if handler:
        children.append(
            extract_catch(
                extractor,
                handler,
                source_code,
            )
        )

    finalizer = field(node, "finalizer")
    if finalizer:
        children.append(
            extract_finally(
                extractor,
                finalizer,
                source_code,
            )
        )

    if children:
        result["children"] = children

    return result


def extract_catch(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "catch",
        source_code,
    )

    parameter = field(node, "parameter")
    if parameter:
        result["parameter"] = text(extractor, parameter, source_code)

    body = field(node, "body")
    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    return result


def extract_finally(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "finally",
        source_code,
    )

    body = field(node, "body")
    if body:
        result["children"] = extract_scope(
            extractor,
            body,
            source_code,
        )

    return result


# ============================================================================
# SWITCH / CASE / DEFAULT
# ============================================================================


def extract_switch(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "switch",
        source_code,
    )

    value = field(node, "value")
    if value:
        result["value"] = text(extractor, value, source_code)

    body = field(node, "body")
    if body:
        cases = []
        for child in body.children:
            if child.type == "switch_case":
                cases.append(
                    extract_switch_case(
                        extractor,
                        child,
                        source_code,
                    )
                )
            elif child.type == "switch_default":
                cases.append(
                    extract_switch_default(
                        extractor,
                        child,
                        source_code,
                    )
                )

        if cases:
            result["children"] = cases

    return result


def extract_switch_case(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "case",
        source_code,
    )

    value = field(node, "value")
    if value:
        result["value"] = text(extractor, value, source_code)

    body_nodes = field_nodes(node, "body")
    children = []
    for statement in body_nodes:
        children.extend(
            extract_statement_or_block(
                extractor,
                statement,
                source_code,
            )
        )

    if children:
        result["children"] = children

    return result


def extract_switch_default(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "default",
        source_code,
    )

    body_nodes = field_nodes(node, "body")
    children = []
    for statement in body_nodes:
        children.extend(
            extract_statement_or_block(
                extractor,
                statement,
                source_code,
            )
        )

    if children:
        result["children"] = children

    return result


# ============================================================================
# WITH / LABELS
# ============================================================================


def extract_with(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "with",
        source_code,
    )

    object_node = field(node, "object")
    body = field(node, "body")

    if object_node:
        result["object"] = text(extractor, object_node, source_code)

    if body:
        result["children"] = extract_statement_or_block(
            extractor,
            body,
            source_code,
        )

    return result


def extract_labeled(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "label",
        source_code,
    )

    label = field(node, "label")
    body = field(node, "body")

    if label:
        result["name"] = text(extractor, label, source_code)

    if body:
        result["children"] = extract_statement_or_block(
            extractor,
            body,
            source_code,
        )

    return result


# ============================================================================
# EXPRESSIONS
# ============================================================================


def extract_expression_statement(extractor, node, source_code):
    expression = first_named_child(node)
    if expression is None:
        return None

    # ------------------------------------------------------------
    # Assignment expression -> meaningful assignment node
    # ------------------------------------------------------------

    if expression.type in {
        "assignment_expression",
        "augmented_assignment_expression",
    }:
        return extract_assignment(
            extractor,
            node,
            expression,
            source_code,
        )

    # ------------------------------------------------------------
    # Function expression / arrow expression
    # ------------------------------------------------------------

    if expression.type in {
        "function_expression",
        "generator_function",
        "arrow_function",
    }:
        return extract_function(
            extractor,
            expression,
            source_code,
            origin="expression_statement",
        )

    # ------------------------------------------------------------
    # Class expression
    # ------------------------------------------------------------

    if expression.type == "class":
        return extract_class(
            extractor,
            expression,
            source_code,
            origin="expression_statement",
        )

    # ------------------------------------------------------------
    # Generic meaningful expression
    # ------------------------------------------------------------

    result = make_node(
        extractor,
        node,
        "expression",
        source_code,
    )

    result["expression_type"] = expression.type

    expression_text = text(extractor, expression, source_code)
    result["expression"] = expression_text

    # A call is particularly useful for later call-graph analysis, so capture
    # its callee as metadata without creating separate argument/identifier
    # nodes.
    call_expression = unwrap_parenthesized(expression)
    if call_expression and call_expression.type == "call_expression":
        function_node = field(call_expression, "function")
        if function_node:
            result["callee"] = text(extractor, function_node, source_code)
        if field(call_expression, "optional_chain"):
            result["optional"] = True

    if call_expression and call_expression.type == "new_expression":
        result["operation"] = "new"
        constructor = field(call_expression, "constructor")
        if constructor:
            result["constructor"] = text(extractor, constructor, source_code)

    if call_expression and call_expression.type == "await_expression":
        result["operation"] = "await"

    if call_expression and call_expression.type in {
        "jsx_element",
        "jsx_self_closing_element",
    }:
        result["operation"] = "jsx"

    return result


def extract_assignment(extractor, statement_node, expression_node, source_code):
    result = make_node(
        extractor,
        statement_node,
        "assignment",
        source_code,
    )

    left = field(expression_node, "left")
    right = field(expression_node, "right")
    operator = field(expression_node, "operator")

    result["assignment_kind"] = (
        "augmented"
        if expression_node.type == "augmented_assignment_expression"
        else "simple"
    )

    if left:
        result["left"] = text(extractor, left, source_code)

    if operator:
        result["operator"] = text(extractor, operator, source_code)

    if right:
        result["right"] = text(extractor, right, source_code)

    return result


def extract_control_transfer(extractor, node, source_code):
    type_map = {
        "return_statement": "return",
        "throw_statement": "throw",
        "break_statement": "break",
        "continue_statement": "continue",
        "debugger_statement": "debugger",
        "empty_statement": "empty",
    }

    result = make_node(
        extractor,
        node,
        type_map.get(node.type, "control"),
        source_code,
    )

    expression = first_named_child(node)
    if expression:
        result["value"] = text(extractor, expression, source_code)
        result["value_type"] = expression.type

    label = field(node, "label")
    if label:
        result["label"] = text(extractor, label, source_code)

    return result


# ============================================================================
# HELPERS
# ============================================================================


def extract_semantic_declaration(extractor, node, source_code):
    """Extract a declaration appearing after `export`."""

    if node.type in {
        "lexical_declaration",
        "variable_declaration",
        "using_declaration",
    }:
        return extract_variable_declaration(
            extractor,
            node,
            source_code,
        )

    if node.type in {
        "function_declaration",
        "generator_function_declaration",
    }:
        return extract_function(
            extractor,
            node,
            source_code,
        )

    if node.type in {
        "class_declaration",
        "class",
    }:
        return extract_class(
            extractor,
            node,
            source_code,
        )

    return None


def extract_comment(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "comment",
        source_code,
    )

    if text(extractor, node, source_code).lstrip().startswith("//"):
        result["comment_kind"] = "line"
    else:
        result["comment_kind"] = "block"

    return result


def extract_hashbang(extractor, node, source_code):
    result = make_node(
        extractor,
        node,
        "hashbang",
        source_code,
    )
    return result


def extract_decorators(extractor, node, source_code):
    decorators = []

    for child in node.children:
        if child.type != "decorator":
            continue

        decorators.append({
            "text": text(extractor, child, source_code),
            "start_line": child.start_point[0] + 1,
            "end_line": child.end_point[0] + 1,
        })

    return decorators


def extract_statement_or_block(extractor, node, source_code):
    if node.type == "statement_block":
        return extract_scope(
            extractor,
            node,
            source_code,
        )

    extracted = extract_single_statement(
        extractor,
        node,
        source_code,
    )
    return [extracted] if extracted else []


def extract_single_statement(extractor, node, source_code):
    """Extract one meaningful statement without creating a wrapper block."""

    child_type = node.type

    if child_type == "comment":
        return extract_comment(extractor, node, source_code)

    if child_type == "import_statement":
        return extract_import(extractor, node, source_code)

    if child_type == "export_statement":
        return extract_export(extractor, node, source_code)

    if child_type in {
        "lexical_declaration",
        "variable_declaration",
        "using_declaration",
    }:
        return extract_variable_declaration(extractor, node, source_code)

    if child_type in {
        "function_declaration",
        "generator_function_declaration",
        "function_expression",
        "generator_function",
        "arrow_function",
    }:
        return extract_function(extractor, node, source_code)

    if child_type in {"class_declaration", "class"}:
        return extract_class(extractor, node, source_code)

    if child_type == "if_statement":
        return extract_if(extractor, node, source_code)

    if child_type == "for_statement":
        return extract_for(extractor, node, source_code)

    if child_type == "for_in_statement":
        return extract_for_in(extractor, node, source_code)

    if child_type == "while_statement":
        return extract_while(extractor, node, source_code)

    if child_type == "do_statement":
        return extract_do_while(extractor, node, source_code)

    if child_type == "try_statement":
        return extract_try(extractor, node, source_code)

    if child_type == "switch_statement":
        return extract_switch(extractor, node, source_code)

    if child_type == "with_statement":
        return extract_with(extractor, node, source_code)

    if child_type == "labeled_statement":
        return extract_labeled(extractor, node, source_code)

    if child_type == "expression_statement":
        return extract_expression_statement(extractor, node, source_code)

    if child_type in {
        "return_statement",
        "throw_statement",
        "break_statement",
        "continue_statement",
        "debugger_statement",
        "empty_statement",
    }:
        if extractor.emit_control_transfer_nodes:
            return extract_control_transfer(extractor, node, source_code)
        return None

    # A bare statement_block is a scope, not a semantic node itself.
    if child_type == "statement_block":
        return None

    # Future grammar fallback: search only inside the wrapper. Do not recurse
    # into ignored leaf statements from here.
    nested = extract_scope(extractor, node, source_code)
    return nested[0] if nested else None


def find_direct_child(node, child_type):
    for child in node.children:
        if child.type == child_type:
            return child
    return None


def first_named_child(node):
    for child in node.children:
        if getattr(child, "is_named", True):
            return child
    return None


def field(node, name):
    return node.child_by_field_name(name)


def field_nodes(node, name):
    """Return all children belonging to a repeated Tree-sitter field."""

    # Current py-tree-sitter exposes children_by_field_name(), which is the
    # correct API for grammar fields declared as multiple: true.
    try:
        result = node.children_by_field_name(name)
        if result:
            return result
    except AttributeError:
        pass

    # Compatibility fallback for older bindings.
    result = []
    field_name_for_child = getattr(node, "field_name_for_child", None)
    child_count = getattr(node, "child_count", 0)

    if field_name_for_child is not None:
        for index in range(child_count):
            try:
                child_field_name = node.field_name_for_child(index)
            except Exception:
                child_field_name = None
            if child_field_name == name:
                result.append(node.children[index])

    if result:
        return result

    # Last-resort single-child behavior for bindings exposing only
    # child_by_field_name().
    try:
        child = node.child_by_field_name(name)
    except Exception:
        child = None

    return [child] if child is not None else []


def contains_keyword(node, keyword):
    """Check direct anonymous/named keyword tokens without text substring traps."""

    if has_child_type(node, keyword):
        return True

    # Some versions/grammars may expose the keyword as part of an unnamed
    # terminal child whose type is still searchable from the concrete node.
    for child in node.children:
        if child.type == keyword:
            return True

    return False


def has_child_type(node, child_type):
    return any(child.type == child_type for child in node.children)


def unwrap_parenthesized(node):
    current = node
    while current and current.type == "parenthesized_expression":
        current = first_named_child(current)
    return current


def collect_parse_errors(extractor, node, source_code):
    errors = []

    if getattr(node, "is_error", False) or getattr(node, "is_missing", False):
        errors.append({
            "type": node.type,
            "missing": bool(getattr(node, "is_missing", False)),
            "start_line": node.start_point[0] + 1,
            "end_line": node.end_point[0] + 1,
            "text": text(extractor, node, source_code),
        })

    for child in node.children:
        errors.extend(
            collect_parse_errors(
                extractor,
                child,
                source_code,
            )
        )

    return errors


# ============================================================================
# NODE METADATA
# ============================================================================


def attach_parent_ids(node, parent_id=None):
    """Attach explicit parent IDs to emitted nodes for graph ingestion."""

    if not isinstance(node, dict) or "node_id" not in node:
        return

    node["parent_id"] = parent_id

    for child in node.get("children", []):
        if isinstance(child, dict) and "node_id" in child:
            attach_parent_ids(child, node["node_id"])



def make_node(extractor, node, semantic_type, source_code, **extra):
    start_row, start_column = node.start_point
    end_row, end_column = node.end_point

    result = {
        "type": semantic_type,
        "node_id": make_node_id(
            extractor.file_id,
            semantic_type,
            node.start_byte,
            node.end_byte,
        ),
        "parent_id": None,
        "language": "javascript",
        "file_id": extractor.file_id,
        "file_path": extractor.file_path,
        "file_name": extractor.file_name,
        "start_line": start_row + 1,
        "start_column": start_column + 1,
        "end_line": end_row + 1,
        "end_column": end_column + 1,
        "start_byte": node.start_byte,
        "end_byte": node.end_byte,
        "text": text(extractor, node, source_code),
    }

    result.update(extra)
    return result


def replace_span_metadata(extractor, result, node, source_code):
    """Make an extracted declaration represent the full wrapper span."""

    start_row, start_column = node.start_point
    end_row, end_column = node.end_point

    result["node_id"] = make_node_id(
        extractor.file_id,
        result["type"],
        node.start_byte,
        node.end_byte,
    )
    result["start_line"] = start_row + 1
    result["start_column"] = start_column + 1
    result["end_line"] = end_row + 1
    result["end_column"] = end_column + 1
    result["start_byte"] = node.start_byte
    result["end_byte"] = node.end_byte
    result["text"] = text(extractor, node, source_code)


def text(extractor, node, source_code):
    """
    Return the exact source text represented by a Tree-sitter node.

    The extractor argument is accepted to keep this helper consistent with
    the Python parser's calling convention.
    """

    if node is None:
        return None

    return source_code[
        node.start_byte:node.end_byte
    ].decode(
        "utf-8",
        errors="replace",
    )


def normalize_file_path(file_path):
    if file_path is None:
        return None

    value = str(file_path).strip()
    if not value:
        return None

    # Keep graph paths stable across Windows/Linux producers.
    return value.replace("\\", "/")


def file_name_from_path(file_path):
    if not file_path:
        return None
    return Path(file_path).name if "/" in file_path else file_path


def make_file_id(file_path):
    value = file_path or "<memory>"
    return sha1(value.encode("utf-8", errors="replace")).hexdigest()[:20]


def make_node_id(file_id, semantic_type, start_byte, end_byte):
    value = f"{file_id}:{semantic_type}:{start_byte}:{end_byte}"
    return sha1(value.encode("utf-8")).hexdigest()[:20]
