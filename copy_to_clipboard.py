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


def retrieve_from_clipboard() -> str:
    """Returns the current contents of the system clipboard and shows a notification."""
    try:
        content = pyperclip.paste()
        notification.notify(
            title="Clipboard Retrieved",
            message=f'Clipboard contains: "{content}"',
            app_name="Clipboard Utility",
            timeout=3,  # seconds
        )
        return content if content is not None else ""
    except Exception as e:
        notification.notify(
            title="Clipboard Error",
            message=str(e),
            app_name="Clipboard Utility",
            timeout=3,
        )
        return f"Error reading clipboard: {e}"
