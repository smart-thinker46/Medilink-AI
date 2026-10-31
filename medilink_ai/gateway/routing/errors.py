class ModelRoutingError(Exception):
    pass


class NoModelAvailableError(ModelRoutingError):
    pass


class ModelNotFoundError(ModelRoutingError):
    pass


class ModelCapabilityError(ModelRoutingError):
    pass


class ModelPolicyError(ModelRoutingError):
    pass
