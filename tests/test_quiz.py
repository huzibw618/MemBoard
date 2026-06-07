import time
import random
import pytest
from quiz import QuizState, STRING_NOTES, STABILITY, RESULT_HOLD, _new_challenge


# ------------------------------------------------------------------ helpers

def make_state(**kwargs) -> QuizState:
    defaults = dict(
        target_string=1, target_note='F', target_octave=4,
        challenge_start=time.time(), state='challenge',
        max_rounds=5, allowed_strings=[1, 2, 3, 4, 5, 6],
    )
    defaults.update(kwargs)
    return QuizState(**defaults)


def feed_stable(quiz: QuizState, note: str, octave: int):
    """Feed a note STABILITY times to trigger a result."""
    for _ in range(STABILITY):
        quiz.feed_note(note, octave)


# ------------------------------------------------------------------ _new_challenge

def test_new_challenge_returns_valid_string():
    random.seed(0)
    for _ in range(50):
        s, n, o = _new_challenge([1, 2, 3])
        assert s in [1, 2, 3]


def test_new_challenge_returns_note_on_that_string():
    random.seed(0)
    for _ in range(50):
        s, n, o = _new_challenge([1, 2, 3, 4, 5, 6])
        assert (n, o) in STRING_NOTES[s]


def test_new_challenge_avoids_repeating_last():
    random.seed(42)
    last = (1, 'F', 4)
    for _ in range(100):
        s, n, o = _new_challenge([1], last=last)
        assert (s, n, o) != last


def test_new_challenge_single_string():
    # With only one string, result must always be on that string
    random.seed(0)
    for _ in range(20):
        s, n, o = _new_challenge([3])
        assert s == 3
        assert (n, o) in STRING_NOTES[3]


# ------------------------------------------------------------------ QuizState.start

def test_start_state_is_challenge():
    q = QuizState.start(max_rounds=10, allowed_strings=[1, 2, 3, 4, 5, 6])
    assert q.state == 'challenge'


def test_start_score_is_zero():
    q = QuizState.start(max_rounds=10, allowed_strings=[1])
    assert q.score == 0
    assert q.total == 0


def test_start_target_is_valid():
    q = QuizState.start(max_rounds=10, allowed_strings=[1, 2, 3, 4, 5, 6])
    assert q.target_string in [1, 2, 3, 4, 5, 6]
    assert (q.target_note, q.target_octave) in STRING_NOTES[q.target_string]


def test_start_challenge_start_is_recent():
    before = time.time()
    q = QuizState.start(max_rounds=5, allowed_strings=[1])
    after = time.time()
    assert before <= q.challenge_start <= after


# ------------------------------------------------------------------ feed_note / stability

def test_feed_note_no_trigger_below_stability():
    q = make_state(target_note='F', target_octave=4)
    for _ in range(STABILITY - 1):
        q.feed_note('F', 4)
    assert q.state == 'challenge'


def test_feed_note_triggers_at_stability():
    q = make_state(target_note='F', target_octave=4)
    feed_stable(q, 'F', 4)
    assert q.state == 'result'


def test_feed_note_mixed_notes_do_not_trigger():
    q = make_state(target_note='F', target_octave=4)
    for i in range(STABILITY * 3):
        q.feed_note('F' if i % 2 == 0 else 'G', 4)
    assert q.state == 'challenge'


def test_feed_note_silence_resets_history():
    q = make_state(target_note='F', target_octave=4)
    for _ in range(STABILITY - 1):
        q.feed_note('F', 4)
    q.feed_note(None, None)      # silence clears history
    q.feed_note('F', 4)          # only 1 note after reset — should not trigger
    assert q.state == 'challenge'


def test_feed_note_does_not_trigger_in_result_state():
    q = make_state(target_note='F', target_octave=4)
    feed_stable(q, 'F', 4)
    assert q.state == 'result'
    q.feed_note('F', 4)          # extra note during result display
    assert q.state == 'result'   # no double-commit


# ------------------------------------------------------------------ correct / wrong scoring

def test_correct_note_increments_score():
    q = make_state(target_note='F', target_octave=4)
    feed_stable(q, 'F', 4)
    assert q.score == 1
    assert q.total == 1
    assert q.result_correct is True


def test_wrong_note_does_not_increment_score():
    q = make_state(target_note='F', target_octave=4)
    feed_stable(q, 'G', 4)
    assert q.score == 0
    assert q.total == 1
    assert q.result_correct is False


def test_wrong_note_records_played_note():
    q = make_state(target_note='F', target_octave=4)
    feed_stable(q, 'G', 5)
    assert q.result_played == 'G'
    assert q.result_played_octave == 5


