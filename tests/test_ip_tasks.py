import poller
import pytest
import asyncio


class TestPyPerf:

    @pytest.mark.asyncio
    async def test_ping(self):
        task = poller.ip_tasks.Ping(device='127.0.0.1')
        result = await task.run()
        assert 'start_timestamp' in result
