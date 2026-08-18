"""Graphical user interface for the equities classifier."""


# ruff and mypy per file settings
#
# boolean-type arguments
# ruff: noqa: FBT001, FBT002
# others
# ruff: noqa: N813, PLR6201, RUF105
#
# fmt: off


from pathlib import Path

import FreeSimpleGUI as sg

from equities_classifier.processflow.input import read_identifiers
from equities_classifier.processflow.output import ClassificationOutput, write_excel
from equities_classifier.processflow.processflow import ProcessFlow


def run_gui() -> None:
    """Run the equities classifier GUI."""

    sg.theme("SystemDefault")

    layout = [
        [
            sg.Text(
                "Equities Classifier",
                font=("Any", 16),
            ),
        ],
        [
            sg.Text("Input-Datei:", size=(14, 1)),
            sg.Input(
                key="-INPUT-",
                expand_x=True,
            ),
            sg.FileBrowse(
                "Auswählen ...",
                target="-INPUT-",
                file_types=(
                    ("Excel-Dateien", "*.xlsx"),
                    ("Alle Dateien", "*.*"),
                ),
            ),
        ],
        [
            sg.Text("Ausgabedatei:", size=(14, 1)),
            sg.Input(
                key="-OUTPUT-",
                expand_x=True,
            ),
            sg.FileSaveAs(
                "Auswählen ...",
                target="-OUTPUT-",
                file_types=(
                    ("Excel-Dateien", "*.xlsx"),
                ),
                default_extension=".xlsx",
            ),
        ],
        [
            sg.Frame(
                "Klassifikation",
                [
                    [
                        sg.Checkbox(
                            "GECS",
                            key="-GECS-",
                        ),
                        sg.Checkbox(
                            "GICS",
                            key="-GICS-",
                        ),
                    ],
                ],
            ),
        ],
        [
            sg.Frame(
                "Zusätzliche Ausgabe",
                [
                    [
                        sg.Checkbox(
                            "Provider-Details",
                            key="-PROVIDER-",
                        ),
                    ],
                ],
            ),
        ],
        [
            sg.Push(),
            sg.Button(
                "Start",
                key="-START-",
                bind_return_key=True,
            ),
            sg.Button(
                "Abbrechen",
                key="-CANCEL-",
            ),
        ],
        [
            sg.Text(
                "",
                key="-STATUS-",
                expand_x=True,
            ),
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
        if event in (sg.WIN_CLOSED, "-CANCEL-"):
            return
        if event == "-START-":
            try:
                _run_process(window, values)
            except Exception as exc:
                sg.popup_error(
                    "Die Verarbeitung konnte nicht durchgeführt werden.",
                    str(exc),
                    title="Equities Classifier"
                )


def _run_process(
    window: sg.Window,
    values: dict[str, object],
) -> None:
    """Run the classification process."""

    input_file = _get_path(values, "-INPUT-")
    if input_file is None:
        sg.popup_error("Bitte eine Input-Datei auswählen.", title="Equities Classifier")
        return

    output_file = _get_path(values, "-OUTPUT-")
    if output_file is None:
        sg.popup_error("Bitte eine Ausgabedatei auswählen.", title="Equities Classifier")
        return

    classification_output = _get_classification_output(values)
    provider_details = bool(values.get("-PROVIDER-"))
    if (
        classification_output is ClassificationOutput.NONE
        and not provider_details
    ):
        sg.popup_error("Bitte mindestens eine Ausgabe auswählen.", title="Equities Classifier")
        return

    window["-STATUS-"].update(
        "Lese Input-Datei ..."
    )
    window.refresh()
    identifiers = read_identifiers(input_file)

    window["-STATUS-"].update(f"{len(identifiers)} Identifier gelesen. " "Starte Verarbeitung ...")
    window.refresh()
    processflow = ProcessFlow()
    securities = processflow.run(identifiers)

    window["-STATUS-"].update(f"{len(securities)} Securities erzeugt. " "Schreibe Ausgabe ...")
    window.refresh()
    write_excel(securities, output_file, classifications=classification_output, provider_details=provider_details)

    window["-STATUS-"].update(f"Fertig: {output_file}")

    sg.popup_ok(
        f"Verarbeitung abgeschlossen.\n\n"
        f"{len(securities)} Securities geschrieben.",
        title="Equities Classifier",
    )


def _get_classification_output(
    values: dict[str, object],
) -> ClassificationOutput:
    """Return selected classification output."""

    gecs = bool(values.get("-GECS-"))
    gics = bool(values.get("-GICS-"))

    if gecs and gics:
        return ClassificationOutput.BOTH
    if gecs:
        return ClassificationOutput.GECS
    if gics:
        return ClassificationOutput.GICS

    return ClassificationOutput.NONE


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