def test_correct_note_appended_to_correct_times():
    q = make_state(target_note='F', target_octave=4)
    feed_stable(q, 'F', 4)
    assert len(q.correct_times) == 1


def test_wrong_note_not_appended_to_correct_times():
    q = make_state(target_note='F', target_octave=4)
    feed_stable(q, 'G', 4)
    assert len(q.correct_times) == 0


def test_result_time_is_positive():
    q = make_state(target_note='F', target_octave=4, challenge_start=time.time() - 1.5)
    feed_stable(q, 'F', 4)
    assert q.result_time >= 1.5


def test_result_until_is_after_now():
    q = make_state(target_note='F', target_octave=4)
    feed_stable(q, 'F', 4)
    assert q.result_until > time.time()


# ------------------------------------------------------------------ tick

def test_tick_does_nothing_in_challenge_state():
    q = make_state()
    q.tick(time.time())
    assert q.state == 'challenge'


def test_tick_does_nothing_before_result_until():
    q = make_state(target_note='F', target_octave=4)
    feed_stable(q, 'F', 4)
    q.tick(q.result_until - 1)   # before time is up
    assert q.state == 'result'


def test_tick_advances_to_next_challenge():
    q = make_state(target_note='F', target_octave=4, max_rounds=5)
    feed_stable(q, 'F', 4)
    q.tick(q.result_until + 0.1)
    assert q.state == 'challenge'


def test_tick_marks_finished_after_max_rounds():
    q = make_state(target_note='F', target_octave=4, max_rounds=1)
    feed_stable(q, 'F', 4)
    q.tick(q.result_until + 0.1)
    assert q.state == 'finished'


def test_tick_resets_note_history():
    q = make_state(target_note='F', target_octave=4, max_rounds=5)
    feed_stable(q, 'F', 4)
    q.tick(q.result_until + 0.1)
    assert q._note_history == []


# ------------------------------------------------------------------ elapsed

def test_elapsed_returns_correct_duration():
    start = time.time() - 3.0
    q = make_state(challenge_start=start)
    assert abs(q.elapsed(time.time()) - 3.0) < 0.05


def test_elapsed_zero_at_start():
    now = time.time()
    q = make_state(challenge_start=now)
    assert q.elapsed(now) == pytest.approx(0.0, abs=0.01)


# ------------------------------------------------------------------ avg_time

def test_avg_time_empty_returns_zero():
    q = make_state()
    assert q.avg_time() == 0.0


def test_avg_time_single_entry():
    q = make_state(times=[2.5])
    assert q.avg_time() == pytest.approx(2.5)


def test_avg_time_multiple_entries():
    q = make_state(times=[1.0, 2.0, 3.0])
    assert q.avg_time() == pytest.approx(2.0)


# ------------------------------------------------------------------ memscore

def test_memscore_no_attempts_returns_zero():
    q = make_state(score=0, total=0, correct_times=[])
    assert q.memscore() == 0.0


def test_memscore_no_correct_returns_zero():
    q = make_state(score=0, total=5, times=[2.0]*5, correct_times=[])
    assert q.memscore() == 0.0


def test_memscore_perfect_fast():
    # 100% correct, avg 1.5s (< 3s target) → speed capped at 1.0 → 100.0
    q = make_state(score=5, total=5, times=[1.5]*5, correct_times=[1.5]*5)
    assert q.memscore() == 100.0


def test_memscore_perfect_at_target_speed():
    # 100% correct, avg exactly 3s → speed = 1.0 → 100.0
    q = make_state(score=5, total=5, times=[3.0]*5, correct_times=[3.0]*5)
    assert q.memscore() == 100.0


def test_memscore_perfect_slow():
    # 100% correct, avg 6s → speed = 3/6 = 0.5 → 50.0
    q = make_state(score=5, total=5, times=[6.0]*5, correct_times=[6.0]*5)
    assert q.memscore() == 50.0


def test_memscore_partial_accuracy():
    # 50% correct, avg 3s → accuracy=0.5, speed=1.0 → 50.0
    q = make_state(score=5, total=10, times=[3.0]*10, correct_times=[3.0]*5)
    assert q.memscore() == 50.0


def test_memscore_combined():
    # 80% correct, avg 6s → accuracy=0.8, speed=0.5 → 40.0
    q = make_state(score=4, total=5, times=[6.0]*5, correct_times=[6.0]*4)
    assert q.memscore() == 40.0


def test_memscore_rounded_to_one_decimal():
    # Result must be rounded to 1 decimal place
    q = make_state(score=1, total=3, times=[3.0]*3, correct_times=[3.0]*1)
    result = q.memscore()
    assert result == round(result, 1)
