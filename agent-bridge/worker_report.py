"""Read-only report of the actual worker supervisor, never legacy cron state."""
import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent

def load(name):
    try:
        return json.loads((ROOT / 'status' / (name + '.json')).read_text(encoding='utf-8-sig'))
    except (ValueError, OSError):
        return {}

def pid_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name != 'nt':
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    kernel = ctypes.windll.kernel32
    kernel.OpenProcess.restype = ctypes.c_void_p
    handle = kernel.OpenProcess(0x100000, False, pid)
    if not handle:
        return False
    try:
        return kernel.WaitForSingleObject(ctypes.c_void_p(handle), 0) == 258
    finally:
        kernel.CloseHandle(ctypes.c_void_p(handle))

def live_worker(state, current):
    try:
        stamp = datetime.fromisoformat(state['updated_at'])
        age = (current - stamp).total_seconds()
        return state.get('state') == 'running' and 0 <= age <= 45 and pid_alive(state.get('pid'))
    except (ValueError, KeyError, TypeError):
        return False

def checked_receipt(state, receipt):
    return (state.get('verified') is True and bool(state.get('cycle_id'))
            and state.get('cycle_id') == receipt.get('cycle_id')
            and state.get('agent') == receipt.get('agent')
            and receipt.get('test_passed') is True and receipt.get('exit_code') == 0)

def render_report(current=None):
    current = current or datetime.now(timezone.utc)
    try:
        stamp = current.astimezone(ZoneInfo('Europe/Berlin')).strftime('%d.%m %H:%M') + ' (Берлин)'
    except Exception:
        stamp = current.strftime('%d.%m %H:%M UTC')
    supervisor = load('supervisor')
    active = supervisor.get('enabled') is True and pid_alive(supervisor.get('pid'))
    lines = [f'ANCAP · OpenClaw + Hermes · {stamp}',
             'Планировщик: два независимых рабочих цикла.' if active else 'Проблемы: супервизор агентов остановлен.']
    if (ROOT / 'runtime/STOP').exists():
        lines.append('Проблемы: установлен STOP; новые циклы не запускаются.')
    for name, title in [('openclaw', 'OpenClaw · сайт и интерфейс'), ('hermes', 'Hermes · API, данные, mobile и инфраструктура')]:
        lines.append(title)
        state, receipt = load(name + '-process'), load(name + '-evidence')
        if active and live_worker(state, current):
            mode = 'проверка выполнения инструментов' if state.get('mode') == 'acceptance' else 'разработка'
            lines.append(f'Работает: PID {state["pid"]}, {mode}, ветка {state.get("branch", "?")}.')
            if state.get('task_id'):
                lines.append('Текущая задача: ' + state['task_id'] + f'; прошло {state.get("elapsed_seconds", 0) // 60} мин. Результат ещё не подтверждён.')
        elif active and state.get('state') == 'starting':
            lines.append('Подготовка исходников и независимая проверка перед запуском задачи.')
        elif active and state.get('state') == 'exited':
            lines.append('Между циклами; следующий запуск выполняется независимо от другого агента.')
        else:
            lines.append('Проблемы: живой рабочий процесс с актуальным heartbeat не подтверждён.')
        result_state = state
        is_current = checked_receipt(state, receipt)
        if not is_current:
            last = load(name + '-last-result')
            result_state, receipt = last.get('state', {}), last.get('receipt', {})
            if not result_state:
                acceptance = load(name + '-acceptance')
                receipt = load(name + '-evidence')
                result_state = dict(agent=name, cycle_id=acceptance.get('cycle_id'),
                                    verified=acceptance.get('verified') is True,
                                    finished_at=acceptance.get('completed_at'))
        if checked_receipt(result_state, receipt):
            if not is_current:
                lines.append('Последний подтверждённый цикл: ' + result_state.get('finished_at', '?'))
            lines.append('Проверено: ' + ('frontend racpDisplay (Vitest)' if name == 'openclaw' else 'backend ACP RPC headers (pytest, без БД)') + ' — PASS.')
            if receipt.get('executor') == 'supervisor':
                lines.append('Проверки выполнены независимым контроллером после правок агента.')
            if result_state.get('commit'):
                lines.append('Коммит этого цикла: ' + result_state['commit'][:12])
            else:
                lines.append('В этом подтверждённом цикле нового коммита нет.')
        else:
            lines.append('Нового подтверждённого результата текущего цикла пока нет.')
        if state.get('exit_code'):
            lines.append(f'Последний код выхода: {state["exit_code"]}; {state.get("reason", "ошибка")[:180]}.')
    return '\n'.join(lines)

if __name__ == '__main__':
    print(render_report())
