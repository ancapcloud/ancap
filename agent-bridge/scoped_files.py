"""Additive file-tool restrictions for the supervised Hermes process only."""
import json
import re
from pathlib import Path

class FilePolicy:
    def __init__(self, cwd, sources, outputs):
        self.cwd = Path(cwd).resolve()
        self.outputs = {self.path(p) for p in outputs}
        self.readable = self.outputs | {self.path(p) for p in sources}

    def path(self, value):
        path = (self.cwd / value).resolve()
        if not path.is_relative_to(self.cwd) or any(p.startswith('.env') or p.lower() in ('.git', 'sicret', 'credentials') for p in path.relative_to(self.cwd).parts):
            raise ValueError('Path is outside this task or is private')
        return path

    def check(self, name, args):
        if name not in ('read_file', 'write_file', 'patch', 'search_files'):
            raise ValueError('Only scoped file tools are enabled for this worker')
        if name == 'patch' and args.get('mode') == 'patch':
            paths = re.findall(r'^\*\*\* (?:Update File|Add File|Delete File|Move to): (.+)$', args.get('patch', ''), re.M)
            if not paths:
                raise ValueError('Patch must declare every target path')
        else:
            paths = [args.get('path', '.')]
        allowed = self.outputs if name in ('write_file', 'patch') else self.readable
        for value in paths:
            if self.path(value) not in allowed:
                raise ValueError('This path is not in the task allowlist')

def install_guard(policy):
    from tools.registry import registry
    original = registry.dispatch
    def guarded(name, args, **kwargs):
        try:
            policy.check(name, args)
        except (ValueError, TypeError) as exc:
            return json.dumps({'error': 'Scope policy denied this operation: ' + str(exc)})
        return original(name, args, **kwargs)
    registry.dispatch = guarded
