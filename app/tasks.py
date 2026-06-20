import os
import time
from pathlib import Path
from app.transcribe import get_transcriber
from app.database import SessionLocal
from app.models import VideoTask
from datetime import datetime
import json
import asyncio


def _ts() -> str:
    return time.strftime("%H:%M:%S", time.localtime()) + f".{int((time.time() % 1) * 1000):03d}"


def log(tag: str, msg: str) -> None:
    print(f"[{_ts()}] [{tag}] {msg}", flush=True)


# 转录并发信号量：限制同时进行转录的任务数，避免多任务争抢模型/内存
MAX_CONCURRENT_TRANSCRIPTIONS = int(os.getenv("MAX_CONCURRENT_TRANSCRIPTIONS", "1"))
_transcription_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TRANSCRIPTIONS)


class TranscriptionTask:
    def __init__(self, task_id, websocket_manager=None):
        self.task_id = task_id
        self.db = SessionLocal()
        self.task = self.db.query(VideoTask).filter(VideoTask.id == task_id).first()
        self.websocket_manager = websocket_manager

        # 目录配置
        self.base_dir = Path("uploads")
        self.video_dir = self.base_dir / "videos"
        self.audio_dir = self.base_dir / "audios"
        self.transcript_dir = self.base_dir / "transcripts"

        # 创建目录
        self.video_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.transcript_dir.mkdir(parents=True, exist_ok=True)

    async def update_progress(self, progress, status=None):
        """更新任务进度"""
        if status:
            self.task.status = status
        self.task.progress = progress
        self.db.commit()
        log("Task", f"{self.task_id[:8]} progress={progress}% status={status or self.task.status}")

        # 同时广播进度更新
        await self.broadcast_progress()

    async def broadcast_progress(self):
        """广播进度更新到所有WebSocket连接"""
        if self.websocket_manager and self.websocket_manager.active_connections:
            try:
                task_data = self.task.to_dict()
                message = json.dumps({
                    "type": "progress_update",
                    "task_id": self.task_id,
                    "progress": self.task.progress,
                    "status": self.task.status,
                    "task_data": task_data
                })

                bt0 = time.time()
                conns = list(self.websocket_manager.active_connections)
                # 直接使用异步方式发送消息给每个连接
                for connection in conns:
                    try:
                        await connection.send_text(message)
                    except Exception as e:
                        log("Task", f"{self.task_id[:8]} ws send failed: {e}")
                cost = time.time() - bt0
                if cost > 0.5:
                    log("Task", f"{self.task_id[:8]} broadcast slow cost={cost:.2f}s conns={len(conns)}")
            except Exception as e:
                log("Task", f"{self.task_id[:8]} broadcast error: {e}")

    async def process(self):
        """处理视频转录任务"""
        t_start = time.time()
        try:
            log("Task", f"{self.task_id[:8]} === process() begin ===")

            # 更新状态为处理中
            await self.update_progress(0, "processing")

            # 1. 文件路径 —— 使用数据库里保存的真实路径，避免写死 .mp4
            if self.task and self.task.video_path:
                video_path = Path(self.task.video_path)
            else:
                # 兜底：在 video_dir 下按 task_id 通配
                candidates = list(self.video_dir.glob(f"{self.task_id}.*"))
                if not candidates:
                    raise FileNotFoundError(
                        f"Video file not found for task {self.task_id} (db.video_path empty, no glob match)"
                    )
                video_path = candidates[0]

            log("Task", f"{self.task_id[:8]} video_path={video_path}")

            if not video_path.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")

            # 验证文件大小
            file_size = video_path.stat().st_size
            log("Task", f"{self.task_id[:8]} file_size={file_size / (1024 * 1024):.2f} MB")

            # 2. 提取音频（用于下载）
            audio_path = self.audio_dir / f"{self.task_id}.mp3"
            await self.update_progress(5, "extracting_audio")

            log("Task", f"{self.task_id[:8]} loading transcriber instance ...")
            t_get = time.time()
            transcriber_instance = get_transcriber()
            log("Task", f"{self.task_id[:8]} transcriber ready cost={time.time() - t_get:.2f}s")

            # 在线程池中运行音频提取
            loop = asyncio.get_event_loop()
            try:
                t_audio = time.time()
                log("Task", f"{self.task_id[:8]} extract_audio start")
                duration = await loop.run_in_executor(
                    None,
                    transcriber_instance.extract_audio,
                    str(video_path),
                    str(audio_path)
                )
                log("Task", f"{self.task_id[:8]} extract_audio done duration={duration:.2f}s cost={time.time() - t_audio:.2f}s")
                self.task.duration = duration
                self.task.audio_path = str(audio_path)
                self.db.commit()
            except Exception as e:
                log("Task", f"{self.task_id[:8]} extract_audio FAILED: {e}")
                # 音频提取失败不影响转录，继续处理
                # 但不设置 audio_path，这样前端就不会显示下载按钮

            # 3. 转录视频（通过信号量排队，避免多任务同时占用模型）
            log("Task", f"{self.task_id[:8]} waiting for transcription slot (max={MAX_CONCURRENT_TRANSCRIPTIONS})...")
            await self.update_progress(10, "queued")

            async with _transcription_semaphore:
                self.db.refresh(self.task)
                if self.task.status == "cancelled":
                    log("Task", f"{self.task_id[:8]} cancelled before transcription start")
                    return

                await self.update_progress(10, "transcribing")

                def sync_progress_callback(progress):
                    mapped_progress = 10 + (progress * 0.85)
                    asyncio.run_coroutine_threadsafe(
                        self.update_progress(int(mapped_progress)),
                        loop
                    )

                t_trans = time.time()
                log("Task", f"{self.task_id[:8]} transcribe start (run_in_executor)")
                result = await loop.run_in_executor(
                    None,
                    lambda: transcriber_instance.transcribe_with_progress(
                        str(video_path),
                        task="transcribe",
                        progress_callback=sync_progress_callback
                    )
                )
                log("Task", f"{self.task_id[:8]} transcribe done cost={time.time() - t_trans:.2f}s text_len={len(result.get('text', ''))}")

            # 4. 保存转录结果
            await self.update_progress(95, "saving_results")
            t_save = time.time()
            txt_path, srt_path, json_path = transcriber_instance.save_transcript(
                result,
                str(self.transcript_dir),
                self.task_id
            )
            log("Task", f"{self.task_id[:8]} save_transcript done cost={time.time() - t_save:.2f}s")

            # 5. 更新数据库
            self.task.transcript_path = txt_path
            self.task.srt_path = srt_path
            self.task.transcript_text = result.get("text", "")
            self.task.status = "completed"
            self.task.progress = 100
            self.task.completed_at = datetime.utcnow()
            self.db.commit()

            log("Task", f"{self.task_id[:8]} === process() done total_cost={time.time() - t_start:.2f}s ===")

        except Exception as e:
            log("Task", f"{self.task_id[:8]} process FAILED after {time.time() - t_start:.2f}s: {e}")
            import traceback
            traceback.print_exc()

            self.task.status = "failed"
            self.task.error_message = str(e)
            self.db.commit()

            # 广播失败状态
            await self.broadcast_progress()
            raise

        finally:
            self.db.close()
