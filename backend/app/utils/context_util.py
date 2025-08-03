from contextvars import ContextVar

request_context: ContextVar[str] = ContextVar("request_context", default="")