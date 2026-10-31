class AuditError(Exception):
    pass


class AuditConfigurationError(AuditError):
    pass


class AuditWriteError(AuditError):
    pass


class AuditIntegrityError(AuditError):
    pass
