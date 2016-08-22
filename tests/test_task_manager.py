import poller
import pytest


class TestPyPerf:

    def test_init_task_manager(self):
        manager = poller.TaskManager()
        assert manager
