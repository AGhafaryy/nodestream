import pytest

from nodestream.pipeline import Pipeline
from nodestream.pipeline.extractors import IterableExtractor
from nodestream.pipeline.object_storage import ObjectStore
from nodestream.pipeline.progress_reporter import PipelineProgressReporter
from nodestream.pipeline.step import Step


class ExplodesAfter(Step):
    def __init__(self, explode_after: int):
        self.count = 0
        self.explode_after = explode_after

    async def process_record(self, record, context):
        self.count += 1
        if self.count > self.explode_after:
            raise Exception("Exploded!")
        yield record


@pytest.mark.asyncio
async def test_snapshot_handling_during_errors(mocker):
    extractor = IterableExtractor.range(0, 100000000)
    kaboom = ExplodesAfter(5000)
    storage = mocker.Mock(spec=ObjectStore)
    storage.namespaced.return_value = storage
    pipeline = Pipeline((extractor, kaboom), 1000, storage)

    await pipeline.run(PipelineProgressReporter())

    # Check that we have a checkpoint placed and
    # that we don't delete the checkpoint if we encounter an error.
    storage.delete.assert_not_called()
    storage.put_picklable.assert_called()
