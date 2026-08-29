"""Command-line interface for equities-classifier."""


# ruff and mypy per file settings
#
# boolean-type arguments
# ruff: noqa: FBT001, FBT002
# others
# ruff: noqa: N813, PLR6201, RUF050, RUF105
#
# fmt: off


import argparse
from collections.abc import Sequence
from pathlib import Path
from equities_classifier.processflow.input import read_identifiers
from equities_classifier.processflow.output import get_classification_output, write_excel
from equities_classifier.processflow.gui import ProcessFlow, run_gui


def _create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""

    parser = argparse.ArgumentParser(
        prog="equities-classifier",
        description="Classify securities from an Excel input file.",
    )
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        help="Input Excel file.",
    )
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="Output Excel file.",
    )
    parser.add_argument(
        "--morningstar",
        action="store_true",
        help="Enable Morningstar enrichment.",
    )
    parser.add_argument(
        "--motleyfool",
        action="store_true",
        help="Enable Motley-Fool enrichment.",
    )
    parser.add_argument(
        "--seekingalpha",
        action="store_true",
        help="Enable SeekingAlpha enrichment.",
    )
    parser.add_argument(
        "--yahoo",
        action="store_true",
        help="Enable Yahoo enrichment.",
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> None:
    """Run the command-line interface."""

    parser = _create_parser()
    args = parser.parse_args(argv)

    # No input/output parameters: start GUI.
    if args.input is None and args.output is None:
        run_gui()
        return

    # Input and output must be specified together.
    if args.input is None or args.output is None:
        parser.error("input and output must be specified together")

    identifiers = read_identifiers(args.input)
    processflow = ProcessFlow(
        morningstar=args.morningstar,
        motleyfool=args.motleyfool,
        seekingalpha=args.seekingalpha,
        yahoo=args.yahoo
    )
    securities = processflow.run(identifiers)
    write_excel(
        securities,
        args.output,
        classifications=get_classification_output(
            args.morningstar,
            args.motleyfool or args.seekingalpha,
        ),
        provider_details=True,
    )


if __name__ == "__main__":

    pass
