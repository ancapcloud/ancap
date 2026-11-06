"""Give Hermes a plain-text terminal when launched without a Windows console."""
import sys
from pathlib import Path
from prompt_toolkit.application.current import create_app_session
from prompt_toolkit.input import DummyInput
from prompt_toolkit.output.plain_text import PlainTextOutput

sys.path.insert(0, str(Path.home() / 'AppData/Local/hermes/hermes-agent'))

if __name__ == '__main__':
    from hermes_cli.main import main
    with create_app_session(input=DummyInput(), output=PlainTextOutput(sys.stdout)):
        main()
