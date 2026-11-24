# ASTRA Phase 4 — Browser, Desktop and Workspace Tools

Phase 4 expands ASTRA from a chat interface into a real, permission-bounded desktop helper.

## Current tools

- DuckDuckGo live search with source URLs.
- Google searches opened in the default browser.
- Visible Selenium browser using a separate ASTRA profile: open/read pages, follow links and fill non-password fields without submitting forms.
- Windows UI Automation through the built-in Windows automation assemblies: inspect accessible controls, invoke named buttons and fill non-password text fields.
- Desktop input: focus a named window, type text, press a limited shortcut list and click a screen coordinate.
- User-home file workspace: list and search files, read/create/append/copy text and code files, create folders, and replace exact text with a backup.

## Multi-step tasks

Use one-line task syntax:

~~~text
task: list files in Downloads || search official Python release
~~~

ASTRA accepts up to eight supported tool commands in a task, runs them in order, and stops at the first failure. Unsupported shell commands are not accepted as task steps.

## Privacy and safety boundaries

- File tools stay inside the current Windows user's home folder and block AppData, hidden folders, browser data, credential-like files, private keys and password stores.
- Creating or copying a file never overwrites an existing destination.
- Exact text replacement creates a backup file before changing the original.
- Browser automation uses %LOCALAPPDATA%\ASTRA\browser-profile; it does not import personal browser cookies or saved passwords.
- Browser field filling and Windows field filling do not submit forms.
- ASTRA does not delete files, install software, make purchases, submit forms, or run arbitrary shell commands.
- Password fields and credential stores are excluded.
- Windows UI Automation only sees controls exposed by an application's accessibility tree; custom-drawn interfaces may not expose useful controls.

## Dependencies

- PySide6 for the desktop UI.
- Selenium for visible browser automation. Selenium Manager obtains a matching driver when first used; the first browser action needs internet access.
- Windows PowerShell and UI Automation assemblies for accessible desktop controls.

Run unit tests with:

~~~powershell
python -m unittest discover -s tests -v
~~~
