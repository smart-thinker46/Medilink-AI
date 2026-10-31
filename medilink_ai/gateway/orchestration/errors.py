class GatewayOrchestrationError(Exception):
    pass


class GatewayStageBlocked(GatewayOrchestrationError):
    pass


class GatewayStageUnavailable(GatewayOrchestrationError):
    pass


class GatewayExecutionError(GatewayOrchestrationError):
    pass
