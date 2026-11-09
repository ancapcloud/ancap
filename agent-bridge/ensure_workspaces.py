"""Restore missing isolated worktrees without touching the user's main checkout."""
from datetime import datetime
from pathlib import Path
import shutil
import subprocess


def restore(repo, target, branch, backup):
    if target.exists():
        actual=subprocess.check_output(['git','-C',str(target),'rev-parse','--show-toplevel'],text=True).strip()
        current=subprocess.check_output(['git','-C',str(target),'branch','--show-current'],text=True).strip()
        if Path(actual).resolve()!=target.resolve() or current!=branch:
            raise RuntimeError('Existing workspace has a different root/branch; preserve it for review')
        return False
    subprocess.run(['git','-C',str(repo),'show-ref','--verify','refs/heads/'+branch],check=True,capture_output=True)
    metadata=subprocess.check_output(['git','-C',str(repo),'rev-parse','--path-format=absolute','--git-common-dir'],text=True).strip()
    records=Path(metadata)/'worktrees'
    if records.exists():
        backup.mkdir(parents=True,exist_ok=True)
        for record in records.iterdir():
            link=record/'gitdir'
            if link.is_file() and Path(link.read_text().strip()).parent.resolve()==target.resolve():
                shutil.copytree(record,backup/record.name,dirs_exist_ok=True)
    target.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['git','-C',str(repo),'worktree','add','--force',str(target),branch],check=True)
    return True


def main():
    root=Path(__file__).resolve().parent
    subprocess.run(['git','-C',str(root.parent),'config','extensions.worktreeConfig','true'],check=True)
    for role in ('openclaw','hermes'):
        target=Path.home()/'Desktop/ANCAP-agents'/('wt-'+role)
        backup=root/'runtime'/('workspace-restore-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
        restore(root.parent,target,'codex/'+role+'-parallel',backup)
        bridge=target/'agent-bridge'
        if not bridge.exists():
            quote=lambda p:"'"+str(p).replace("'","''")+"'"
            subprocess.run(['powershell.exe','-NoProfile','-Command',
                'New-Item -ItemType Junction -Path '+quote(bridge)+' -Target '+quote(root)+' -ErrorAction Stop | Out-Null'],check=True)
        # Junction contents are shared control state, not development output.
        # Exclude only in each isolated worktree, never in the user's main index.
        exclude=root/'runtime'/('git-exclude-'+role)
        previous=subprocess.run(['git','-C',str(target),'config','--get','core.excludesFile'],capture_output=True,text=True)
        content=exclude.read_text(encoding='utf-8') if exclude.exists() else ''
        if previous.returncode==0 and Path(previous.stdout.strip()).is_file() and Path(previous.stdout.strip()).resolve()!=exclude.resolve():
            content+=Path(previous.stdout.strip()).read_text(encoding='utf-8')
        if '/agent-bridge/' not in content.splitlines():content+='\n/agent-bridge/\n'
        exclude.write_text(content,encoding='utf-8')
        subprocess.run(['git','-C',str(target),'config','--worktree','core.excludesFile',str(exclude)],check=True)
    front=Path.home()/'Desktop/ANCAP-agents/wt-openclaw/frontend-app'
    if not (front/'node_modules/typescript/bin/tsc').is_file():
        npm=shutil.which('npm.cmd')
        if not npm:raise RuntimeError('npm.cmd is missing')
        subprocess.run([npm,'ci','--no-audit','--no-fund'],cwd=front,check=True)


if __name__=='__main__':main()
