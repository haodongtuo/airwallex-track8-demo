"""Stdlib tests for the escrow core. Run: python3 test_escrow.py"""
from decimal import Decimal as D

from escrow import Job, Seller, refund, settle, verify_delivery, demo_ledger


def test_net_payout():
    s = Seller("s1")
    job = Job("j1", s, D("100"))
    assert job.fee == D("2.00") and job.risk_hold == D("5.00")
    assert job.net_payout == D("93.00")
    assert verify_delivery(job, {"a": True, "b": True})
    assert settle(job) == D("93.00") and job.status == "PAID"


def test_fail_branch_refunds_in_full():
    s = Seller("s1")
    job = Job("j2", s, D("100"))
    assert not verify_delivery(job, {"a": True, "b": False})
    assert refund(job) == D("100") and job.status == "REFUNDED"
    assert s.failed_jobs == 1


def test_cap_moves_with_history():
    s = Seller("s1")
    assert s.per_job_cap == D("500.00")
    s.clean_jobs = 1
    assert s.per_job_cap == D("550.00")
    s.failed_jobs = 1
    assert s.per_job_cap == D("275.00")


def test_cannot_settle_unverified():
    s = Seller("s1")
    job = Job("j3", s, D("50"))
    try:
        settle(job)
    except ValueError:
        pass
    else:
        raise AssertionError("settle() should refuse an unverified job")


def test_demo_ledger():
    rows = demo_ledger()
    assert len(rows) == 3
    assert rows[0]["status"] == "PAID" and rows[1]["status"] == "REFUNDED"
    assert rows[2]["status"] == "PAID"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
    print("all escrow tests pass")
