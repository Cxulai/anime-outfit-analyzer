"""QThread worker for fashion reference search."""
import logging

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class SearchWorker(QThread):
    """Background thread for SerpAPI fashion search."""

    started = pyqtSignal()
    finished = pyqtSignal(dict)   # {"suggestions": [...], "references": [...]}
    error = pyqtSignal(str)

    def __init__(self, items: list[dict], style_tags: list[str], parent=None):
        super().__init__(parent)
        self._items = items
        self._style_tags = style_tags

    def run(self):
        from models.search_client import SearchClient

        self.started.emit()

        try:
            client = SearchClient()
            result = client.search(self._items, self._style_tags)
            self.finished.emit(result)
        except Exception as e:
            logger.exception("Search worker failed")
            # Don't emit error — search failure is non-critical, return empty
            self.finished.emit({"suggestions": [], "references": []})
