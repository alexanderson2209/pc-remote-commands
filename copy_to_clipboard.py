import pyperclip
from plyer import notification


def copy_to_clipboard(text: str):
    pyperclip.copy(text)

    notification.notify(
        title="Copied to Clipboard",
        message=f'"{text}" has been copied.',
        app_name="Clipboard Utility",
        timeout=3,  # seconds
    )


copy_to_clipboard("hello world!")
