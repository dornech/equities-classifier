"""client helper for all clients."""


from typing import Any


class ClientHelper:

    @staticmethod
    def unknown_provider_attribute(
        provider: str,
        attribute: str,
        value: Any
    ) -> None:
        """Called when the provider returns an unmapped JSON attribute."""
        pass

    @staticmethod
    def missing_record_attribute(
        provider: str,
        attribute: str,
        value: Any
    ) -> None:
        """Called when the mapping points to a record attribute that does not exist."""
        pass
