"""Unit tests for the PyUnit test runner."""

import unittest
import pytest

from testplan.testing import pyunit
from testplan.testing import filtering
from testplan.testing import ordering
from testplan import defaults
import testplan.report

from tests.unit.testplan.testing import pyunit_expected_data

PYUNIT_DEFAULT_PARAMS = {
    "test_filter": filtering.Filter(),
    "test_sorter": ordering.NoopSorter(),
    "stdout_style": defaults.STDOUT_STYLE,
}


@pytest.mark.skip("Example PyUnit testsuite")
class Passing(unittest.TestCase):
    """
    Minimal PyUnit testcase with a single trivial test method. For more
    information about the unittest library, see the [documentation](
    http://docs.python.org/2/library/unittest.html).
    """

    def test_asserts(self):
        """Test with basic assertions."""
        self.assertTrue(True)
        self.assertFalse(False)


@pytest.mark.skip("Example PyUnit testsuite")
class Failing(unittest.TestCase):
    def test_asserts_false(self):
        """Assert False is True."""
        self.assertTrue(False)

    def test_raises(self):
        """Raises an Exception."""
        raise RuntimeError("Boom")


@pytest.fixture
def pyunit_runner_inst():
    """Return a PyUnit test runner instance."""
    return pyunit.PyUnit(
        name="My PyUnit",
        description="PyUnit example test",
        testcases=[Passing, Failing],
        **PYUNIT_DEFAULT_PARAMS
    )


def test_run_tests(pyunit_runner_inst):
    """Test running all PyUnit Testcases as a batch."""
    result = pyunit_runner_inst.run()
    report = result.report
    assert report.status == testplan.report.Status.FAILED
    assert len(report.entries) == 2

    passing_testsuite_report = report["Passing"]
    assert passing_testsuite_report.status == testplan.report.Status.PASSED
    assert passing_testsuite_report.name == "Passing"
    assert len(passing_testsuite_report.entries) == 1

    passing_testcase_report = passing_testsuite_report.entries[0]
    _check_passing_testcase_report(passing_testcase_report)

    failing_testsuite_report = report["Failing"]
    assert failing_testsuite_report.status == testplan.report.Status.FAILED
    assert failing_testsuite_report.name == "Failing"
    assert len(failing_testsuite_report.entries) == 1

    failing_testcase_report = failing_testsuite_report.entries[0]
    _check_failing_testcase_report(failing_testcase_report)


def test_dry_run(pyunit_runner_inst):
    """Test that the dry_run() method returns the expected report skeleton."""
    result = pyunit_runner_inst.dry_run()
    report = result.report
    assert report == pyunit_expected_data.EXPECTED_DRY_RUN_REPORT


def test_run_testcases_iter_all(pyunit_runner_inst):
    """Test running all testcases iteratively."""
    results = list(pyunit_runner_inst.run_testcases_iter())
    assert len(results) == 2

    passing_testcase_report, passing_parent_uids = results[0]
    assert passing_parent_uids == ["My PyUnit", "Passing"]
    _check_passing_testcase_report(passing_testcase_report)

    failing_testcase_report, failing_parent_uids = results[1]
    assert failing_parent_uids == ["My PyUnit", "Failing"]
    _check_failing_testcase_report(failing_testcase_report)


def test_run_testcases_iter_single(pyunit_runner_inst):
    """Test running a single testcase iteratively."""
    results = list(
        pyunit_runner_inst.run_testcases_iter(testsuite_pattern="Passing")
    )
    assert len(results) == 1

    passing_testcase_report, passing_parent_uids = results[0]
    assert passing_parent_uids == ["My PyUnit", "Passing"]
    _check_passing_testcase_report(passing_testcase_report)


def _check_passing_testcase_report(testcase_report):
    """Check the testsuite report generated by running the "Passing" PyUnit Testcase."""
    assert testcase_report.passed
    assert len(testcase_report.entries) == 1

    log_entry = testcase_report.entries[0]
    assert log_entry["type"] == "Log"
    assert log_entry["message"] == "All PyUnit testcases passed"


def _check_failing_testcase_report(testcase_report):
    """Check the testcase report for the Failing testsuite is as expected."""
    assert not testcase_report.passed
    assert len(testcase_report.entries) == 2

    error_entry = testcase_report.entries[0]
    assert "RuntimeError: Boom" in error_entry["content"]
    assert "test_raises" in error_entry["description"]

    fail_entry = testcase_report.entries[1]
    assert "AssertionError: False is not true" in fail_entry["content"]
    assert "test_asserts_false" in fail_entry["description"]
