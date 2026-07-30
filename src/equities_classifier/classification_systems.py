from enums import ClassificationSystemID
from models import ClassificationSystem


GICS = ClassificationSystem(
    id=ClassificationSystemID.GICS,
    display_name="Global Industry Classification Standard",
    authorities=(
        "MSCI",
        "S&P Dow Jones Indices",
    ),
    hierarchy=(
        "Sector",
        "Industry Group",
        "Industry",
        "Sub-Industry",
    ),
    supports_codes=True,
)


GECS = ClassificationSystem(
    id=ClassificationSystemID.GECS,
    display_name="Global Equity Classification Structure",
    authorities=("Morningstar",),
    hierarchy=(
        "Super Sector",
        "Sector",
        "Industry",
    ),
    supports_codes=False,
)
