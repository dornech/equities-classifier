"""Tests for classification generator."""


# ruff and mypy per file settings
#

# fmt: off


from equities_classifier.enums import DataSourceID, ClassificationLevel
from equities_classifier.models import Security
from equities_classifier.classification.systems import GECS, GICS
from equities_classifier.classification.generator import ClassificationGenerator, ClassificationSource


def test_generate_gecs() -> None:
    """Generate GECS classification from Morningstar attributes."""

    security = Security(
        name="Apple Inc.",
        ticker="AAPL",
        provider_attributes={
            DataSourceID.MORNINGSTAR: {
                "sector": "Technology",
                "industry": "Semiconductors",
            },
        },
    )

    source = ClassificationSource(
        datasource=DataSourceID.MORNINGSTAR,
        system=GECS,
        level_attributes={
            ClassificationLevel.LEVEL2: "sector",
            ClassificationLevel.LEVEL3: "industry",
        },
    )

    generator = ClassificationGenerator((source,))
    classifications = generator.generate(security)

    assert len(classifications) == 1

    classification = classifications[0]

    assert classification.system is GECS
    assert len(classification.nodes) == 2

    assert classification.nodes[ClassificationLevel.LEVEL2].value == "Technology"

    assert classification.nodes[ClassificationLevel.LEVEL3].value == "Semiconductors"


def test_generate_gecs_ad_suppersector() -> None:
    """Generate GECS classification from Morningstar attributes."""

    security = Security(
        name="Apple Inc.",
        ticker="AAPL",
        provider_attributes={
            DataSourceID.MORNINGSTAR: {
                "sector": "Technology",
                "industry": "Semiconductors",
            },
        },
    )

    generator = ClassificationGenerator()
    classifications = generator.generate(security)

    assert len(classifications) == 1

    classification = classifications[0]

    assert classification.system is GECS
    assert len(classification.nodes) == 3

    assert classification.nodes[ClassificationLevel.LEVEL2].value == "Technology"

    assert classification.nodes[ClassificationLevel.LEVEL3].value == "Semiconductors"


def test_generate_without_provider_data() -> None:
    """Return no classification when provider data is unavailable."""

    security = Security(
        name="Apple Inc.",
        ticker="AAPL",
    )

    source = ClassificationSource(
        datasource=DataSourceID.MORNINGSTAR,
        system=GECS,
        level_attributes={
            ClassificationLevel.LEVEL2: "sector",
            ClassificationLevel.LEVEL3: "industry",
        },
    )

    generator = ClassificationGenerator((source,))

    assert generator.generate(security) == []


def test_generate_with_missing_level() -> None:
    """Skip classification levels without provider data."""

    security = Security(
        name="Apple Inc.",
        ticker="AAPL",
        provider_attributes={
            DataSourceID.MORNINGSTAR: {
                "sector": "Technology",
            },
        },
    )

    source = ClassificationSource(
        datasource=DataSourceID.MORNINGSTAR,
        system=GECS,
        level_attributes={
            ClassificationLevel.LEVEL2: "sector",
            ClassificationLevel.LEVEL3: "industry",
        },
    )

    generator = ClassificationGenerator((source,))

    classifications = generator.generate(security)

    assert len(classifications) == 1
    assert len(classifications[0].nodes) == 1


def test_generate_multiple_classifications() -> None:
    """Generate classifications from multiple providers."""

    security = Security(
        name="Apple Inc.",
        ticker="AAPL",
        provider_attributes={
            DataSourceID.MORNINGSTAR: {
                "sector": "Technology",
                "industry": "Semiconductors",
            },
            DataSourceID.MOTLEYFOOL: {
                "sector": "Technology",
                "industry": "Consumer Electronics",
            },
        },
    )

    sources = (
        ClassificationSource(
            datasource=DataSourceID.MORNINGSTAR,
            system=GECS,
            level_attributes={
                ClassificationLevel.LEVEL2: "sector",
                ClassificationLevel.LEVEL3: "industry",
            },
        ),
        ClassificationSource(
            datasource=DataSourceID.MOTLEYFOOL,
            system=GICS,
            level_attributes={
                ClassificationLevel.LEVEL1: "sector",
                ClassificationLevel.LEVEL3: "industry",
            },
        ),
    )

    generator = ClassificationGenerator(sources)

    classifications = generator.generate(security)

    assert len(classifications) == 2
