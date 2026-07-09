"""QThread worker for anime conversion — local AnimeGANv2 with cloud fallback."""
import logging
from io import BytesIO

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QPixmap

from settings import get as get_setting

logger = logging.getLogger(__name__)


class AnimeWorker(QThread):
    """Background thread for anime conversion. Local-first, cloud optional."""

    started = pyqtSignal()
    finished = pyqtSignal(QPixmap)  # emits the result pixmap
    error = pyqtSignal(str)
    progress = pyqtSignal(str)     # status messages

    def __init__(self, image_path: str, style: str, parent=None):
        super().__init__(parent)
        self._image_path = image_path
        self._style = style

    def run(self):
        self.started.emit()

        api_key = (get_setting("replicate_api_key") or "").strip()

        if api_key:
            # Cloud mode — Replicate API
            self._run_cloud(api_key)
        else:
            # Local mode — AnimeGANv2
            self._run_local()

    def _run_local(self):
        from models.anime_local import AnimeLocal

        try:
            self.progress.emit("加载本地动漫模型...")
            client = AnimeLocal()
            self.progress.emit(f"本地生成中 ({self._style})...")
            result_img = client.convert(self._image_path, self._style)

            self.progress.emit("处理完成")
            self._emit_pixmap(result_img)

        except RuntimeError as e:
            self.error.emit(str(e))
        except Exception as e:
            logger.exception("Local anime conversion failed")
            self.error.emit(f"本地动漫化失败: {e}")

    def _run_cloud(self, api_key: str):
        from models.anime_client import AnimeClient

        try:
            self.progress.emit("连接 SiliconFlow API...")
            client = AnimeClient()
            self.progress.emit(f"云端生成中 ({self._style})...")
            result_img = client.convert(self._image_path, self._style)

            self.progress.emit("下载结果...")
            self._emit_pixmap(result_img)

        except ValueError as e:
            self.error.emit(str(e))
        except RuntimeError as e:
            self.error.emit(str(e))
        except Exception as e:
            logger.exception("Cloud anime conversion failed")
            self.error.emit(f"云端动漫化失败: {e}")

    def _emit_pixmap(self, img):
        buf = BytesIO()
        img.save(buf, format="PNG")
        pix = QPixmap()
        pix.loadFromData(buf.getvalue(), "PNG")

        if pix.isNull():
            self.error.emit("无法加载动漫化结果")
            return

        self.progress.emit("完成")
        self.finished.emit(pix)
