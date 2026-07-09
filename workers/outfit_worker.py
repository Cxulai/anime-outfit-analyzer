"""QThread worker for outfit analysis — runs YOLO + CLIP in background."""
import logging

from PyQt6.QtCore import QThread, pyqtSignal

from data.schema import OutfitAnalysis

logger = logging.getLogger(__name__)


class OutfitWorker(QThread):
    """Background thread for clothing detection + classification."""

    started = pyqtSignal()
    finished = pyqtSignal(dict)  # emits analysis.to_dict()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)   # status messages

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self._image_path = image_path

    def run(self):
        from models.outfit_model import OutfitModel

        self.started.emit()
        self.progress.emit("加载模型中...")

        try:
            model = OutfitModel()
            self.progress.emit("检测人物...")
            analysis = model.analyze(self._image_path)

            if not analysis.items:
                self.error.emit("未检测到人物或服装，请换一张图")
                return

            self.progress.emit("分析完成")
            self.finished.emit(analysis.to_dict())

        except Exception as e:
            logger.exception("Outfit analysis failed")
            self.error.emit(f"分析失败: {e}")
