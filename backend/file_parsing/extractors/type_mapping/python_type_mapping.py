# Python Tree-sitter node type -> language-independent canonical type.
#
# The canonical types are intentionally semantic rather than syntax/grammar
# specific so the same conventions can be reused across languages.

PYTHON_TYPE_MAPPING = {
    # ------------------------------------------------------------------
    # ROOT / GENERIC AST CATEGORIES
    # ------------------------------------------------------------------

    "module": "file",

    "_compound_statement": "statement",
    "_simple_statement": "statement",

    "expression": "expression",
    "primary_expression": "expression",
    "pattern": "pattern",
    "case_pattern": "pattern",
    "parameter": "parameter",
    "type": "type",

    "block": "block",

    # ------------------------------------------------------------------
    # COMMENTS
    # ------------------------------------------------------------------

    "comment": "comment",

    # ------------------------------------------------------------------
    # DECLARATIONS / DEFINITIONS
    # ------------------------------------------------------------------

    "class_definition": "class",
    "decorated_definition": "definition",

    "function_definition": "function",
    "async_function_definition": "function",

    "type_alias_statement": "type_alias",

    "type_parameter": "type_parameter",

    # ------------------------------------------------------------------
    # IMPORTS
    # ------------------------------------------------------------------

    "import_statement": "import",
    "import_from_statement": "import",
    "future_import_statement": "import",

    "aliased_import": "import_item",
    "wildcard_import": "import_item",
    "relative_import": "relative_import",
    "import_prefix": "import_prefix",
    "dotted_name": "qualified_name",

    # ------------------------------------------------------------------
    # ASSIGNMENTS / VARIABLES
    # ------------------------------------------------------------------

    "assignment": "assignment",
    "augmented_assignment": "assignment",
    "named_expression": "assignment",
    "annotated_assignment": "assignment",

    "default_parameter": "parameter",
    "typed_parameter": "parameter",
    "typed_default_parameter": "parameter",
    "identifier": "identifier",

    # Parameter-specific syntax
    "positional_separator": "parameter_separator",
    "keyword_separator": "parameter_separator",
    "list_splat_pattern": "variadic_parameter",
    "dictionary_splat_pattern": "variadic_parameter",

    # ------------------------------------------------------------------
    # CONDITIONALS
    # ------------------------------------------------------------------

    "if_statement": "if",
    "if_clause": "condition",
    "elif_clause": "elif",
    "else_clause": "else",

    # ------------------------------------------------------------------
    # LOOPS
    # ------------------------------------------------------------------

    "for_statement": "for",
    "async_for_statement": "for",

    "for_in_clause": "for_clause",

    "while_statement": "while",

    # ------------------------------------------------------------------
    # EXCEPTION HANDLING
    # ------------------------------------------------------------------

    "try_statement": "try",
    "except_clause": "except",
    "except_group_clause": "except",
    "finally_clause": "finally",

    # ------------------------------------------------------------------
    # CONTEXT MANAGEMENT
    # ------------------------------------------------------------------

    "with_statement": "with",
    "async_with_statement": "with",
    "with_clause": "with_clause",
    "with_item": "with_item",

    # ------------------------------------------------------------------
    # MATCH / CASE
    # ------------------------------------------------------------------

    "match_statement": "match",
    "case_clause": "case",

    # Match patterns
    "as_pattern": "pattern",
    "as_pattern_target": "pattern",

    "class_pattern": "pattern",
    "complex_pattern": "pattern",
    "dict_pattern": "pattern",
    "keyword_pattern": "pattern",
    "list_pattern": "pattern",
    "splat_pattern": "pattern",
    "tuple_pattern": "pattern",
    "union_pattern": "pattern",

    # ------------------------------------------------------------------
    # CONTROL FLOW STATEMENTS
    # ------------------------------------------------------------------

    "break_statement": "break",
    "continue_statement": "continue",
    "pass_statement": "pass",

    "return_statement": "return",
    "yield": "yield",

    "raise_statement": "raise",
    "assert_statement": "assert",

    "delete_statement": "delete",
    "global_statement": "global",
    "nonlocal_statement": "nonlocal",

    # Python 2 grammar compatibility nodes
    "exec_statement": "exec",
    "print_statement": "print",

    # ------------------------------------------------------------------
    # FUNCTION / CALL SYNTAX
    # ------------------------------------------------------------------

    "call": "call",
    "argument_list": "arguments",
    "keyword_argument": "argument",

    "lambda": "lambda",
    "lambda_parameters": "parameters",

    "parameters": "parameters",

    # ------------------------------------------------------------------
    # EXPRESSIONS / OPERATORS
    # ------------------------------------------------------------------

    "binary_operator": "binary_expression",
    "boolean_operator": "logical_expression",
    "comparison_operator": "comparison_expression",
    "unary_operator": "unary_expression",
    "conditional_expression": "conditional_expression",
    "not_operator": "logical_expression",

    "await": "await_expression",

    # ------------------------------------------------------------------
    # MEMBER / INDEX / ACCESS EXPRESSIONS
    # ------------------------------------------------------------------

    "attribute": "member_access",
    "subscript": "index_access",
    "slice": "slice",
    "parenthesized_expression": "parenthesized_expression",

    # ------------------------------------------------------------------
    # COLLECTIONS
    # ------------------------------------------------------------------

    "list": "array",
    "list_comprehension": "array_comprehension",

    "tuple": "tuple",
    "tuple_expression": "tuple",

    "dictionary": "object",
    "dictionary_comprehension": "object_comprehension",

    "set": "set",
    "set_comprehension": "set_comprehension",

    "generator_expression": "generator_expression",

    # Spread / unpacking
    "list_splat": "spread",
    "dictionary_splat": "spread",
    "parenthesized_list_splat": "spread",

    # ------------------------------------------------------------------
    # LITERALS
    # ------------------------------------------------------------------

    "integer": "integer_literal",
    "float": "float_literal",

    "string": "string_literal",
    "concatenated_string": "string_literal",
    "string_content": "string_content",
    "string_start": "string_delimiter",
    "string_end": "string_delimiter",

    "true": "boolean_literal",
    "false": "boolean_literal",

    "none": "null_literal",
    "ellipsis": "ellipsis_literal",

    # ------------------------------------------------------------------
    # F-STRINGS / STRING INTERPOLATION
    # ------------------------------------------------------------------

    "interpolation": "interpolation",
    "format_specifier": "format_specifier",
    "format_expression": "format_expression",
    "type_conversion": "type_conversion",
    "chevron": "redirect",

    # ------------------------------------------------------------------
    # EXPRESSION / VALUE WRAPPERS
    # ------------------------------------------------------------------

    "expression_statement": "expression",
    "expression_list": "expression_list",
    "pattern_list": "pattern_list",

    # ------------------------------------------------------------------
    # COMPREHENSION HELPERS
    # ------------------------------------------------------------------

    "if_clause": "condition",
    "for_in_clause": "for_clause",

    # ------------------------------------------------------------------
    # TYPE ANNOTATIONS / TYPE EXPRESSIONS
    # ------------------------------------------------------------------

    "constrained_type": "type",
    "generic_type": "generic_type",
    "member_type": "member_type",
    "splat_type": "variadic_type",
    "union_type": "union_type",

    # ------------------------------------------------------------------
    # DECORATORS
    # ------------------------------------------------------------------

    "decorator": "decorator",

    # ------------------------------------------------------------------
    # PATTERN / IDENTIFIER HELPERS
    # ------------------------------------------------------------------

    "attribute": "member_access",
    "identifier": "identifier",
    "dotted_name": "qualified_name",

    # ------------------------------------------------------------------
    # AST STRUCTURAL HELPERS
    # ------------------------------------------------------------------

    "case_pattern": "pattern",
    "block": "block",
}