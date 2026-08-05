class MiniDBError(Exception):
    """Base class for all minidb errors."""


class LexError(MiniDBError):
    pass


class ParseError(MiniDBError):
    pass


class SchemaError(MiniDBError):
    pass


class ExecutionError(MiniDBError):
    pass
