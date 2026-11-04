"""Report actual queue/worker states; idle is healthy, quarantined is role-local."""
import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parent
def load(name):
    try:return json.loads((ROOT/'status'/(name+'.json')).read_text(encoding='utf-8-sig'))
    except (ValueError,OSError):return {}

def alive(pid):
    if not isinstance(pid,int) or pid<1:return False
    if os.name!='nt':
        try:os.kill(pid,0);return True
        except OSError:return False
    kernel=ctypes.windll.kernel32;kernel.OpenProcess.restype=ctypes.c_void_p
    handle=kernel.OpenProcess(0x100000,False,pid)
    if not handle:return False
    try:return kernel.WaitForSingleObject(ctypes.c_void_p(handle),0)==258
    finally:kernel.CloseHandle(ctypes.c_void_p(handle))

def fresh(state,seconds=45):
    try:return 0<=(datetime.now(timezone.utc)-datetime.fromisoformat(state['updated_at'])).total_seconds()<=seconds
    except (KeyError,ValueError,TypeError):return False

def stamp(value=None):
    dt=datetime.fromisoformat(value) if value else datetime.now(timezone.utc)
    try:return dt.astimezone(ZoneInfo('Europe/Berlin')).strftime('%d.%m %H:%M')+' (Берлин)'
    except Exception:return dt.strftime('%d.%m %H:%M UTC')

def render_report():
    supervisor=load('supervisor')
    active=supervisor.get('enabled') is True and fresh(supervisor) and alive(supervisor.get('pid'))
    lines=['ANCAP · OpenClaw + Hermes · '+stamp(),
           'Координатор: работает; только явные ограниченные задания.' if active else 'Координатор: остановлен или heartbeat устарел.']
    if (ROOT/'runtime/STOP').exists():lines.append('Общий STOP: новые задания остановлены оператором.')
    for role,title in [('openclaw','OpenClaw · frontend'),('hermes','Hermes · backend')]:
        state=load(role+'-process');phase=state.get('state')
        lines.append(title)
        if active and phase=='running' and fresh(state) and alive(state.get('pid')):
            lines.append(f'Выполняет задание {state.get("task_id", "?")}; PID {state["pid"]}. Результат ещё не принят.')
        elif active and phase=='idle' and fresh(state):lines.append('Готов; очередь выполнена, ожидает новое разрешённое задание.')
        elif active and phase in ('starting','checking'):lines.append('Подготовка/независимая проверка задания; это ещё не завершённый результат.')
        elif phase=='blocked':lines.append('Приостановлен только этот агент: '+state.get('reason','требуется разбор'))
        elif phase=='completed':lines.append('Последнее задание завершено и проверено.')
        else:lines.append('Текущее выполнение не подтверждено.')
        last=load(role+'-last-result');result=last.get('state',{});receipt=last.get('receipt',{})
        valid=(result.get('verified') is True and result.get('exit_code')==0 and bool(result.get('cycle_id'))
               and result.get('cycle_id')==receipt.get('cycle_id') and receipt.get('test_passed') is True)
        if valid:
            lines.append('Последняя проверка: '+stamp(result['finished_at'])+' — PASS.')
            if result.get('commit'):lines.append('Локальный коммит: '+result['commit'][:12])
    return '\n'.join(lines)

if __name__=='__main__':print(render_report())
