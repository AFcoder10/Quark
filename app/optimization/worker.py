from __future__ import annotations

import asyncio

from loguru import logger

from app.metadata.builder import MetadataBuilder
from app.optimization.hls_builder import HLSBuilder, OptimizationError
from app.optimization.queue import OptimizationQueue


async def optimization_worker(queue: OptimizationQueue) -> None:
    metadata_builder = MetadataBuilder()
    hls_builder = HLSBuilder()
    while True:
        media_id = await queue.next()
        queue.start(media_id)
        logger.info("Optimizing %s", media_id)
        try:
            meta = metadata_builder.load(media_id)
            if meta is None:
                raise OptimizationError(f"No metadata found for {media_id}")
            if queue.should_cancel(media_id):
                continue
            hls_builder.on_progress = lambda progress, message: queue.update(media_id, progress, message) if not queue.should_cancel(media_id) else None
            await hls_builder.build(meta)
            if queue.should_cancel(media_id):
                continue
            queue.finish(media_id)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Optimization failed for %s", media_id)
            queue.fail(media_id, str(exc))