class AIError(RuntimeError):
    pass


class ProviderError(AIError):
    retryable = False


class ProviderUnavailable(ProviderError):
    pass


class ProviderTimeout(ProviderError):
    retryable = True


class ProviderRateLimited(ProviderError):
    retryable = True


class ProviderTransientError(ProviderError):
    retryable = True


class ProviderResponseError(ProviderError):
    pass


class ProviderCapabilityError(ProviderError):
    pass


class AllProvidersUnavailable(AIError):
    pass


class AIConcurrencyLimit(AIError):
    pass


class AIInputTooLarge(AIError):
    pass


class InvalidStructuredOutput(AIError):
    pass
