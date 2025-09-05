# threads/record_thread.py
# -*- coding: utf-8 -*-
"""录音线程 - 优先使用 arecord，稳定避坑；每次覆盖输出"""

import os
import time
import signal
import shutil
import subprocess
from PySide6.QtCore import QThread, Signal

# 回退用：仅在没有 arecord 时再用 PyAudio
try:
    import pyaudio
except Exception:
    pyaudio = None


class RecordThread(QThread):
    """每次覆盖写 /tmp/ai_voice_image_record.wav；优先 arecord"""

    finished = Signal(str)  # 返回音频文件路径
    error = Signal(str)     # 错误信息

    def __init__(self, out_path="/tmp/ai_voice_image_record.wav", device=None):
        super().__init__()
        self.out_path = out_path
        self.device = device  # arecord 的 -D 设备名，可选
        self.recording = True
        self._proc = None  # arecord 子进程句柄

        # 录音参数（ASR 要求）
        self.rate = 16000
        self.channels = 1
        self.sample_fmt = "S16_LE"  # 16-bit

    def run(self):
        try:
            os.makedirs(os.path.dirname(self.out_path), exist_ok=True)
            # 先删旧文件，确保是干净输出
            try:
                if os.path.exists(self.out_path):
                    os.remove(self.out_path)
            except:
                pass

            if self._has_arecord():
                ok = self._record_with_arecord()
            else:
                ok = self._record_with_pyaudio()

            if not ok:
                self.finished.emit("")
                return

            # 基本校验
            if not os.path.exists(self.out_path) or os.path.getsize(self.out_path) < 64:
                self.error.emit("录音文件无效或过短")
                self.finished.emit("")
                return

            self.finished.emit(self.out_path)

        except Exception as e:
            self.error.emit(f"录音失败: {e}")
            self.finished.emit("")
        finally:
            print("🧹 录音资源已清理")

    def stop(self):
        """请求停止录音"""
        self.recording = False
        # arecord 的停止在 _record_with_arecord 内通过 SIGINT/terminate 实现

    # ---------- arecord 路径 ----------

    def _has_arecord(self):
        return shutil.which("arecord") is not None

    def _record_with_arecord(self):
        """使用 arecord，更稳"""
        try:
            cmd = [
                "arecord",
                "-q",                    # 静默
                "-t", "wav",             # 输出 wav
                "-f", self.sample_fmt,   # S16_LE
                "-r", str(self.rate),    # 16000 Hz
                "-c", str(self.channels) # 单声道
            ]
            # 指定设备（可选）
            if self.device:
                cmd += ["-D", self.device]

            # 输出文件路径作为最后一个参数
            cmd += [self.out_path]

            print("🎙️ 使用 arecord 录音:", " ".join(cmd))
            # 注意：arecord 会直接写入文件，不需要我们再写
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # 直到 stop() 被调用
            while self.recording and self._proc.poll() is None:
                time.sleep(0.05)

            # 请求退出
            if self._proc and self._proc.poll() is None:
                try:
                    # 优先发 SIGINT 让 arecord 写好 WAV 头
                    self._proc.send_signal(signal.SIGINT)
                    for _ in range(40):  # 最多等 2 秒
                        if self._proc.poll() is not None:
                            break
                        time.sleep(0.05)
                except Exception:
                    pass

            # 兜底：还没退出就 terminate/kill
            if self._proc and self._proc.poll() is None:
                try:
                    self._proc.terminate()
                    for _ in range(20):
                        if self._proc.poll() is not None:
                            break
                        time.sleep(0.05)
                except Exception:
                    pass
            if self._proc and self._proc.poll() is None:
                try:
                    self._proc.kill()
                except Exception:
                    pass

            return True

        except FileNotFoundError:
            self.error.emit("找不到 arecord，请安装 alsa-utils")
            return False
        except Exception as e:
            self.error.emit(f"arecord 录音失败: {e}")
            return False

    # ---------- PyAudio 回退 ----------

    def _record_with_pyaudio(self):
        """仅在没有 arecord 时回退；注意某些板子上 PortAudio 可能 abort"""
        if pyaudio is None:
            self.error.emit("系统缺少 arecord 且 PyAudio 不可用")
            return False

        audio = None
        stream = None
        frames = []
        CHUNK = 2048
        FORMAT = pyaudio.paInt16

        try:
            audio = pyaudio.PyAudio()
            # 首选 16kHz，不行则回退到设备默认
            try:
                stream = audio.open(format=FORMAT,
                                    channels=self.channels,
                                    rate=self.rate,
                                    input=True,
                                    frames_per_buffer=CHUNK)
                actual_rate = self.rate
            except Exception:
                default_rate = int(audio.get_default_input_device_info().get('defaultSampleRate', self.rate))
                stream = audio.open(format=FORMAT,
                                    channels=self.channels,
                                    rate=default_rate,
                                    input=True,
                                    frames_per_buffer=CHUNK)
                actual_rate = default_rate
                print(f"⚠️ 采样率回退到设备默认: {default_rate}Hz")

            print("🔴 录音中（PyAudio 回退）...")
            while self.recording:
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

            # 停止流
            if stream and stream.is_active():
                stream.stop_stream()
            if stream:
                stream.close()

            # 保存到固定路径（覆盖）
            import wave
            os.makedirs(os.path.dirname(self.out_path), exist_ok=True)
            with wave.open(self.out_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(audio.get_sample_size(FORMAT))
                wf.setframerate(actual_rate)
                wf.writeframes(b''.join(frames))

            print(f"💾 录音已保存: {self.out_path}")
            return True

        except Exception as e:
            self.error.emit(f"PyAudio 录音失败: {e}")
            return False
        finally:
            try:
                if stream:
                    if stream.is_active():
                        stream.stop_stream()
                    stream.close()
            except:
                pass
            try:
                if audio:
                    audio.terminate()
            except:
                pass