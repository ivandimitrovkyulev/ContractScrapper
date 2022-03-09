class TextFormat:
    """Class that implements different text formatting styles."""

    B = '\033[1m'  # Bold
    U = '\033[4m'  # Underline
    IT = '\x1B[3m'  # Italic
    RED = '\033[91m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'  # Every style must have an 'END' at the end


def formatted(
        text: str,
        style: str = 'U',
) -> str:
    """Re formats the Text with the specified style.
    Defaults to bold.

    :param text: text to be formatted
    :param style: the style to re-format to, eg. bold, underline, etc. All available options can be
    found in the TextFormat class using the dot operator"""

    # get a list of all available styles
    style_keys = [i for i in TextFormat.__dict__.keys() if i[0] != '_']

    # make sure selected style is available
    assert style in style_keys, "Style not available, please choose from {}".format(style_keys)

    styled_text = "{0}{1}{2}".format(TextFormat.__dict__[style], text, TextFormat.END)

    return styled_text
