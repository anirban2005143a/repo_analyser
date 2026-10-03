from abc import ABC, abstractmethod


class BaseParser(ABC):
    @abstractmethod
    def parse(self, source_code: bytes):
        """
        Public entry point for parsing source code.
        """
        raise NotImplementedError
