"""
Fish Audio TTS 服务

提供文字转语音功能，支持动漫角色音色。
"""
import requests
from typing import Optional
from pathlib import Path
import tempfile
import os

from PySide6.QtCore import QObject, Signal, QUrl, QBuffer, QByteArray
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from app.common.logger import get_logger

logger = get_logger()


class TTSService(QObject):
    """Fish Audio TTS 服务"""

    # 播放状态信号
    playback_started = Signal(int)  # participant_id
    playback_finished = Signal(int)
    playback_error = Signal(int, str)  # participant_id, error_msg

    def __init__(self, api_key: str = None, parent=None):
        super().__init__(parent)
        self._api_key = api_key
        self._base_url = "https://api.fish.audio/v1"

        # 播放器
        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)

        # 当前播放状态
        self._current_participant_id: Optional[int] = None
        self._is_playing = False

        # 临时音频文件
        self._temp_file: Optional[str] = None

        # 连接播放器信号
        self._player.playbackStateChanged.connect(self._on_state_changed)
        self._player.errorOccurred.connect(self._on_error)

    @property
    def api_key(self) -> str:
        """获取 API Key"""
        return self._api_key or ""

    @api_key.setter
    def api_key(self, value: str):
        """设置 API Key"""
        self._api_key = value

    def is_playing(self) -> bool:
        """是否正在播放"""
        return self._is_playing

    def synthesize(self, text: str, voice_id: str) -> Optional[bytes]:
        """
        调用 Fish Audio API 合成语音

        Args:
            text: 要合成的文本
            voice_id: Fish Audio 音色 ID (reference_id)

        Returns:
            音频二进制数据，失败返回 None
        """
        if not self._api_key:
            logger.warning("Fish Audio API Key 未配置")
            return None

        if not voice_id:
            logger.warning("Fish Audio 音色 ID 未配置")
            return None

        try:
            url = f"{self._base_url}/tts"
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "text": text,
                "reference_id": voice_id,
                "format": "mp3"
            }

            logger.debug(f"调用 Fish Audio TTS API", extra={"voice_id": voice_id, "text_length": len(text)})
            response = requests.post(url, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                logger.info(f"Fish Audio TTS 合成成功", extra={"audio_size": len(response.content)})
                return response.content
            else:
                error_msg = f"API 返回错误: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        error_msg = error_data['message']
                except:
                    pass
                logger.error(f"Fish Audio TTS API 错误", extra={"status": response.status_code, "error": error_msg})
                return None

        except requests.exceptions.Timeout:
            logger.error("Fish Audio TTS API 请求超时")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Fish Audio TTS API 请求失败", extra={"error": str(e)})
            return None
        except Exception as e:
            logger.error(f"Fish Audio TTS 合成异常", extra={"error": str(e)})
            return None

    def play(self, text: str, voice_id: str, participant_id: int) -> bool:
        """
        合成并播放语音

        Args:
            text: 要播放的文本
            voice_id: Fish Audio 音色 ID
            participant_id: 参与者 ID（用于信号通知）

        Returns:
            是否成功开始播放
        """
        # 如果正在播放，先停止
        if self._is_playing:
            self.stop()

        # 检查配置
        if not self._api_key:
            self.playback_error.emit(participant_id, "Fish Audio API Key 未配置")
            return False

        if not voice_id:
            self.playback_error.emit(participant_id, "未配置音色 ID")
            return False

        # 合成语音
        audio_data = self.synthesize(text, voice_id)
        if not audio_data:
            self.playback_error.emit(participant_id, "语音合成失败")
            return False

        # 保存到临时文件
        try:
            # 清理旧的临时文件
            if self._temp_file and os.path.exists(self._temp_file):
                os.remove(self._temp_file)

            # 创建新临时文件
            temp_dir = tempfile.gettempdir()
            self._temp_file = os.path.join(temp_dir, f"tts_{participant_id}.mp3")
            with open(self._temp_file, 'wb') as f:
                f.write(audio_data)

            # 设置播放源
            self._current_participant_id = participant_id
            self._player.setSource(QUrl.fromLocalFile(self._temp_file))

            # 开始播放
            self._player.play()
            self._is_playing = True
            self.playback_started.emit(participant_id)

            logger.info(f"开始播放 TTS 音频", extra={"participant_id": participant_id})
            return True

        except Exception as e:
            logger.error(f"TTS 播放失败", extra={"error": str(e)})
            self.playback_error.emit(participant_id, f"播放失败: {str(e)}")
            return False

    def stop(self):
        """停止播放"""
        if self._is_playing:
            self._player.stop()
            self._is_playing = False
            logger.debug("停止 TTS 播放")

        # 清理临时文件
        if self._temp_file and os.path.exists(self._temp_file):
            try:
                os.remove(self._temp_file)
                self._temp_file = None
            except:
                pass

    def _on_state_changed(self, state):
        """播放状态变化"""
        from PySide6.QtMultimedia import QMediaPlayer

        if state == QMediaPlayer.StoppedState:
            if self._is_playing:
                self._is_playing = False
                if self._current_participant_id is not None:
                    self.playback_finished.emit(self._current_participant_id)
                    logger.debug(f"TTS 播放完成", extra={"participant_id": self._current_participant_id})

                # 清理临时文件
                if self._temp_file and os.path.exists(self._temp_file):
                    try:
                        os.remove(self._temp_file)
                        self._temp_file = None
                    except:
                        pass

    def _on_error(self, error, error_string):
        """播放错误"""
        logger.error(f"TTS 播放器错误", extra={"error": error_string})
        if self._current_participant_id is not None:
            self.playback_error.emit(self._current_participant_id, error_string)
        self._is_playing = False


# 全局 TTS 服务实例
tts_service = TTSService()
