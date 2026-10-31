class OutputValidationError(Exception):
    pass


class OutputSchemaError(OutputValidationError):
    pass


class OutputBlockedError(OutputValidationError):
    pass
