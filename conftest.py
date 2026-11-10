"""Repository-wide pytest configuration.

Windows portability
-------------------
The external intake runner, the Obuchowski VALIDATION_RUNNER and the prospective
M=2000 runner are POSIX-only by design: they use ``fcntl`` file locks, ``resource``
limits, ``O_NOFOLLOW`` symlink defences and Unix ``0600`` key permissions. Those
modules are hash-locked in the release manifests, so they are not patched here.

On Windows (``sys.platform == "win32"``) this file:

* does not collect the two test modules whose runners import ``resource`` at import time;
* converts a test failure into a SKIP **only** when its root cause is one of these
  missing POSIX features:
    - ``ModuleNotFoundError`` for ``fcntl`` or ``resource``
    - ``OSError`` WinError 1314 (no privilege to create symlinks)
    - the Unix ``0o600`` key-permission assertion in the QC packet test.

Any other failure is still reported as a failure. On macOS/Linux this file does
nothing. To run the complete suite on a Windows machine, use WSL or a Linux/macOS host.
"""

import sys

import pytest

IS_WINDOWS = sys.platform == "win32"

collect_ignore = []
if IS_WINDOWS:
    collect_ignore += [
        "vv_audit/inconclusive_resolution/test_prospective_m2000_runner.py",
        "vv_audit/obuchowski_validation/test_operational_hardening_suite.py",
    ]

_POSIX_ONLY_MODULES = {"fcntl", "resource"}
_WIN_SYMLINK_PRIVILEGE_ERROR = 1314
_UNIX_PERMISSION_TESTS = {
    "qc_workflow/test_qc_workflow.py::test_qc_packet_zero_leakage_and_opaque_paths",
}


def _posix_only_reason(item, excinfo):
    exc = excinfo.value
    if isinstance(exc, ModuleNotFoundError) and exc.name in _POSIX_ONLY_MODULES:
        return f"POSIX-only: requires the '{exc.name}' module (unavailable on Windows)"
    if isinstance(exc, OSError) and getattr(exc, "winerror", None) == _WIN_SYMLINK_PRIVILEGE_ERROR:
        return "POSIX-only: creating symlinks needs Developer Mode or admin rights on Windows"
    if (
        item.nodeid.replace("\\", "/") in _UNIX_PERMISSION_TESTS
        and isinstance(exc, AssertionError)
        and "384" in str(exc)  # 0o600 == 384
    ):
        return "POSIX-only: Windows does not support Unix 0600 file permissions"
    return None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    if not IS_WINDOWS or call.excinfo is None:
        return
    report = outcome.get_result()
    if not report.failed:
        return
    reason = _posix_only_reason(item, call.excinfo)
    if reason:
        report.outcome = "skipped"
        report.longrepr = (str(item.path), item.location[1] or 0, f"Skipped: {reason}")
