"""client helper for all clients."""


# ruff and mypy per file settings
#
# others
# ruff: noqa: E501, N806, PLC2701, PLR0917, RUF052, RUF105
# disable mypy errors
# mypy: disable-error-code = "operator"

# fmt: off


from typing import Any, cast

from collections import Counter

import httpx
from lxml import html
from lxml.etree import _Element

from finance_enums import exchange_records_by_market_category

from equities_classifier.enums import (
    DataSourceID,
    SecurityIdentifierType,
)
from equities_classifier.models import SecurityIdentifier
from equities_classifier.exceptions import ClientResponseError
from equities_classifier.logginghelper import logger_equities_classifier


class ClientHelper:
    """Helper methods for client processing."""

    @staticmethod
    def invalid_security_type(
        provider: DataSourceID,
        identifier: SecurityIdentifier,
        raise_object: type[ClientResponseError] | None = None,
    ) -> None:
        """Called when the provider is called with invalid security type."""

        message = f"Identifier type {identifier.type} invalid or invalid for source '{provider}' (value was '{identifier.value}')."
        logger_equities_classifier.warning(message)

        if raise_object:
            raise raise_object(message)

    @staticmethod
    def search_result_counter_issue(
        provider: DataSourceID,
        identifier: SecurityIdentifier,
        count_provider: int,
        count_found: int,
        raise_object: type[ClientResponseError] | None = None,
    ) -> None:
        """Called when the provider delivers inconsistent number of data records."""

        message = f"Search result from source '{provider}' for {identifier.type} '{identifier.value}' contains inconsistent counter value, expected {count_provider} vs {count_found} found."
        logger_equities_classifier.warning(message)

        if raise_object:
            raise raise_object(message)

    @staticmethod
    def search_result_not_unique(
        provider: DataSourceID,
        identifier: SecurityIdentifier,
        raise_object: type[ClientResponseError] | None = None,
    ) -> None:
        """Called when the provider cannot find unique dataset."""

        message = f"Search result from source '{provider}' for {identifier.type} '{identifier.value}' is not unique. Processing first match."
        logger_equities_classifier.warning(message)

        if raise_object:
            raise raise_object(message)

    @staticmethod
    def unknown_provider_attribute(
        provider: DataSourceID,
        identifier: SecurityIdentifier,
        attribute: str,
        value: str,
        context: str,
        raise_object: type[ClientResponseError] | None = None,
    ) -> None:
        """Called when the provider returns an unmapped JSON attribute."""

        message = f"Provider attribute {attribute}, value '{value}' from source '{provider}' for {identifier.type} '{identifier.value}' not mapped in '{context}'."
        logger_equities_classifier.warning(message)

        if raise_object:
            raise raise_object(message)

    @staticmethod
    def unknown_provider_attributes(
        provider: DataSourceID,
        identifier: SecurityIdentifier,
        attributes: set[tuple[str, ...]],
        context: str,
        raise_object: type[ClientResponseError] | None = None,
    ) -> None:
        """Called when the provider returns unmapped JSON attributes."""

        message = f"Provider attributes {attributes} from source '{provider}' for {identifier.type} '{identifier.value}' not mapped in '{context}'."
        logger_equities_classifier.warning(message)

        if raise_object:
            raise raise_object(message)

    @staticmethod
    def missing_provider_attribute(
        provider: DataSourceID,
        identifier: SecurityIdentifier,
        attribute: str,
        raise_object: type[ClientResponseError] | None = None,
    ) -> None:
        """Called when the provider returns an unmapped JSON attribute."""

        message = f"Missing provider attribute '{attribute}' from source '{provider}' for {identifier.type} '{identifier.value}'."
        logger_equities_classifier.warning(message)

        if raise_object:
            raise raise_object(message)

    @staticmethod
    def missing_record_attribute(
        provider: DataSourceID,
        attribute: str,
        value: Any,
        context: str,
        raise_object: type[ClientResponseError] | None = None,
    ) -> None:
        """Called when the mapping points to a record attribute that does not exist."""

        message = f"Unknown/not handled provider attribute '{attribute}' with value '{value}' in response from '{provider}', not mapped in '{context}'."
        logger_equities_classifier.warning(message)

        if raise_object:
            raise raise_object(message)

    @staticmethod
    def unknown_identifier_type(
        provider: DataSourceID,
        identifier_type: SecurityIdentifierType,
        name: str,
        raise_object: type[ClientResponseError] | None = None,
    ) -> None:
        """Called when expected identifier of  an (expected) security type is not present."""

        message = f"Unknown identifier type '{identifier_type}' for security '{name}') in data form '{provider}'."
        logger_equities_classifier.warning(message)

        if raise_object:
            raise raise_object(message)

    @staticmethod
    def inconsistent_provider_data(
        provider: DataSourceID,
        name: str,
        description: str,
        raise_object: type[ClientResponseError] | None = None,
    ) -> None:
        """Called when Provider record shows data inconsistency."""

        message = f"Provider record for '{name}' shows inconsistent data: {description}."
        logger_equities_classifier.warning(message)

        if raise_object:
            raise raise_object(message)

    @staticmethod
    def primary_ticker_not_unique(
        provider: DataSourceID,
        isin: str,
        raise_object: type[ClientResponseError] | None = None,
    ) -> None:
        """Called when Provider record does not allow reliable identification of primary ticker."""

        message = f"Provider record from '{provider}' shows more than one candidate for primary ticker for isin, '{isin}'."
        logger_equities_classifier.warning(message)

        if raise_object:
            raise raise_object(message)

    @staticmethod
    def records_cleaned(
        provider: DataSourceID,
        clean_counter: int,
        reason: str,
        raise_object: type[ClientResponseError] | None = None,
    ) -> None:
        """Called when provider records where cleaned."""

        message = f"{clean_counter} provider record from '{provider}' where cleaned/deleted: {reason}."
        logger_equities_classifier.warning(message)

        if raise_object:
            raise raise_object(message)

    @staticmethod
    def other_error_with_message(
        provider: DataSourceID,
        message: str,
        raise_object: type[ClientResponseError] | None = None,
    ) -> None:
        """Called when the provider is called with invalid security type."""

        logger_equities_classifier.error(message)

        if raise_object:
            raise raise_object(message)


