# Define ANSI escape codes as constants
RESET = "\033[0m"
BOLD = "\033[1m"
INVISIBLE_CURSOR = "\033[?25l"
VISIBLE_CURSOR = "\033[?25h"
UNDERLINE = "\033[4m"


def get_true_fg(color: list[str], bold: bool = True) -> str:
    """Custom helper function that enables colored text in the terminal

    Args:
        bold: whether to bolden the text
        string: string to color
        r: red
        g: green
        b: blue

    Returns:
        colored string
    """
    # NOTE: Currently only supports terminals that support true color
    r = color[0]
    g = color[1]
    b = color[2]
    if bold:
        return f"{BOLD}\033[38;2;{r};{g};{b};m"
    else:
        return f"\033[38;2;{r};{g};{b};m"
