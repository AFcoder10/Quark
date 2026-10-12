from __future__ import annotations

import asyncio

from loguru import logger

from app.metadata.builder import MetadataBuilder
from app.optimization.hls_builder import HLSBuilder, OptimizationError
from app.optimization.hevc_builder import HEVCBuilder
from app.optimization.queue import OptimizationQueue


async def optimization_worker(queue: OptimizationQueue) -> None:
    metadata_builder = MetadataBuilder()
    hls_builder = HLSBuilder()
    hevc_builder = HEVCBuilder()
    while True:
        media_id = await queue.next()
        job = queue.get_job(media_id)
        mode = job.mode if job else "hls"
        queue.start(media_id)
        logger.info("Optimizing {} (mode={})", media_id, mode)
        try:
            meta = metadata_builder.load(media_id)
            if meta is None:
                raise OptimizationError(f"No metadata found for {media_id}")
            if queue.should_cancel(media_id):
                continue
            
            cb = lambda progress, message: queue.update(media_id, progress, message) if not queue.should_cancel(media_id) else None
            
            if mode == "hevc":
                hevc_builder.on_progress = cb
                updated_meta = await hevc_builder.build(meta)
            else:
                hls_builder.on_progress = cb
                updated_meta = await hls_builder.build(meta)
                
            metadata_builder.save(updated_meta)

            if queue.should_cancel(media_id):
                continue
            queue.finish(media_id)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Optimization failed for {}", media_id)
            queue.fail(media_id, str(exc))