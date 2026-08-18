"""Process flow for security data acquisition and enrichment."""


# ruff and mypy per file settings
#
# others
# ruff: noqa: PLR2004, RUF105

# fmt: off


from collections.abc import Sequence

from equities_classifier.enums import SecurityIdentifierType
from equities_classifier.models import (
    SecurityIdentifier,
    Security,
)
from equities_classifier.clients.morningstar.client import MorningstarClient
from equities_classifier.clients.morningstar.models import MorningstarRecord
from equities_classifier.clients.openfigi.client import OpenFIGIClient
from equities_classifier.clients.openfigi.models import OpenFIGIRecord
from equities_classifier.clients.motleyfool.client import MotleyFoolClient
from equities_classifier.clients.motleyfool.models import MotleyFoolRecord
from equities_classifier.matching.merger import (
    SecurityMerger,
    JoinType,
)
from equities_classifier.classification.generator import ClassificationGenerator


class ProcessFlow:
    """Process security data from providers."""

    def __init__(
        self,
        *,
        morningstar: bool = True,
        motleyfool: bool = False,
    ) -> None:
        """Initialize process flow class."""

        self._use_morningstar = morningstar
        self._use_motleyfool = motleyfool

        self._merger = SecurityMerger()
        self._classificationgenerator = ClassificationGenerator()

    @staticmethod
    def _read_openfigi(
        source_identifiers: Sequence[SecurityIdentifier],
    ) -> list[OpenFIGIRecord]:
        with OpenFIGIClient() as client:
            return client.read_provider_base_data(source_identifiers, )

    @staticmethod
    def _read_morningstar(
        source_identifiers: Sequence[SecurityIdentifier],
    ) -> list[MorningstarRecord]:

        with MorningstarClient() as client:
            base_data = client.read_provider_base_data(source_identifiers,)
            return client.read_provider_profile_data(base_data)

    @staticmethod
    def _read_motleyfool(
        source_identifiers: Sequence[SecurityIdentifier],
    ) -> list[MotleyFoolRecord]:

        with MotleyFoolClient() as client:
            return client.read_provider_profile_data(source_identifiers)

    def run(
        self,
        source_identifiers: Sequence[SecurityIdentifier],
    ) -> list[Security]:
        """Process flow core routine."""

        # morningstar_records = self._read_morningstar(source_identifiers,)
        # securities = self._merger.create_securities(morningstar_records)
        openfigi_records = self._read_openfigi(source_identifiers, )
        securities = self._merger.create_securities(openfigi_records)

        if self._use_morningstar:
            morningstar_identifiers_isin = [
                identifier
                for security in securities
                for identifier in security.identifiers
                if identifier.type is SecurityIdentifierType.ISIN
            ]
            morningstar_identifiers_only_ticker = [
                identifier
                for security in securities
                for identifier in security.identifiers
                if security.has_identifier(SecurityIdentifierType.TICKER) and not
                   security.has_identifier(SecurityIdentifierType.ISIN)
                if identifier.type is SecurityIdentifierType.TICKER
            ]
            morningstar_identifiers = morningstar_identifiers_isin + morningstar_identifiers_only_ticker
            morningstar_records = self._read_morningstar(morningstar_identifiers, )

        if self._use_motleyfool:
            motelyfool_identifiers = [
                identifier
                for security in securities
                for identifier in security.identifiers
                if identifier.type is SecurityIdentifierType.TICKER
            ]
            motleyfool_records = self._read_motleyfool(motelyfool_identifiers, )

        for security in securities:

            # if self._use_openfigi:
            #     openfigi_records = self._read_openfigi(security.source_identifiers)
            #     security = self._merger.merge_enrich_single(
            #         security,
            #         openfigi_records,
            #         join_type=JoinType.LEFT,
            #     )

            if self._use_morningstar:
                security = self._merger.merge_enrich_single(
                    security,
                    morningstar_records,
                    join_type=JoinType.LEFT,
                )

            if self._use_motleyfool:
                security = self._merger.merge_enrich_single(
                    security,
                    motleyfool_records,
                )

            self._classificationgenerator.generate(security, )

        return securities
