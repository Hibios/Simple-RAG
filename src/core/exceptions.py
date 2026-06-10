class BaseAppError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message: str = message
        self.status_code: int = status_code
        super().__init__(self.message)


class RAGProcessingError(BaseAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message=f"RAG Error: {message}", status_code=502)
