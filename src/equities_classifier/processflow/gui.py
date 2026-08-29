"""Graphical user interface for the equities classifier."""


# ruff and mypy per file settings
#
# boolean-type arguments
# ruff: noqa: FBT001, FBT002
# others
# ruff: noqa: N813, PLR6201, RUF050, RUF105
#
# fmt: off


from pathlib import Path

import FreeSimpleGUI as sg

from equities_classifier.processflow.input import read_identifiers
from equities_classifier.processflow.output import ClassificationOutput, get_classification_output, write_excel
from equities_classifier.processflow.processflow import ProcessFlow


def run_gui() -> None:
    """Run the equities classifier GUI."""

    sg.theme("SystemDefault")

    layout = [
        [
            sg.Text("Equities Classifier", font=("Any", 16)),
        ],
        [
            sg.Text("Input file:", size=(14, 1)),
            sg.Input(key="-INPUT-", expand_x=True),
            sg.FileBrowse(
                "Select ...",
                target="-INPUT-",
                file_types=(("Excel files", "*.xlsx"), ("All files", "*.*")),
            ),
        ],
        [
            sg.Text("Output file:", size=(14, 1)),
            sg.Input(key="-OUTPUT-", expand_x=True),
            sg.FileSaveAs(
                "Select ...",
                target="-OUTPUT-",
                file_types=(("Excel files", "*.xlsx")),
                default_extension=".xlsx",
            ),
        ],
        [
            sg.Frame(
                "Classification",
                [
                    [
                        sg.Checkbox("GECS", key="-GECS-"),
                        sg.Checkbox("GICS", key="-GICS-"),
                    ],
                ],
            ),
        ],
        [
            sg.Frame(
                "Additional output",
                [
                    [
                        sg.Checkbox("Detailed provider information", key="-PROVIDER-"),
                    ],
                ],
            ),
        ],
        [
            sg.Push(),
            sg.Button("Start", key="-START-", bind_return_key=True),
            sg.Button("Cancel", key="-CANCEL-"),
        ],
        [
            sg.Text("", key="-STATUS-", expand_x=True),
        ],
    ]

    window = sg.Window("Equities Classifier", layout, resizable=True, finalize=True)

    try:
        _event_loop(window)
    finally:
        window.close()


def _event_loop(
    window: sg.Window,
) -> None:
    """Process GUI events."""

    while True:
        event, values = window.read()
        if event in {sg.WIN_CLOSED, "-CANCEL-"}:
            return
        if event == "-START-":
            try:
                _run_process(window, values)
            except Exception as exc:
                sg.popup_error("Processing not successful.", str(exc), title="Equities Classifier")


def _run_process(
    window: sg.Window,
    values: dict[str, object],
) -> None:
    """Run the classification process."""

    input_file = _get_path(values, "-INPUT-")
    if input_file is None:
        sg.popup_error("No input file specified.", title="Equities Classifier")
        return

    output_file = _get_path(values, "-OUTPUT-")
    if output_file is None:
        sg.popup_error("No output file specified..", title="Equities Classifier")
        return

    classification_output = get_classification_output(bool(values.get("-GECS-")), bool(values.get("-GICS-")))
    provider_details = bool(values.get("-PROVIDER-"))
    if (classification_output is ClassificationOutput.NONE and not provider_details):
        sg.popup_error("No output specified.", title="Equities Classifier")
        return

    window["-STATUS-"].update("Specifiy and read input file ...")
    window.refresh()
    identifiers = read_identifiers(input_file)

    window["-STATUS-"].update(f"{len(identifiers)} identifiers read from input file. Processing ...")
    window.refresh()
    processflow = ProcessFlow()
    securities = processflow.run(identifiers)

    window["-STATUS-"].update(f"Data for {len(securities)} input found an processed. " "Write output file ...")
    window.refresh()
    write_excel(securities, output_file, classifications=classification_output, provider_details=provider_details)

    window["-STATUS-"].update(f"Generated output file is: {output_file}")

    sg.popup_ok(
        f"Processing finished.\n\nData for {len(securities)} written to file.",
        title="Equities Classifier",
    )


def _get_path(
    values: dict[str, object],
    key: str,
) -> Path | None:
    """Return a selected path."""

    value = values.get(key)
    if not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    return Path(value)


if __name__ == "__main__":

    pass
