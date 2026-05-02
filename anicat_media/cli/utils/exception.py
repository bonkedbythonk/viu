import sys

from rich.traceback import install as rich_install


def custom_exception_hook(exc_type, exc_value, exc_traceback):
    print(f"{exc_type.__name__}: {exc_value}")


default_exception_hook = sys.excepthook


def setup_exceptions_handler(
    trace: bool | None,
    dev: bool | None,
    rich_traceback: bool | None,
    rich_traceback_theme: str,
):
    if trace or dev:
        sys.excepthook = default_exception_hook
        if rich_traceback:
            rich_install(show_locals=True, theme=rich_traceback_theme)
    else:
        sys.excepthook = custom_exception_hook