# handling of multiple tickers


def _get_bloomberg_exchange_mapping() -> list[dict[str, str]]:
    """Read the Bloomberg-to-MIC equity exchange mapping."""

    _URL = "https://www.inforeachinc.com/bloomberg-exchange-code-mapping"
    _XPATH = "//div[@class='tab-content wys']//table[.//caption[normalize-space()='Equity Exchanges Mappings']]"
    _COLUMNS = (
        "bloomberg_exchange",
        "bloomberg_exchange_name",
        "bloomberg_composite",
        "mic",
        "operating_mic",
        "mic_exchange_name",
        "country",
    )

    response = httpx.get(_URL, timeout=30.0, follow_redirects=True,)
    response.raise_for_status()

    document = html.fromstring(response.content)

    table = cast(list[_Element], document.xpath(_XPATH))
    if len(table) != 1:
        message = f"Expected exactly one mapping table, found {len(table)}."
        raise RuntimeError(message)

    rows = cast(list[_Element], table[0].xpath(".//tbody/tr"))

    result: list[dict[str, str]] = []
    for row in rows:
        values = [
            " ".join(str(value) for value in td.itertext()).strip()
            for td in cast(list[_Element], row.xpath("./td"))
        ]
        if len(values) != len(_COLUMNS):
            message = f"Unexpected number of columns: expected {len(_COLUMNS)}, got {len(values)}: {values!r}"
            raise RuntimeError(message)
        result.append(dict(zip(_COLUMNS, values, strict=True)))

    return result


bloomberg_exchange_mapping = _get_bloomberg_exchange_mapping()


def _get_regulated_mics_by_country() -> dict[str, frozenset[str]]:
    """Return regulated market MICs grouped by ISO country code."""

    result: dict[str, set[str]] = {}

    for exchange in exchange_records_by_market_category("RMKT"):
        result.setdefault(exchange.iso_country_code, set()).add(exchange.operating_mic)

    return {country: frozenset(mics) for country, mics in result.items()}


_REGULATED_MICS_BY_COUNTRY: dict[str, frozenset[str]] = (
    _get_regulated_mics_by_country()
)


def get_primary_ticker(
    provider: DataSourceID,
    isin: str,
    name: str,
    ticker_for_check: str,
    list_ticker: list[str],
    list_mic_code: list[str],
    error_object: type[ClientResponseError] | None = None,
) -> str | None:

    if list_ticker and len(list_ticker) > 0 and list_mic_code and len(list_mic_code) > 0:

        if len(list_ticker) != len(list_mic_code):
            ClientHelper.inconsistent_provider_data(
                provider,
                name,
                "count of 'ticker_exchange' and 'mic_code' differ",
                error_object,
            )
            return None

        regulated_mics_for_country = _REGULATED_MICS_BY_COUNTRY.get(
            isin[:2],
            frozenset(),
        )
        tickers = [
            ticker
            for ticker, mic in zip(list_ticker, list_mic_code, strict=True, )
            if mic in regulated_mics_for_country
        ]
        counter_tickers = Counter(tickers)
        if len(counter_tickers) > 0:
            ticker_new = counter_tickers.most_common(1)[0][0]
            if ticker_for_check and ticker_for_check != ticker_new:
                ClientHelper.inconsistent_provider_data(
                    DataSourceID.OPENFIGI,
                    name,
                    f"ticker '{ticker_for_check}' currently set does not match assumed primary ticker '{ticker_new}'",
                    error_object,
                )
            if (len(counter_tickers.most_common()) > 1 and
                counter_tickers.most_common(1)[0][1] == counter_tickers.most_common(2)[1][1]):
                ClientHelper.primary_ticker_not_unique(
                    DataSourceID.OPENFIGI,
                    isin,
                    error_object,
                )

            return ticker_new

    return None
