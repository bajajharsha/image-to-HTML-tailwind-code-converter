import sys
import traceback

from functools import wraps

from fastapi.responses import JSONResponse


class JsonResponseError(Exception):
    def __init__(self, status_code: int, detail: str, original_exception=None):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code
        self.original_exception = original_exception

        if original_exception:
            self.traceback = ''.join(traceback.format_exception(
                type(original_exception), 
                original_exception, 
                original_exception.__traceback__
            ))
        else:
            self.traceback = traceback.format_exc()

        self.response = JSONResponse(
            status_code=status_code,
            content={
                "detail": detail,
                "error": str(original_exception) if original_exception else detail,
                "traceback": self.traceback.split("\n")
            }
        )

    def __str__(self):
        """Return a string representation of the error."""
        if self.original_exception:
            return f"{self.detail} - Original error: {str(self.original_exception)}"
        return self.detail


def error_handler(func):
    """
    Decorator to catch JsonResponseError or any other exceptions raised
    from deeper layers and return a JSONResponse with traceback details.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except JsonResponseError as json_exc:

            print(f"ERROR: {json_exc.detail}", file=sys.stderr)
            print(f"TRACEBACK: {json_exc.traceback}", file=sys.stderr)
            
            return json_exc.response
        
        except Exception as exc:
            trace = traceback.format_exc()

            print(f"UNHANDLED ERROR: {str(exc)}", file=sys.stderr)
            print(f"TRACEBACK: {trace}", file=sys.stderr)

            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal Server Error",
                    "error": str(exc),
                    "traceback": trace.split(
                        "\n"
                    ),
                },
            )

    return wrapper