from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os
import asyncio
from pathlib import Path
import uuid
from typing import List
import json

from app.database import get_db, init_db
from app.models import VideoTask
from app.tasks import TranscriptionTask

# 创建FastAPI应用
app = FastAPI(
    title="Video to Text Converter",
    description="Upload videos and convert them to text transcripts",
    version="1.0.0"
)

# 初始化数据库
init_db()

# 配置静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")

# 创建上传目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass


manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/upload")
async def upload_video(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    上传视频文件 - 支持并发处理和大文件
    """
    try:
        # 生成唯一ID
        task_id = str(uuid.uuid4())

        # 保存视频文件 - 使用任务ID作为文件名，避免同名冲突
        video_dir = UPLOAD_DIR / "videos"
        video_dir.mkdir(exist_ok=True)
        
        # 获取原始文件扩展名
        file_ext = Path(file.filename).suffix or '.mp4'
        video_path = video_dir / f"{task_id}{file_ext}"

        # 流式保存大文件，避免内存溢出
        print(f"[Upload] Saving file: {file.filename} -> {video_path.name}")
        
        with open(video_path, "wb") as buffer:
            # 分块读取，每次1MB
            chunk_size = 1024 * 1024
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                buffer.write(chunk)

        file_size = video_path.stat().st_size
        print(f"[Upload] File saved: {video_path} ({file_size / (1024*1024):.2f} MB)")

        # 创建数据库记录
        task = VideoTask(
            id=task_id,
            original_filename=file.filename,
            video_path=str(video_path),
            status="pending"
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        # 启动后台处理任务（不等待完成，支持并发）
        asyncio.create_task(process_video_task(task_id))

        print(f"[Upload] Task created: {task_id}")

        return JSONResponse({
            "success": True,
            "task_id": task_id,
            "message": "视频上传成功，开始处理"
        })

    except Exception as e:
        print(f"[Upload] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def get_websocket_manager():
    """获取WebSocket管理器"""
    return manager


async def process_video_task(task_id: str):
    """
    后台处理视频任务 - 支持并发
    """
    try:
        print(f"[Background] Starting task: {task_id}")
        task = TranscriptionTask(task_id, get_websocket_manager())
        await task.process()

        # 广播任务完成
        await manager.broadcast(json.dumps({
            "type": "task_completed",
            "task_id": task_id
        }))
        
        print(f"[Background] Task completed: {task_id}")

    except Exception as e:
        print(f"[Background] Task failed: {task_id}, Error: {e}")
        import traceback
        traceback.print_exc()
        
        await manager.broadcast(json.dumps({
            "type": "task_failed",
            "task_id": task_id,
            "error": str(e)
        }))


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """获取任务状态"""
    task = db.query(VideoTask).filter(VideoTask.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task.to_dict()


@app.get("/tasks")
async def list_tasks(db: Session = Depends(get_db)):
    """获取所有任务"""
    tasks = db.query(VideoTask).order_by(VideoTask.created_at.desc()).all()
    return [task.to_dict() for task in tasks]


@app.get("/download/audio/{task_id}")
async def download_audio(task_id: str, db: Session = Depends(get_db)):
    """下载音频文件"""
    task = db.query(VideoTask).filter(VideoTask.id == task_id).first()

    if not task or not task.audio_path:
        raise HTTPException(status_code=404, detail="音频文件不存在")

    if not os.path.exists(task.audio_path):
        raise HTTPException(status_code=404, detail="音频文件已删除")

    filename = f"{task.original_filename.rsplit('.', 1)[0]}.mp3"

    return FileResponse(
        task.audio_path,
        media_type="audio/mpeg",
        filename=filename
    )


@app.get("/download/transcript/{task_id}")
async def download_transcript(task_id: str, db: Session = Depends(get_db)):
    """下载文本文件"""
    task = db.query(VideoTask).filter(VideoTask.id == task_id).first()

    if not task or not task.transcript_path:
        raise HTTPException(status_code=404, detail="文本文件不存在")

    if not os.path.exists(task.transcript_path):
        raise HTTPException(status_code=404, detail="文本文件已删除")

    filename = f"{task.original_filename.rsplit('.', 1)[0]}.txt"

    return FileResponse(
        task.transcript_path,
        media_type="text/plain",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/download/srt/{task_id}")
async def download_srt(task_id: str, db: Session = Depends(get_db)):
    """下载SRT字幕文件"""
    task = db.query(VideoTask).filter(VideoTask.id == task_id).first()

    if not task or not task.srt_path:
        raise HTTPException(status_code=404, detail="SRT文件不存在")

    if not os.path.exists(task.srt_path):
        raise HTTPException(status_code=404, detail="SRT文件已删除")

    filename = f"{task.original_filename.rsplit('.', 1)[0]}.srt"

    return FileResponse(
        task.srt_path,
        media_type="text/plain",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/download/preview/{task_id}")
async def preview_transcript(task_id: str, db: Session = Depends(get_db)):
    """预览文本内容"""
    task = db.query(VideoTask).filter(VideoTask.id == task_id).first()

    if not task or not task.transcript_text:
        raise HTTPException(status_code=404, detail="文本内容不存在")

    return JSONResponse({
        "text": task.transcript_text[:500] + "..." if len(task.transcript_text) > 500 else task.transcript_text,
        "full_text": task.transcript_text,
        "filename": task.original_filename
    })


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """删除任务及相关文件"""
    task = db.query(VideoTask).filter(VideoTask.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    try:
        # 删除文件
        files_to_delete = [
            task.video_path,
            task.audio_path,
            task.transcript_path,
            task.srt_path
        ]

        for file_path in files_to_delete:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

        # 删除数据库记录
        db.delete(task)
        db.commit()

        return JSONResponse({
            "success": True,
            "message": "任务删除成功"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket连接，用于实时更新进度"""
    await manager.connect(websocket)

    try:
        # 连接建立后立即发送当前任务状态
        db = next(get_db())
        task = db.query(VideoTask).filter(VideoTask.id == task_id).first()

        if task:
            await manager.send_message(
                json.dumps({
                    "type": "progress_update",
                    "task_id": task_id,
                    "progress": task.progress,
                    "status": task.status,
                    "task_data": task.to_dict()
                }),
                websocket
            )

        while True:
            # 保持连接活跃
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "get_status":
                # 获取任务状态
                db = next(get_db())
                task = db.query(VideoTask).filter(VideoTask.id == task_id).first()

                if task:
                    await manager.send_message(
                        json.dumps(task.to_dict()),
                        websocket
                    )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print("=" * 50)
    print("🎬 Video to Text Converter Started!")
    print(f"📁 Upload directory: {UPLOAD_DIR.absolute()}")
    print(f"🌐 Server: http://localhost:8000")
    print("=" * 50)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
