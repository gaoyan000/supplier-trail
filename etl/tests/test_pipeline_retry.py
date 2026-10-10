import psycopg.errors
import pytest

from supplier_trail_etl.pipeline import retry_on_lock_conflict


class FakeConn:
    def __init__(self):
        self.rollbacks = 0

    def rollback(self):
        self.rollbacks += 1


def test_retries_deadlock_then_succeeds():
    conn, calls = FakeConn(), []

    def work():
        calls.append(1)
        if len(calls) < 3:
            raise psycopg.errors.DeadlockDetected("deadlock")
        return "ok"

    assert retry_on_lock_conflict(conn, work, attempts=3, backoff_s=0) == "ok"
    assert len(calls) == 3 and conn.rollbacks == 2


def test_gives_up_after_attempts():
    conn = FakeConn()

    def work():
        raise psycopg.errors.DeadlockDetected("deadlock")

    with pytest.raises(psycopg.errors.DeadlockDetected):
        retry_on_lock_conflict(conn, work, attempts=2, backoff_s=0)


def test_other_errors_are_not_retried():
    conn, calls = FakeConn(), []

    def work():
        calls.append(1)
        raise ValueError("bad")

    with pytest.raises(ValueError):
        retry_on_lock_conflict(conn, work, attempts=3, backoff_s=0)
    assert len(calls) == 1
