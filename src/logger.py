import csv
import os
import sys
from datetime import datetime
from quiz import QuizState

# Dev: logs sit next to the source files.
# Windows frozen: logs next to the exe (user-writable extracted folder).
# Linux frozen: use XDG user data dir so a system install in /opt stays read-only.
if getattr(sys, 'frozen', False):
    if sys.platform == 'win32':
        _BASE_DIR = os.path.dirname(sys.executable)
    else:
        _xdg = os.environ.get('XDG_DATA_HOME', os.path.join(os.path.expanduser('~'), '.local', 'share'))
        _BASE_DIR = os.path.join(_xdg, 'memboard')
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_FOLDER_FOR_STRING = {1: 'E', 2: 'B', 3: 'G', 4: 'D', 5: 'A', 6: 'e'}
_ALL_STRINGS = [1, 2, 3, 4, 5, 6]


def _session_folder(allowed_strings: list[int]) -> str:
    s = sorted(allowed_strings)
    if s == _ALL_STRINGS:
        return 'all'
    if len(s) == 1:
        return _FOLDER_FOR_STRING[s[0]]
    return '-'.join(str(i) for i in s)


def get_best_scores(allowed_strings: list[int], round_options: list[int]) -> dict[int, float | None]:
    """Returns {round_count: best_memscore} for each option. None if no data yet."""
    folder = os.path.join(
        _BASE_DIR, 'log', _session_folder(allowed_strings), 'rounds'
    )
    best: dict[int, float | None] = {r: None for r in round_options}
    for rounds in round_options:
        path = os.path.join(folder, f'{rounds}.csv')
        if not os.path.exists(path):
            continue
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            scores = [float(row['memscore']) for row in reader if row.get('memscore')]
        if scores:
            best[rounds] = max(scores)
    return best


def log_session(quiz: QuizState):
    folder = os.path.join(
        _BASE_DIR, 'log', _session_folder(quiz.allowed_strings), 'rounds'
    )
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f'{quiz.max_rounds}.csv')
    is_new = not os.path.exists(path)

    now = datetime.now()
    accuracy = (quiz.score / quiz.total * 100) if quiz.total > 0 else 0.0

    with open(path, 'a', newline='') as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(['date', 'time', 'score', 'total', 'accuracy_%', 'avg_time_s', 'memscore'])
        writer.writerow([
            now.strftime('%Y-%m-%d'),
            now.strftime('%H:%M:%S'),
            quiz.score,
            quiz.total,
            f'{accuracy:.1f}',
            f'{quiz.avg_time():.2f}',
            quiz.memscore(),
        ])
