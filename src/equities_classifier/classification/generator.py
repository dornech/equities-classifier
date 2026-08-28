"""Generate security classifications from provider data."""


# ruff and mypy per file settings
#

# fmt: off


from collections.abc import Callable, Mapping
from dataclasses import dataclass

from equities_classifier.enums import DataSourceID, ClassificationLevel
from equities_classifier.models import ClassificationSystem, ClassificationNode, Security, SecurityClassification
from equities_classifier.classification.systems import (
    GECS, resolve_gecs_supersector,
    GICS, resolve_gics_motleyfool, resolve_gics_seekingalpha
)


@dataclass(frozen=True, slots=True)
class ClassificationSource:
    """Definition of a provider classification source."""

    datasource: DataSourceID
    system: ClassificationSystem
    level_attributes: Mapping[ClassificationLevel, tuple[str, str | None]]

    resolver: Callable | None = None

    priority: bool = False


_SOURCE_GECS_MORNINGSTAR = ClassificationSource(
    datasource=DataSourceID.MORNINGSTAR,
    system=GECS,
    level_attributes={
        ClassificationLevel.LEVEL2: ("sector", None),
        ClassificationLevel.LEVEL3: ("industry", None)
    },
    resolver=resolve_gecs_supersector,
)


_SOURCE_GICS_MOTLEYFOOL = ClassificationSource(
    datasource=DataSourceID.MOTLEYFOOL,
    system=GICS,
    level_attributes={
        ClassificationLevel.LEVEL1: ("sector", None),
        ClassificationLevel.LEVEL3: ("industry", None)
    },
    resolver=resolve_gics_motleyfool,
)

_SOURCE_GICS_SEEKINGALPHA = ClassificationSource(
    datasource=DataSourceID.SEEKINGALPHA,
    system=GICS,
    level_attributes={
        ClassificationLevel.LEVEL1: ("sector", "sector_code"),
        ClassificationLevel.LEVEL4: ("subindustry", "subindustry_code")
    },
    resolver=resolve_gics_seekingalpha,
    priority=True
)


class ClassificationGenerator:
    """Generate classifications from Security provider attributes."""

    def __init__(
        self,
        sources: tuple[ClassificationSource, ...] = (),
    ) -> None:
        """Initialize classification generator class."""

        if len(sources) == 0:
            self._sources: tuple[ClassificationSource, ...] = (
                _SOURCE_GECS_MORNINGSTAR,
                _SOURCE_GICS_MOTLEYFOOL,
                _SOURCE_GICS_SEEKINGALPHA
            )
        else:
            self._sources = sources

    def generate(
        self,
        security: Security,
    ) -> list[SecurityClassification]:
        """Generate classifications for a security."""

        classifications: list[SecurityClassification] = []

        for source in self._sources:
            if source.datasource in security.provider_attributes:

                new_classification = self._generate_classification(security, source)
                if new_classification:

                    # check for duplicates
                    classification_exists = False
                    for existing_classification in classifications:
                        if existing_classification.system == new_classification.system:
                            classification_exists = True
                            break

                    if classification_exists:
                        if source.priority:
                            classifications.remove(existing_classification)
                            classifications.append(new_classification)
                    else:
                        classifications.append(new_classification)

        return classifications

    @staticmethod
    def _generate_classification(
        security: Security,
        source: ClassificationSource,
    ) -> SecurityClassification | None:
        """Generate one classification from a provider source."""

        provider_attributes = security.provider_attributes.get(source.datasource)
        if not provider_attributes:
            return None

        nodes: dict[ClassificationLevel, ClassificationNode] = {}

        for level, attribute in sorted(source.level_attributes.items(), key=lambda item: item[0]):
            value = provider_attributes.get(attribute[0])
            if value is None:
                continue
            value = str(value).strip()
            if not value:
                continue
            if attribute[1]:
                code = provider_attributes.get(attribute[1])
                if code is None:
                    continue
                code = str(code).strip()
                if not code:
                    continue
            else:
                code = None
            nodes[level] = ClassificationNode(value=value, code=code)

        if source.resolver is not None:
            nodes = source.resolver(nodes)

        return SecurityClassification(
            system=source.system,
            nodes={
                level: nodes[level] for level in sorted(nodes)
            },
        )
