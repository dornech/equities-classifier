"""Process flow for security data acquisition and enrichment."""


# ruff and mypy per file settings
#
# others
# ruff: noqa: PLR2004, RUF050, RUF105

# fmt: off


from collections.abc import Sequence

from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import (
    SecurityIdentifier,
    Security,
)
from equities_classifier.clients.morningstar.client import MorningstarClient
from equities_classifier.clients.morningstar.models import MorningstarRecord
from equities_classifier.clients.motleyfool.client import MotleyFoolClient
from equities_classifier.clients.motleyfool.models import MotleyFoolRecord
from equities_classifier.clients.openfigi.client import OpenFIGIClient
from equities_classifier.clients.openfigi.models import OpenFIGIRecord
from equities_classifier.clients.seekingalpha.client import SeekingAlphaClient
from equities_classifier.clients.seekingalpha.models import SeekingAlphaRecord
from equities_classifier.clients.yahoo.client import YahooClient
from equities_classifier.clients.yahoo.models import YahooRecord
from equities_classifier.matching.merger import SecurityMerger
from equities_classifier.classification.generator import ClassificationGenerator


class ProcessFlow:
    """Process security data from providers."""

    def __init__(
        self,
        *,
        morningstar: bool = True,
        motleyfool: bool = True,
        seekingalpha: bool = True,
        yahoo: bool = True,
    ) -> None:
        """Initialize process flow class."""

        self._use_morningstar = morningstar
        self._use_motleyfool = motleyfool
        self._use_seekingalpha = seekingalpha
        self._use_yahoo = yahoo

        self._merger = SecurityMerger()
        self._classificationgenerator = ClassificationGenerator()

    @staticmethod
    def _read_openfigi(source_identifiers: Sequence[SecurityIdentifier]) -> list[OpenFIGIRecord]:

        with OpenFIGIClient() as client:
            openfigi_records = client.read_provider_base_data(source_identifiers)
            openfigi_records = client.remove_records_without_share_class_figi_1(openfigi_records)
            openfigi_records = client.remove_records_without_share_class_figi_2(openfigi_records)
            client.check_and_set_primary_ticker(openfigi_records, True)
            client.check_and_set_us_ticker(openfigi_records, True)

        return openfigi_records

    @staticmethod
    def _read_morningstar(source_identifiers: Sequence[SecurityIdentifier]) -> list[MorningstarRecord]:

        with MorningstarClient() as client:
            morningstar_records = client.read_provider_base_data(source_identifiers)
            client.read_provider_profile_data(morningstar_records)

        return morningstar_records

    @staticmethod
    def _read_motleyfool(source_identifiers: Sequence[SecurityIdentifier]) -> list[MotleyFoolRecord]:

        with MotleyFoolClient() as client:
            motleyfool_records = client.read_provider_profile_data(source_identifiers)
            motleyfool_records = client.remove_records_without_classification(motleyfool_records)

        return motleyfool_records

    @staticmethod
    def _read_seekingalpha(source_identifiers: Sequence[SecurityIdentifier]) -> list[SeekingAlphaRecord]:

        with SeekingAlphaClient() as client:
            seekingalpha_records = client.read_provider_profile_data(source_identifiers)

        return seekingalpha_records

    @staticmethod
    def _read_yahoo(source_identifiers: Sequence[SecurityIdentifier]) -> list[YahooRecord]:

        with YahooClient() as client:
            yahoo_records = client.read_provider_profile_data(source_identifiers)

        return yahoo_records

    @staticmethod
    def _prepare_motleyfool_identifier(
        identifiers: Sequence[SecurityIdentifier],
        identifier: SecurityIdentifier,
    ) -> SecurityIdentifier:
        """Prepare ticker identifier for Motley Fool lookup."""

        if (identifier.type is not SecurityIdentifierType.TICKER or identifier.country is not None):
            return identifier

        isin = next(
            (
                item
                for item in identifiers
                if item.type is SecurityIdentifierType.ISIN
            ),
            None,
        )
        if isin is None:
            return identifier

        return SecurityIdentifier(
            type=SecurityIdentifierType.TICKER,
            value=f"{identifier.value_cleaned}.{isin.value[:2]}",
        )

    def run(self, source_identifiers: Sequence[SecurityIdentifier],) -> list[Security]:
        """Process flow core routine."""

        openfigi_records = self._read_openfigi(source_identifiers)
        securities = self._merger.create_securities(openfigi_records)

        if self._use_morningstar:
            morningstar_identifiers_isin = {
                identifier
                for security in securities
                for identifier in security.identifiers
                if identifier.type is SecurityIdentifierType.ISIN
            }
            # avoid re-duplication of tickers resulting from OpenFIGI finding non-US securities for a ticker
            morningstar_identifiers_only_ticker = {
                identifier
                for security in securities
                for identifier in security.identifiers
                if security.has_identifier(SecurityIdentifierType.TICKER) and not
                    security.has_identifier(SecurityIdentifierType.ISIN)
                if identifier.type is SecurityIdentifierType.TICKER
            }
            morningstar_identifiers: list[SecurityIdentifier] = list(
                morningstar_identifiers_isin.union(morningstar_identifiers_only_ticker)
            )
            morningstar_records = self._read_morningstar(morningstar_identifiers)

        if self._use_motleyfool:
            motleyfool_identifiers_ticker1 = {
                self._prepare_motleyfool_identifier(security.identifiers, identifier)
                for security in securities
                for identifier in security.identifiers
                if identifier.type is SecurityIdentifierType.TICKER
            }
            # avoid re-duplication of tickers
            motleyfool_identifiers_ticker2 = {
                identifier
                for security in securities
                for identifier in security.identifiers
                if (security.has_identifier(SecurityIdentifierType.TICKER_US) and not
                   security.has_identifier(SecurityIdentifierType.TICKER)) or
                   security.identifier(SecurityIdentifierType.TICKER) !=
                security.identifier(SecurityIdentifierType.TICKER_US)
                if identifier.type is SecurityIdentifierType.TICKER_US
            }
            motleyfool_identifiers: list[SecurityIdentifier] = list(
                motleyfool_identifiers_ticker1.union(motleyfool_identifiers_ticker2)
            )
            motleyfool_records = self._read_motleyfool(motleyfool_identifiers)

        if self._use_seekingalpha:
            seekingalpha_identifiers: list[SecurityIdentifier] = list({
                identifier
                for security in securities
                for identifier in security.identifiers
                if identifier.type is SecurityIdentifierType.TICKER_US
            })
            seekingalpha_records = self._read_seekingalpha(seekingalpha_identifiers)

        if self._use_yahoo:
            yahoo_records = self._read_yahoo(source_identifiers)

        for security in securities:

            if self._use_morningstar:
                security = self._merger.merge_enrich_single(security, morningstar_records)

            if self._use_motleyfool:
                security = self._merger.merge_enrich_single(security, motleyfool_records)

            if self._use_seekingalpha:
                security = self._merger.merge_enrich_single(security, seekingalpha_records)

            if self._use_yahoo:
                security = self._merger.merge_enrich_single(security, yahoo_records)

            self._classificationgenerator.generate(security)

        return securities
