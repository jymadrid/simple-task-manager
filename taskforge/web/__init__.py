"""Web interface package.

Dashboard dependencies are optional, so import them lazily.
"""


def run_dashboard() -> None:
    """Run the default Streamlit dashboard."""
    from .dashboard import main

    main()


__all__ = ["run_dashboard"]
