# JavaScript Tree-sitter node type -> language-independent canonical type

JAVASCRIPT_TYPE_MAPPING = {
    # ------------------------------------------------------------------
    # GENERIC / SUPERTYPE CATEGORIES
    # ------------------------------------------------------------------

    "declaration": "declaration",
    "expression": "expression",
    "primary_expression": "expression",
    "pattern": "pattern",
    "statement": "statement",

    # ------------------------------------------------------------------
    # ROOT / STRUCTURE
    # ------------------------------------------------------------------

    "program": "file",
    "statement_block": "block",

    # ------------------------------------------------------------------
    # COMMENTS / FILE DIRECTIVES
    # ------------------------------------------------------------------

    "comment": "comment",
    "html_comment": "comment",
    "hash_bang_line": "comment",

    # ------------------------------------------------------------------
    # DECLARATIONS
    # ------------------------------------------------------------------

    "class_declaration": "class",
    "function_declaration": "function",
    "generator_function_declaration": "function",

    "lexical_declaration": "variable_declaration",
    "variable_declaration": "variable_declaration",
    "using_declaration": "variable_declaration",

    "variable_declarator": "variable",

    # ------------------------------------------------------------------
    # CLASS / OBJECT-ORIENTED
    # ------------------------------------------------------------------

    "class": "class",
    "class_body": "block",
    "class_heritage": "inheritance",
    "class_static_block": "block",

    "method_definition": "function",
    "field_definition": "property",

    "computed_property_name": "computed_property",

    "decorator": "decorator",

    # ------------------------------------------------------------------
    # FUNCTIONS
    # ------------------------------------------------------------------

    "function_expression": "function",
    "generator_function": "function",
    "arrow_function": "function",

    "formal_parameters": "parameters",
    "arguments": "arguments",

    # ------------------------------------------------------------------
    # ASSIGNMENTS
    # ------------------------------------------------------------------

    "assignment_expression": "assignment",
    "augmented_assignment_expression": "assignment",
    "assignment_pattern": "assignment",
    "object_assignment_pattern": "assignment",

    # ------------------------------------------------------------------
    # CONDITIONALS
    # ------------------------------------------------------------------

    "if_statement": "if",
    "else_clause": "else",

    # ------------------------------------------------------------------
    # LOOPS
    # ------------------------------------------------------------------

    "for_statement": "for",
    "for_in_statement": "for",
    "while_statement": "while",
    "do_statement": "do_while",

    # ------------------------------------------------------------------
    # EXCEPTION HANDLING
    # ------------------------------------------------------------------

    "try_statement": "try",
    "catch_clause": "except",
    "finally_clause": "finally",

    # ------------------------------------------------------------------
    # SWITCH / CASE
    # ------------------------------------------------------------------

    "switch_statement": "switch",
    "switch_body": "block",
    "switch_case": "case",
    "switch_default": "default",

    # ------------------------------------------------------------------
    # CONTROL FLOW
    # ------------------------------------------------------------------

    "break_statement": "break",
    "continue_statement": "continue",
    "return_statement": "return",
    "throw_statement": "raise",

    "debugger_statement": "debugger",
    "empty_statement": "pass",
    "labeled_statement": "label",

    # ------------------------------------------------------------------
    # IMPORTS
    # ------------------------------------------------------------------

    "import_statement": "import",
    "import_clause": "import_clause",
    "import_specifier": "import_item",
    "named_imports": "import_items",
    "namespace_import": "namespace_import",
    "import_attribute": "import_attribute",
    "import": "import_expression",

    # ------------------------------------------------------------------
    # EXPORTS
    # ------------------------------------------------------------------

    "export_statement": "export",
    "export_clause": "export_clause",
    "export_specifier": "export_item",
    "namespace_export": "namespace_export",

    # ------------------------------------------------------------------
    # EXPRESSIONS
    # ------------------------------------------------------------------

    "binary_expression": "binary_expression",
    "unary_expression": "unary_expression",
    "update_expression": "update_expression",
    "ternary_expression": "conditional_expression",
    "sequence_expression": "expression",

    "await_expression": "await_expression",
    "yield_expression": "yield_expression",

    "new_expression": "instantiation",
    "call_expression": "call",

    # ------------------------------------------------------------------
    # ACCESS / MEMBER EXPRESSIONS
    # ------------------------------------------------------------------

    "member_expression": "member_access",
    "subscript_expression": "index_access",
    "parenthesized_expression": "parenthesized_expression",

    "optional_chain": "optional_chain",
    "meta_property": "meta_property",

    # ------------------------------------------------------------------
    # ARRAYS / OBJECTS / COLLECTIONS
    # ------------------------------------------------------------------

    "array": "array",
    "array_pattern": "array_pattern",

    "object": "object",
    "object_pattern": "object_pattern",

    "pair": "property",
    "pair_pattern": "property",

    "spread_element": "spread",
    "rest_pattern": "spread",

    # ------------------------------------------------------------------
    # LITERALS
    # ------------------------------------------------------------------

    "number": "number_literal",
    "string": "string_literal",

    "true": "boolean_literal",
    "false": "boolean_literal",

    "null": "null_literal",
    "undefined": "undefined_literal",

    "regex": "regex_literal",

    "template_string": "template_string",
    "template_substitution": "interpolation",

    # ------------------------------------------------------------------
    # STRING / REGEX HELPERS
    # ------------------------------------------------------------------

    "string_fragment": "string_content",
    "escape_sequence": "escape_sequence",

    "regex_pattern": "regex_pattern",
    "regex_flags": "regex_flags",

    "html_character_reference": "character_reference",

    # ------------------------------------------------------------------
    # IDENTIFIERS
    # ------------------------------------------------------------------

    "identifier": "identifier",
    "property_identifier": "property_identifier",
    "private_property_identifier": "property_identifier",

    "shorthand_property_identifier": "property_identifier",
    "shorthand_property_identifier_pattern": "property_identifier",

    "statement_identifier": "label",

    # ------------------------------------------------------------------
    # SPECIAL VALUES / KEYWORDS
    # ------------------------------------------------------------------

    "this": "this",
    "super": "super",

    # ------------------------------------------------------------------
    # JSX
    # ------------------------------------------------------------------

    "jsx_element": "element",
    "jsx_self_closing_element": "element",

    "jsx_opening_element": "tag",
    "jsx_closing_element": "tag",

    "jsx_attribute": "attribute",
    "jsx_expression": "expression",
    "jsx_namespace_name": "namespace",
    "jsx_text": "text",

    # ------------------------------------------------------------------
    # GENERIC EXPRESSION / PATTERN HELPERS
    # ------------------------------------------------------------------

    "expression_statement": "expression",
    "case_clause": "case",

    # ------------------------------------------------------------------
    # ADDITIONAL STRUCTURAL TYPES
    # ------------------------------------------------------------------

    "label": "label",
    "property": "property",
    "type": "type",
}