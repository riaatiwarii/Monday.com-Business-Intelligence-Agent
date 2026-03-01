from collections.abc import Iterable


class TraceLogger:
    def __init__(self) -> None:
        self._steps: list[str] = []

    def add(self, message: str) -> None:
        self._steps.append(message)

    def extend(self, messages: Iterable[str]) -> None:
        self._steps.extend(messages)

    @property
    def steps(self) -> list[str]:
        return list(self._steps)
