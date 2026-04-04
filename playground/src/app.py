"""
Point d'entree de l'interface NiceGUI CoVeX.

Execution depuis la racine du projet:
- `uv run --project playground python src/app.py`
- `--project playground` utilise l'environnement Python et les dependances du playground.
- `python src/app.py` lance ce module, qui enregistre la page Playground puis demarre NiceGUI.
"""

import os

from nicegui import ui

from playground import (
    build_analysis_profiles_page,
    build_golden_dataset_page,
    build_playground_page,
)


def create_ui() -> None:
    @ui.page("/")
    def playground_page() -> None:
        build_playground_page()

    @ui.page("/golden-dataset")
    def golden_dataset_page() -> None:
        build_golden_dataset_page()

    @ui.page("/analysis-profiles")
    def analysis_profiles_page() -> None:
        build_analysis_profiles_page()


def main() -> None:
    create_ui()
    ui.run(
        title="CoVeX Playground",
        reload=os.getenv("COVEX_PLAYGROUND_RELOAD") == "1",
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
