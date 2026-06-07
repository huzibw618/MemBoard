import csv
import time
import pytest
import logger
from quiz import QuizState


# ------------------------------------------------------------------ helpers

def make_quiz(allowed_strings, max_rounds, score, total, times, correct_times):
    return QuizState(
        state='finished',
        allowed_strings=allowed_strings,
        max_rounds=max_rounds,
        score=score,
        total=total,
        times=times,
        correct_times=correct_times,
        target_string=allowed_strings[0],
        target_note='F',
        target_octave=4,
        challenge_start=time.time(),
    )


# ------------------------------------------------------------------ log_session

def test_log_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz = make_quiz([1, 2, 3, 4, 5, 6], 5, 4, 5, [2.0] * 5, [2.0] * 4)
    logger.log_session(quiz)
    assert (tmp_path / 'log' / 'all' / 'rounds' / '5.csv').exists()


def test_log_creates_header(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz = make_quiz([1, 2, 3, 4, 5, 6], 5, 4, 5, [2.0] * 5, [2.0] * 4)
    logger.log_session(quiz)
    path = tmp_path / 'log' / 'all' / 'rounds' / '5.csv'
    with open(path) as f:
        header = next(csv.reader(f))
    assert header == ['date', 'time', 'score', 'total', 'accuracy_%', 'avg_time_s', 'memscore']


def test_log_data_row_score(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz = make_quiz([1, 2, 3, 4, 5, 6], 5, 4, 5, [2.0] * 5, [2.0] * 4)
    logger.log_session(quiz)
    path = tmp_path / 'log' / 'all' / 'rounds' / '5.csv'
    with open(path) as f:
        row = next(csv.DictReader(f))
    assert row['score'] == '4'
    assert row['total'] == '5'


def test_log_data_row_accuracy(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz = make_quiz([1, 2, 3, 4, 5, 6], 5, 4, 5, [2.0] * 5, [2.0] * 4)
    logger.log_session(quiz)
    path = tmp_path / 'log' / 'all' / 'rounds' / '5.csv'
    with open(path) as f:
        row = next(csv.DictReader(f))
    assert row['accuracy_%'] == '80.0'


def test_log_data_row_avg_time(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz = make_quiz([1, 2, 3, 4, 5, 6], 5, 5, 5, [3.0] * 5, [3.0] * 5)
    logger.log_session(quiz)
    path = tmp_path / 'log' / 'all' / 'rounds' / '5.csv'
    with open(path) as f:
        row = next(csv.DictReader(f))
    assert row['avg_time_s'] == '3.00'


def test_log_data_row_memscore(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz = make_quiz([1, 2, 3, 4, 5, 6], 5, 5, 5, [3.0] * 5, [3.0] * 5)
    logger.log_session(quiz)
    path = tmp_path / 'log' / 'all' / 'rounds' / '5.csv'
    with open(path) as f:
        row = next(csv.DictReader(f))
    assert float(row['memscore']) == quiz.memscore()


def test_log_appends_on_second_call(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz = make_quiz([1, 2, 3, 4, 5, 6], 5, 5, 5, [1.0] * 5, [1.0] * 5)
    logger.log_session(quiz)
    logger.log_session(quiz)
    path = tmp_path / 'log' / 'all' / 'rounds' / '5.csv'
    with open(path) as f:
        rows = list(csv.reader(f))
    assert len(rows) == 3  # header + 2 data rows


def test_log_no_duplicate_header_on_append(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz = make_quiz([1, 2, 3, 4, 5, 6], 5, 5, 5, [1.0] * 5, [1.0] * 5)
    logger.log_session(quiz)
    logger.log_session(quiz)
    path = tmp_path / 'log' / 'all' / 'rounds' / '5.csv'
    with open(path) as f:
        rows = list(csv.reader(f))
    # Only first row should be the header
    assert rows[0][0] == 'date'
    assert rows[1][0] != 'date'
    assert rows[2][0] != 'date'


def test_log_all_strings_uses_all_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz = make_quiz([1, 2, 3, 4, 5, 6], 5, 3, 5, [2.0] * 5, [2.0] * 3)
    logger.log_session(quiz)
    assert (tmp_path / 'log' / 'all' / 'rounds' / '5.csv').exists()


def test_log_single_string_uses_string_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz = make_quiz([2], 5, 3, 5, [2.0] * 5, [2.0] * 3)
    logger.log_session(quiz)
    assert (tmp_path / 'log' / 'B' / 'rounds' / '5.csv').exists()


def test_log_round_count_in_filename(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz = make_quiz([1, 2, 3, 4, 5, 6], 100, 80, 100, [2.0] * 100, [2.0] * 80)
    logger.log_session(quiz)
    assert (tmp_path / 'log' / 'all' / 'rounds' / '100.csv').exists()


# ------------------------------------------------------------------ get_best_scores

def test_get_best_scores_no_data_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    scores = logger.get_best_scores([1, 2, 3, 4, 5, 6], [5, 25, 50])
    assert scores == {5: None, 25: None, 50: None}


def test_get_best_scores_returns_memscore(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz = make_quiz([1, 2, 3, 4, 5, 6], 25, 25, 25, [2.0] * 25, [2.0] * 25)
    logger.log_session(quiz)
    scores = logger.get_best_scores([1, 2, 3, 4, 5, 6], [25])
    assert scores[25] == pytest.approx(quiz.memscore())


def test_get_best_scores_returns_max_of_multiple(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz_low  = make_quiz([1, 2, 3, 4, 5, 6], 25, 20, 25, [2.0] * 25, [2.0] * 20)
    quiz_high = make_quiz([1, 2, 3, 4, 5, 6], 25, 25, 25, [1.0] * 25, [1.0] * 25)
    logger.log_session(quiz_low)
    logger.log_session(quiz_high)
    scores = logger.get_best_scores([1, 2, 3, 4, 5, 6], [25])
    assert scores[25] == pytest.approx(quiz_high.memscore())


def test_get_best_scores_missing_round_option_is_none(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz = make_quiz([1, 2, 3, 4, 5, 6], 25, 25, 25, [2.0] * 25, [2.0] * 25)
    logger.log_session(quiz)
    scores = logger.get_best_scores([1, 2, 3, 4, 5, 6], [5, 25, 50])
    assert scores[5] is None
    assert scores[50] is None
    assert scores[25] is not None


def test_get_best_scores_isolated_by_string_selection(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, '_BASE_DIR', str(tmp_path))
    quiz_all = make_quiz([1, 2, 3, 4, 5, 6], 25, 25, 25, [2.0] * 25, [2.0] * 25)
    quiz_one = make_quiz([1], 25, 10, 25, [2.0] * 25, [2.0] * 10)
    logger.log_session(quiz_all)
    logger.log_session(quiz_one)
    # querying for all-strings should not include single-string session
    scores_all = logger.get_best_scores([1, 2, 3, 4, 5, 6], [25])
    scores_one = logger.get_best_scores([1], [25])
    assert scores_all[25] != scores_one[25]
