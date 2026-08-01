"""Security identifier resolver class for OpenFIGI."""


from collections.abc import Sequence

from equities_classifier.models import (
    SecurityIdentifier,
    Security
)
from equities_classifier.resolvers.base import  SecurityIdentifierResolver
from equities_classifier.clients.openfigi import (
    OpenFIGIClient,
    OpenFIGIRecord
)


class OpenFIGIResolver(SecurityIdentifierResolver):
    """Resolve security identifiers using the OpenFIGI service."""

    def __init__(self, client: OpenFIGIClient | None = None, api_key: str | None = None) -> None:
        if client is None:
            self._api_key = api_key
            self._client_not_provided = True
        else:
            self._client_not_provided = False
        self._client = client or OpenFIGIClient(api_key=api_key)

    def name(self) -> str:
        return type(self).__name__

    def close(self) -> None:
        """Release allocated resources."""

        if self._client_not_provided:
            self._client.close()

    def resolve(
        self,
        identifiers: Sequence[SecurityIdentifier]
    ) -> list[Security]:
        """Resolve one or more securities via OpenFIGI."""

        records: list[OpenFIGIRecord] = self._client.map(
            identifiers=identifiers,
        )
        securities: list[Security] = []
        for record in records:
            security = Security(
                company_name=record.company_name,
                ticker=record.ticker,
                security_type=record.security_type,
                identifiers=tuple(record.identifiers),
                provider_attributes = record.provider_attributes()
            )
            securities.append(security)

        return securities
