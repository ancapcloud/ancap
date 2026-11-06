"""Headless Hermes with an additive, task-specific file-tool guard."""
import json
import os
import sys
from pathlib import Path
from prompt_toolkit.application.current import create_app_session
from prompt_toolkit.input import DummyInput
from prompt_toolkit.output.plain_text import PlainTextOutput
from scoped_files import FilePolicy, install_guard

sys.path.insert(0, str(Path.home() / 'AppData/Local/hermes/hermes-agent'))
if __name__ == '__main__':
    from hermes_cli.main import main
    spec = json.loads(os.environ['ANCAP_FILE_POLICY'])
    install_guard(FilePolicy(spec['cwd'], spec['sources'], spec['outputs']))
    with create_app_session(input=DummyInput(), output=PlainTextOutput(sys.stdout)):
        main()
