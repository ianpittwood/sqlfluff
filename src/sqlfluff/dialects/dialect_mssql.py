"""The Microsoft SQL Server dialect.

https://docs.microsoft.com/en-us/sql/t-sql/language-reference?view=sql-server-ver15
"""

from sqlfluff.core.dialects import load_raw_dialect
from sqlfluff.core.parser import RegexParser, CodeSegment, BaseSegment, OneOf, Sequence, Ref, AnyNumberOf, \
    SymbolSegment, StringParser, NamedParser, KeywordSegment
from sqlfluff.dialects.mssql_keywords import mssql_reserved_keywords

# Initialize dialect
ansi_dialect = load_raw_dialect("ansi")
mssql_dialect = ansi_dialect.copy_as("mssql")

# Set key words
mssql_dialect.sets("unreserved_keywords").difference_update(
    [n.strip().upper() for n in mssql_reserved_keywords.split("\n")]
)
mssql_dialect.sets("reserved_keywords").update(
    [n.strip().upper() for n in mssql_reserved_keywords.split("\n")]
)

mssql_dialect.add(
    AdditionAssignmentSegment=StringParser(
        "+=", SymbolSegment, name="addition_assignment", type="binary_operator"
    ),
    SubtractionAssignmentSegment=StringParser(
        "-=", SymbolSegment, name="subtraction_assignment", type="binary_operator"
    ),
    DivisionAssignmentSegment=StringParser(
        "/=", SymbolSegment, name="division_assignment", type="binary_operator"
    ),
    MultiplicationAssignmentSegment=StringParser(
        "*=", SymbolSegment, name="multiplication_assignment", type="binary_operator"
    ),
    ModuloAssignmentSegment=StringParser(
        "%=", SymbolSegment, name="modulo_assignment", type="binary_operator"
    ),
    BitwiseAndAssignmentSegment=StringParser(
        "&=", SymbolSegment, name="binary_and_assignment", type="binary_operator"
    ),
    BitwiseOrAssignmentSegment=StringParser(
        "|=", SymbolSegment, name="binary_or_assignment", type="binary_operator"
    ),
    BitwiseXorAssignmentSegment=StringParser(
        "^=", SymbolSegment, name="binary_xor_assignment", type="binary_operator"
    ),
    ArithmeticBinaryAssignmentOperatorGrammar=OneOf(
        Ref("AdditionAssignmentSegment"),
        Ref("SubtractionAssignmentSegment"),
        Ref("DivisionAssignmentSegment"),
        Ref("MultiplicationAssignmentSegment"),
        Ref("ModuloAssignmentSegment"),
        Ref("BitwiseAndAssignmentSegment"),
        Ref("BitwiseOrAssignmentSegment"),
        Ref("BitwiseXorAssignmentSegment"),
    ),
    GoSegement=StringParser(
        "GO", KeywordSegment, name="execution_command", type="literal"
    ),
    DoubleQuotedLiteralSegment=NamedParser(
        "double_quote",
        CodeSegment,
        name="quoted_literal",
        type="literal",
        trim_chars=('"',),
    ),
    VariableNameSegment=RegexParser(
        r"[@][a-zA-Z0-9_\.]*",  # Includes "." for property and field support on variables
        CodeSegment,
        name="declared_variable",
        type="variable",
    )
)


@mssql_dialect.segment()
class DeclareStatement(BaseSegment):
    """DECLARE statement.

    mssql: https://docs.microsoft.com/en-us/sql/t-sql/language-elements/declare-local-variable-transact-sql?view=sql-server-ver15
    """

    type = "declare_statement"

    match_grammar = OneOf(
        Sequence(
            "DECLARE",
            Ref("NakedIdentifierSegment"),
            "CURSOR",
            "FOR",
            Ref("StatementSegment"),
        ),
        Sequence(
            "DECLARE",
            OneOf("CONTINUE", "EXIT", "UNDO"),
            "HANDLER",
            "FOR",
            OneOf(
                "SQLEXCEPTION",
                "SQLWARNING",
                Sequence("NOT", "FOUND"),
                Sequence(
                    "SQLSTATE",
                    Ref.keyword("VALUE", optional=True),
                    Ref("QuotedLiteralSegment"),
                ),
                OneOf(
                    Ref("QuotedLiteralSegment"),
                    Ref("NumericLiteralSegment"),
                    Ref("NakedIdentifierSegment"),
                ),
            ),
            Sequence(Ref("StatementSegment")),
        ),
        Sequence(
            "DECLARE",
            Ref("NakedIdentifierSegment"),
            "CONDITION",
            "FOR",
            OneOf(Ref("QuotedLiteralSegment"), Ref("NumericLiteralSegment")),
        ),
        Sequence(
            "DECLARE",
            Ref("VariableNameSegment"),
            Ref("DatatypeSegment"),
            Sequence(
                Ref.keyword("DEFAULT"),
                OneOf(
                    Ref("QuotedLiteralSegment"),
                    Ref("NumericLiteralSegment"),
                    Ref("FunctionSegment"),
                ),
                optional=True,
            ),
        ),
    )


@mssql_dialect.segment(replace=True)
class DropStatementSegment(BaseSegment):
    """A `DROP` statement."""

    type = "drop_statement"

    match_grammar = Sequence(
        "DROP",
        OneOf(
            "TABLE",
            "VIEW",
            "USER",
            "FUNCTION",
            "PROCEDURE",
        ),
        Ref("IfExistsGrammar", optional=True),
        Ref("TableReferenceSegment"),
    )


@mssql_dialect.segment()
class GoStatementSegment(BaseSegment):
    """A `GO` statement.

    mssql: https://docs.microsoft.com/en-us/sql/t-sql/language-elements/sql-server-utilities-statements-go?view=sql-server-ver15
    """

    type = "go_statement"

    match_grammar = Sequence(
        Ref("GoSegment"),
        Ref("NumericLiteralSegment", optional=True)
    )


@mssql_dialect.segment()
class SetAssignmentStatementSegment(BaseSegment):
    """A `SET` statement.

    mssql: https://docs.microsoft.com/en-us/sql/t-sql/language-elements/set-local-variable-transact-sql?view=sql-server-ver15
    """

    type = "set_statement"

    match_grammar = Sequence(
        "SET",
        Ref("VariableNameSegment"),
        OneOf(Ref("EqualsSegment"), Ref("ArithmeticBinaryAssignmentOperatorGrammar")),
        AnyNumberOf(
            Ref("LiteralGrammar"),
            Ref("DoubleQuotedLiteralSegment"),
            Ref("VariableNameSegment"),
            Ref("FunctionSegment"),
        ),
    )
