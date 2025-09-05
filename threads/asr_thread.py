"""语音识别线程 - 增强安全性和错误处理"""
import json
import gzip
import uuid
import asyncio
import websockets
import wave
import time
import logging
from io import BytesIO
from PySide6.QtCore import QThread, Signal
from utils.config import Config

logger = logging.getLogger(__name__)


class ASRThread(QThread):
    """语音识别线程"""

    result = Signal(str)  # 识别结果
    error = Signal(str)  # 错误信息

    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path
        self.config = Config.get_instance()
        self._stop_requested = False

        # WebSocket超时设置
        self.ws_timeout = self.config.WS_TIMEOUT
        self.max_retries = self.config.MAX_RETRIES

    def stop(self):
        """停止识别"""
        self._stop_requested = True

    def run(self):
        """执行语音识别"""
        try:
            if self._stop_requested:
                return

            # 等待文件写入完成
            time.sleep(0.1)

            # 读取音频文件（增加重试机制）
            audio_data = None
            for attempt in range(self.max_retries):
                try:
                    if self._stop_requested:
                        return
                    with open(self.audio_path, 'rb') as f:
                        audio_data = f.read()
                    break
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise e
                    time.sleep(0.1)

            if not audio_data:
                self.error.emit("无法读取音频文件")
                return

            # 校验音频格式
            if not self.validate_audio_format(audio_data):
                return

            # 执行识别
            logger.info("🔍 正在识别语音...")
            text = asyncio.run(self.recognize(audio_data))

            if self._stop_requested:
                return

            if text and text.strip():
                logger.info(f"✅ 识别成功: {text}")
                self.result.emit(text.strip())
            else:
                self.error.emit("未识别到有效语音内容")

        except Exception as e:
            if not self._stop_requested:
                logger.error(f"识别错误: {e}")
                self.error.emit(f"识别错误：{str(e)}")

    def validate_audio_format(self, audio_data):
        """校验音频格式"""
        try:
            if len(audio_data) < 44:  # WAV文件头最小长度
                self.error.emit("音频文件太小或损坏")
                return False

            with BytesIO(audio_data) as f:
                wf = wave.open(f, 'rb')
                nchannels = wf.getnchannels()
                framerate = wf.getframerate()
                sampwidth = wf.getsampwidth()
                nframes = wf.getnframes()
                wf.close()

            # 检查音频长度
            duration = nframes / framerate if framerate > 0 else 0
            if duration < self.config.MIN_RECORD_TIME:
                self.error.emit(f"录音时间太短（{duration:.1f}秒），需要至少{self.config.MIN_RECORD_TIME}秒")
                return False
            if duration > self.config.MAX_RECORD_TIME:
                self.error.emit(f"录音时间太长（{duration:.1f}秒），最多{self.config.MAX_RECORD_TIME}秒")
                return False

            # 要求：单声道、16000Hz采样率、16位深
            if nchannels != 1:
                self.error.emit(f"音频格式错误：需单声道，实际{nchannels}声道")
                return False
            if framerate != 16000:
                self.error.emit(f"音频格式错误：需16000Hz，实际{framerate}Hz")
                return False
            if sampwidth != 2:
                self.error.emit(f"音频格式错误：需16位深，实际{sampwidth * 8}位深")
                return False

            logger.info(f"音频验证通过: {duration:.1f}秒, {nchannels}声道, {framerate}Hz, {sampwidth*8}位")
            return True

        except Exception as e:
            self.error.emit(f"音频格式解析失败：{str(e)}")
            return False

    async def recognize(self, audio_data):
        """异步识别"""
        if self._stop_requested:
            return None

        reqid = str(uuid.uuid4())

        # 构建请求参数
        request_params = {
            'app': {
                'appid': self.config.ASR_APP_ID,
                'cluster': self.config.ASR_CLUSTER,
                'token': self.config.ASR_TOKEN,
            },
            'user': {'uid': 'image_gen_app'},
            'request': {
                'reqid': reqid,
                'nbest': 1,
                'workflow': 'audio_in,resample,partition,vad,fe,decode,itn,nlu_punctuate',
                'show_language': False,
                'show_utterances': False,
                'result_type': 'full',
                'sequence': 1
            },
            'audio': {
                'format': 'wav',
                'rate': 16000,
                'language': 'zh-CN',
                'bits': 16,
                'channel': 1,
                'codec': 'raw'
            }
        }

        ws = None
        try:
            # WebSocket连接 - 增加重试
            header = {'Authorization': f'Bearer; {self.config.ASR_TOKEN}'}

            for attempt in range(self.max_retries):
                if self._stop_requested:
                    return None

                try:
                    ws = await asyncio.wait_for(
                        websockets.connect(
                            self.config.ASR_WS_URL,
                            additional_headers=header,
                            ping_interval=10,
                            ping_timeout=5,
                            close_timeout=10
                        ),
                        timeout=10
                    )
                    break
                except Exception as e:
                    logger.warning(f"WebSocket连接失败 (尝试 {attempt+1}/{self.max_retries}): {e}")
                    if attempt == self.max_retries - 1:
                        raise e
                    await asyncio.sleep(1)

            if not ws:
                raise Exception("无法建立WebSocket连接")

            # 发送初始请求
            payload_bytes = gzip.compress(json.dumps(request_params).encode())
            full_request = bytearray(self.generate_full_default_header())
            full_request.extend(len(payload_bytes).to_bytes(4, 'big'))
            full_request.extend(payload_bytes)

            await ws.send(full_request)

            if self._stop_requested:
                return None

            res = await asyncio.wait_for(ws.recv(), timeout=self.ws_timeout)
            init_result = self.parse_response(res)

            # 检查初始化响应
            if 'payload_msg' in init_result:
                if init_result['payload_msg'].get('code') != 1000:
                    error_msg = init_result['payload_msg'].get('message', '未知错误')
                    logger.error(f"❌ 服务器初始化失败：{error_msg}")
                    return None

            # 发送音频数据分片
            final_result = ""
            segment_size = self.calculate_segment_size(audio_data)

            for seq, (chunk, is_last) in enumerate(self.slice_data(audio_data, segment_size), 1):
                if self._stop_requested:
                    return None

                chunk_bytes = gzip.compress(chunk)

                # 选择正确的header
                if is_last:
                    header = self.generate_last_audio_default_header()
                else:
                    header = self.generate_audio_default_header()

                audio_request = bytearray(header)
                audio_request.extend(len(chunk_bytes).to_bytes(4, 'big'))
                audio_request.extend(chunk_bytes)

                await ws.send(audio_request)
                res = await asyncio.wait_for(ws.recv(), timeout=self.ws_timeout)
                segment_result = self.parse_response(res)

                # 处理识别结果
                if 'payload_msg' in segment_result and 'result' in segment_result['payload_msg']:
                    result_data = segment_result['payload_msg']['result']

                    if isinstance(result_data, list) and len(result_data) > 0:
                        text_content = result_data[0].get('text', '')
                        if text_content:
                            final_result = text_content
                            logger.info(f"  片段{seq}: {text_content[:30]}...")
                    elif isinstance(result_data, str):
                        final_result = result_data

            return final_result if final_result else None

        except asyncio.TimeoutError:
            logger.error("❌ WebSocket连接超时")
            return None
        except Exception as e:
            logger.error(f"❌ 识别失败: {str(e)}")
            return None
        finally:
            if ws:
                try:
                    await ws.close()
                except Exception:
                    pass

    def calculate_segment_size(self, audio_data):
        """计算分片大小"""
        try:
            with BytesIO(audio_data) as f:
                wf = wave.open(f, 'rb')
                nchannels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                wf.close()

            # 15秒分片
            size_per_sec = nchannels * sampwidth * framerate
            return int(size_per_sec * 15)
        except Exception:
            # 回退到默认值
            return 480000  # 假设16kHz, 1通道, 16位, 15秒

    def slice_data(self, data: bytes, chunk_size: int):
        """将音频数据分片"""
        data_len = len(data)
        offset = 0
        while offset + chunk_size < data_len:
            yield data[offset: offset + chunk_size], False
            offset += chunk_size
        yield data[offset:], True

    def generate_header(self, version=0b0001, message_type=0b0001,
                        message_type_specific_flags=0b0000, serial_method=0b0001,
                        compression_type=0b0001, reserved_data=0x00, extension_header=bytes()):
        """生成协议头"""
        header = bytearray()
        header_size = int(len(extension_header) / 4) + 1
        header.append((version << 4) | header_size)
        header.append((message_type << 4) | message_type_specific_flags)
        header.append((serial_method << 4) | compression_type)
        header.append(reserved_data)
        header.extend(extension_header)
        return header

    def generate_full_default_header(self):
        """生成完整请求头"""
        return self.generate_header()

    def generate_audio_default_header(self):
        """生成音频数据头"""
        return self.generate_header(message_type=0b0010)

    def generate_last_audio_default_header(self):
        """生成最后一个音频数据头"""
        return self.generate_header(
            message_type=0b0010,
            message_type_specific_flags=0b0010
        )

    def parse_response(self, res):
        """解析服务器响应"""
        try:
            if len(res) < 4:
                return {"error": "响应数据过短"}

            protocol_version = res[0] >> 4
            header_size = res[0] & 0x0f
            message_type = res[1] >> 4
            message_compression = res[2] & 0x0f
            serialization_method = res[2] >> 4

            if header_size * 4 > len(res):
                return {"error": "头部大小错误"}

            payload = res[header_size * 4:]
            result = {}
            payload_msg = None
            payload_size = 0

            if message_type == 0b1001:  # 完整响应
                if len(payload) >= 4:
                    payload_size = int.from_bytes(payload[:4], "big", signed=True)
                    payload_msg = payload[4:]
            elif message_type == 0b1011:  # 确认响应
                if len(payload) >= 4:
                    seq = int.from_bytes(payload[:4], "big", signed=True)
                    result['seq'] = seq
                if len(payload) >= 8:
                    payload_size = int.from_bytes(payload[4:8], "big", signed=False)
                    payload_msg = payload[8:]
            elif message_type == 0b1111:  # 错误响应
                if len(payload) >= 4:
                    code = int.from_bytes(payload[:4], "big", signed=False)
                    result['code'] = code
                payload_msg = payload[8:] if len(payload) >= 8 else b""

            if payload_msg:
                if message_compression == 0b0001:  # GZIP解压
                    try:
                        payload_msg = gzip.decompress(payload_msg)
                    except Exception as e:
                        return {"error": f"解压失败: {e}"}

                if serialization_method == 0b0001:  # JSON解析
                    try:
                        payload_msg = json.loads(payload_msg.decode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        # 尝试直接解码为字符串
                        try:
                            payload_msg = payload_msg.decode("utf-8")
                        except UnicodeDecodeError:
                            return {"error": f"数据解码失败: {e}"}
                else:
                    try:
                        payload_msg = payload_msg.decode("utf-8")
                    except UnicodeDecodeError:
                        return {"error": "字符串解码失败"}

                result['payload_msg'] = payload_msg

            return result
        except Exception as e:
            logger.error(f"❌ 响应解析失败：{str(e)}")
            return {"error": str(e)}