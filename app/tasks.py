import os
from pathlib import Path
from app.transcribe import get_transcriber
from app.database import SessionLocal
from app.models import VideoTask
from datetime import datetime
import json
import asyncio


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
        print(f"[Task {self.task_id}] Progress: {progress}%, Status: {status or self.task.status}")

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
                
                # 直接使用异步方式发送消息给每个连接
                for connection in self.websocket_manager.active_connections:
                    try:
                        await connection.send_text(message)
                    except Exception as e:
                        print(f"Error sending message to connection: {e}")
            except Exception as e:
                print(f"Error broadcasting progress for task {self.task_id}: {e}")

    async def process(self):
        """处理视频转录任务"""
        try:
            print(f"[Task {self.task_id}] Starting processing...")

            # 更新状态为处理中
            await self.update_progress(0, "processing")

            # 1. 文件路径
            video_path = self.video_dir / f"{self.task_id}.mp4"

            if not video_path.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")

            # 验证文件大小
            file_size = video_path.stat().st_size
            print(f"[Task {self.task_id}] Video file size: {file_size / (1024*1024):.2f} MB")

            # 2. 提取音频（用于下载）
            audio_path = self.audio_dir / f"{self.task_id}.mp3"
            await self.update_progress(5, "extracting_audio")

            transcriber_instance = get_transcriber()
            
            # 在线程池中运行音频提取
            loop = asyncio.get_event_loop()
            try:
                duration = await loop.run_in_executor(
                    None,
                    transcriber_instance.extract_audio,
                    str(video_path),
                    str(audio_path)
                )
                self.task.duration = duration
                self.task.audio_path = str(audio_path)
                self.db.commit()
                print(f"[Task {self.task_id}] Audio extracted: {duration:.2f}s, saved to {audio_path}")
            except Exception as e:
                print(f"[Task {self.task_id}] Audio extraction failed: {e}")
                # 音频提取失败不影响转录，继续处理
                # 但不设置 audio_path，这样前端就不会显示下载按钮

            # 3. 转录视频
            await self.update_progress(10, "transcribing")

            # 创建一个同步的进度回调包装器
            def sync_progress_callback(progress):
                # 将0-100的进度映射到10-95的范围
                mapped_progress = 10 + (progress * 0.85)
                # 在事件循环中调度异步更新
                asyncio.run_coroutine_threadsafe(
                    self.update_progress(int(mapped_progress)),
                    loop
                )

            # 在线程池中运行转录任务
            print(f"[Task {self.task_id}] Starting transcription...")
            result = await loop.run_in_executor(
                None,
                lambda: transcriber_instance.transcribe_with_progress(
                    str(video_path),
                    language="zh",
                    task="transcribe",
                    progress_callback=sync_progress_callback
                )
            )

            print(f"[Task {self.task_id}] Transcription completed")

            # 4. 保存转录结果
            await self.update_progress(95, "saving_results")
            txt_path, srt_path, json_path = transcriber_instance.save_transcript(
                result,
                str(self.transcript_dir),
                self.task_id
            )

            # 5. 更新数据库
            self.task.transcript_path = txt_path
            self.task.srt_path = srt_path
            self.task.transcript_text = result.get("text", "")
            self.task.status = "completed"
            self.task.progress = 100
            self.task.completed_at = datetime.utcnow()
            self.db.commit()

            print(f"[Task {self.task_id}] Processing completed successfully")

        except Exception as e:
            print(f"[Task {self.task_id}] Processing failed: {e}")
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
