import whisper
import warnings
import os
from pathlib import Path
import json
import subprocess
import threading

# 简体字转换
try:
    from opencc import OpenCC
    cc = OpenCC('t2s')  # 繁体转简体
    HAS_OPENCC = True
except ImportError:
    HAS_OPENCC = False
    print("Warning: opencc not installed, traditional Chinese will not be converted to simplified")

warnings.filterwarnings("ignore")

# 线程锁，确保模型加载和使用的线程安全
_model_lock = threading.Lock()


class VideoTranscriber:
    def __init__(self, model_size="base"):
        """
        初始化转录器

        Args:
            model_size: 模型大小 (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.model = None
        self._load_model()

    def _load_model(self):
        """加载Whisper模型 - 线程安全"""
        with _model_lock:
            print(f"[Whisper] Loading {self.model_size} model...")
            self.model = whisper.load_model(self.model_size)
            print(f"[Whisper] Model loaded successfully")

    def extract_audio(self, video_path, audio_path):
        """
        从视频提取音频 - 提取 MP3 格式用于下载

        Args:
            video_path: 视频文件路径
            audio_path: 音频输出路径（MP3格式）
        """
        try:
            print(f"[FFmpeg] Extracting audio from {video_path}")
            
            # 使用 FFmpeg 提取音频为 MP3 格式（用于下载）
            cmd = [
                "ffmpeg", "-i", video_path,
                "-vn",  # 不处理视频
                "-acodec", "libmp3lame",  # MP3 编码
                "-ab", "192k",  # 比特率
                "-ar", "44100",  # 采样率
                "-ac", "2",  # 立体声
                audio_path,
                "-y"  # 覆盖输出文件
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                check=True
            )

            # 获取视频时长
            cmd_duration = [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of", "csv=p=0", video_path
            ]
            duration_result = subprocess.run(
                cmd_duration, 
                capture_output=True, 
                text=True, 
                check=True
            )
            duration = float(duration_result.stdout.strip())
            
            # 验证音频文件是否成功创建
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                raise RuntimeError("Audio extraction failed: output file is empty")
            
            print(f"[FFmpeg] Audio extracted successfully: {duration:.2f} seconds")
            return duration

        except subprocess.CalledProcessError as e:
            print(f"[FFmpeg] Error: {e.stderr}")
            raise RuntimeError(f"Audio extraction failed: {e.stderr}")
        except Exception as e:
            print(f"[FFmpeg] Error extracting audio: {e}")
            raise

    def transcribe_with_progress(self, video_path, language=None, task="transcribe", progress_callback=None):
        """
        转录视频 - 直接处理，不分段（更稳定）
        使用线程锁确保模型使用的线程安全

        Args:
            video_path: 视频文件路径
            language: 语言代码
            task: 任务类型
            progress_callback: 进度回调函数
        """
        try:
            print(f"[Whisper] Transcribing: {video_path}")

            # 初始进度
            if progress_callback:
                progress_callback(0)

            # 转录参数
            options = {
                "task": task,
                "language": language,
                "verbose": False,
                "fp16": False,
                "beam_size": 5,  # 提高准确率
                "best_of": 5,
                "temperature": 0.0,  # 使用贪婪解码，更稳定
            }

            # 改进的进度更新（更平滑，不会卡在某个百分比）
            progress_value = [10]
            stop_progress = [False]
            start_time = [None]

            def update_progress():
                """智能进度更新 - 根据时间动态调整"""
                import time
                start_time[0] = time.time()
                
                while not stop_progress[0]:
                    elapsed = time.time() - start_time[0]
                    
                    # 根据经过的时间动态计算进度
                    # 假设平均每秒处理 1% 的进度
                    estimated_progress = 10 + min(int(elapsed / 2), 85)
                    
                    # 使用缓慢增长的曲线，避免卡在某个值
                    if progress_value[0] < estimated_progress:
                        progress_value[0] = estimated_progress
                    else:
                        # 即使估算进度没增加，也缓慢增长
                        progress_value[0] = min(progress_value[0] + 1, 95)
                    
                    if progress_callback:
                        progress_callback(progress_value[0])
                    
                    time.sleep(3)  # 每3秒更新一次

            # 启动进度更新线程
            progress_thread = threading.Thread(target=update_progress, daemon=True)
            progress_thread.start()

            try:
                # 使用线程锁确保模型使用的线程安全
                with _model_lock:
                    print(f"[Whisper] Starting transcription (thread-safe)")
                    result = self.model.transcribe(video_path, **options)
                    print(f"[Whisper] Transcription completed")
            finally:
                # 停止进度更新
                stop_progress[0] = True
                progress_thread.join(timeout=1)

            # 转换为简体字
            if HAS_OPENCC and result.get("text"):
                result["text"] = cc.convert(result["text"])
                for segment in result.get("segments", []):
                    if "text" in segment:
                        segment["text"] = cc.convert(segment["text"])

            # 完成
            if progress_callback:
                progress_callback(100)

            print(f"[Whisper] Transcription result: {len(result.get('text', ''))} characters")
            return result

        except Exception as e:
            print(f"[Whisper] Error transcribing: {e}")
            import traceback
            traceback.print_exc()
            raise

    def save_transcript(self, result, output_dir, task_id):
        """
        保存转录结果

        Args:
            result: 转录结果
            output_dir: 输出目录
            task_id: 任务ID
        """
        try:
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)

            # 保存为文本文件
            txt_path = os.path.join(output_dir, f"{task_id}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(result.get("text", ""))

            # 保存为SRT字幕文件
            srt_path = os.path.join(output_dir, f"{task_id}.srt")
            if result.get("segments"):
                self._save_srt(result["segments"], srt_path)

            # 保存为JSON文件
            json_path = os.path.join(output_dir, f"{task_id}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"[Save] Transcript saved: {txt_path}")
            return txt_path, srt_path, json_path
            
        except Exception as e:
            print(f"[Save] Error saving transcript: {e}")
            raise

    def _save_srt(self, segments, srt_file):
        """保存为SRT字幕格式"""
        srt_content = ""
        for i, segment in enumerate(segments, 1):
            start = self._format_time(segment.get("start", 0))
            end = self._format_time(segment.get("end", 0))
            text = segment.get("text", "").strip()

            if text:  # 只保存有文本的片段
                srt_content += f"{i}\n"
                srt_content += f"{start} --> {end}\n"
                srt_content += f"{text}\n\n"

        with open(srt_file, "w", encoding="utf-8") as f:
            f.write(srt_content)

    def _format_time(self, seconds):
        """将秒转换为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")


# 全局模型实例（单例模式）
_global_transcriber = None
_transcriber_lock = threading.Lock()


def get_transcriber():
    """
    获取转录器实例（单例模式，线程安全）
    所有任务共享同一个模型实例，但使用线程锁确保安全
    """
    global _global_transcriber
    
    with _transcriber_lock:
        if _global_transcriber is None:
            _global_transcriber = VideoTranscriber(model_size="base")
        return _global_transcriber
