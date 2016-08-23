import poller
import pytest
import asyncio


class TestPyPerf:

    @pytest.mark.asyncio
    async def test_http_get(self):
        task = poller.http_tasks.GetPage(url='http://www.whatismyip.com/')
        result = await task.run()
        assert 'start_timestamp' in result
