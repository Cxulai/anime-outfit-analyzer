"""Main window — sequential pipeline: outfit → anime → annotate."""
import io
import os

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QComboBox, QPushButton, QLabel,
    QMenuBar, QMenu, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QDialogButtonBox, QMessageBox,
    QFileDialog, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QPixmap

from settings import get, set_
from ui.image_panel import ImagePanel
from ui.anime_panel import AnimePanel
from ui.outfit_panel import OutfitPanel
from workers.outfit_worker import OutfitWorker
from workers.anime_worker import AnimeWorker
from workers.search_worker import SearchWorker


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(420)
        self.setStyleSheet("""
            QDialog { background-color: #11111b; }
            QLabel { color: #cdd6f4; }
            QLineEdit { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; border-radius: 6px; padding: 6px; }
            QSpinBox { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; border-radius: 6px; padding: 6px; }
        """)
        layout = QFormLayout(self)
        self._api_key = QLineEdit(get("replicate_api_key") or "")
        self._api_key.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("SiliconFlow API Key:", self._api_key)
        self._search_key = QLineEdit(get("search_api_key") or "")
        self._search_key.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Search API Key:", self._search_key)
        self._export_quality = QSpinBox()
        self._export_quality.setRange(10, 100)
        self._export_quality.setValue(int(get("export_quality") or 95))
        layout.addRow("导出画质:", self._export_quality)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _save(self):
        set_("replicate_api_key", self._api_key.text())
        set_("search_api_key", self._search_key.text())
        set_("export_quality", self._export_quality.value())
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anime Outfit Analyzer — 动漫穿搭分析")
        self.resize(1200, 850)
        self.setMinimumSize(960, 700)

        self._current_image_path: str | None = None
        self._anime_pixmap: QPixmap | None = None
        self._outfit_data: dict | None = None
        self._outfit_worker = None
        self._anime_worker = None
        self._search_worker = None

        self._setup_menu()
        self._setup_ui()

    # ── Menu ──
    def _setup_menu(self):
        bar = self.menuBar()
        bar.setStyleSheet("QMenuBar { background: #11111b; color: #cdd6f4; border-bottom: 1px solid #313244; }")

        file_menu = bar.addMenu("文件")
        open_action = QAction("打开图片...", self)
        open_action.triggered.connect(self._open_image)
        file_menu.addAction(open_action)
        export_action = QAction("导出动漫图...", self)
        export_action.triggered.connect(self._export_anime)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        settings_menu = bar.addMenu("设置")
        settings_action = QAction("偏好设置...", self)
        settings_action.triggered.connect(self._open_settings)
        settings_menu.addAction(settings_action)

    # ── UI ──
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 6, 10, 10)
        root.setSpacing(8)

        # Top bar
        top_bar = QHBoxLayout()
        top_bar.addStretch()

        style_label = QLabel("动漫风格")
        style_label.setStyleSheet("color: #a6adc8; font-size: 13px; margin-right: 6px;")
        top_bar.addWidget(style_label)

        self._style_combo = QComboBox()
        self._style_combo.addItems(AnimePanel.ANIME_STYLES)
        self._style_combo.setFixedWidth(120)
        self._style_combo.setStyleSheet("""
            QComboBox {
                background: #1e1e2e; color: #cdd6f4; border: 1px solid #313244;
                border-radius: 6px; padding: 5px 10px; font-size: 13px;
            }
            QComboBox::drop-down { border: none; }
        """)
        top_bar.addWidget(self._style_combo)

        self._analyze_btn = QPushButton("开始分析")
        self._analyze_btn.clicked.connect(self._start_analysis)
        self._analyze_btn.setEnabled(False)
        self._analyze_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #cba6f7, stop:1 #f38ba8);
                color: #11111b; font-weight: bold; font-size: 14px;
                border: none; border-radius: 8px; padding: 8px 22px;
            }
            QPushButton:hover { opacity: 0.9; }
            QPushButton:disabled { background: #313244; color: #585b70; }
        """)
        top_bar.addWidget(self._analyze_btn)
        root.addLayout(top_bar)

        # Splitter: left images | right images
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: #313244; width: 2px; }")

        self._image_panel = ImagePanel()
        self._image_panel.image_loaded.connect(self._on_image_loaded)
        splitter.addWidget(self._image_panel)

        self._anime_panel = AnimePanel()
        self._anime_panel.export_requested.connect(self._export_anime)
        splitter.addWidget(self._anime_panel)

        splitter.setSizes([600, 600])
        root.addWidget(splitter, 3)

        # Bottom: outfit analysis with cropped items
        self._outfit_panel = OutfitPanel()
        self._outfit_panel.export_text_requested.connect(self._copy_analysis)
        root.addWidget(self._outfit_panel, 2)

    # ── Slots ──
    def _open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if path:
            self._image_panel.load_image(path)

    def _on_image_loaded(self, path: str):
        self._current_image_path = path
        self._analyze_btn.setEnabled(True)
        self._anime_panel.reset()
        self._outfit_panel.reset()

    def _start_analysis(self):
        if not self._current_image_path:
            return
        self._analyze_btn.setEnabled(False)
        self._analyze_btn.setText("分析中...")
        self._outfit_data = None

        # Step 1: Outfit detection FIRST
        self._outfit_panel.set_loading()
        self._outfit_worker = OutfitWorker(self._current_image_path)
        self._outfit_worker.progress.connect(lambda msg: None)
        self._outfit_worker.finished.connect(self._on_outfit_done)
        self._outfit_worker.error.connect(self._on_outfit_error)
        self._outfit_worker.start()

    def _on_outfit_done(self, data: dict):
        self._outfit_data = data
        style = self._style_combo.currentText()

        # Step 2: Anime conversion
        self._anime_panel.show_loading()
        self._anime_worker = AnimeWorker(self._current_image_path, style)
        self._anime_worker.finished.connect(self._on_anime_done)
        self._anime_worker.error.connect(self._on_anime_error)
        self._anime_worker.start()

    def _on_outfit_error(self, msg: str):
        self._outfit_panel.set_error(msg)
        self._analyze_btn.setText("开始分析")
        self._analyze_btn.setEnabled(True)

    def _on_anime_done(self, pixmap: QPixmap):
        # Step 3: Annotate + extract
        from PIL import Image
        from models.annotation import annotate_image, crop_items

        if self._outfit_data and self._outfit_data.get("items"):
            items = self._outfit_data["items"]
            # Save pixmap to bytes via QBuffer
            from PyQt6.QtCore import QBuffer
            qbuf = QBuffer()
            qbuf.open(QBuffer.OpenModeFlag.ReadWrite)
            pixmap.save(qbuf, "PNG")
            anime_img = Image.open(io.BytesIO(qbuf.data().data())).convert("RGB")
            qbuf.close()

            # Annotate
            annotated = annotate_image(anime_img, items)
            abuf = io.BytesIO()
            annotated.save(abuf, "PNG")
            apix = QPixmap()
            apix.loadFromData(abuf.getvalue(), "PNG")
            self._anime_panel.set_result(apix)

            # Crop items
            crops = crop_items(anime_img, items)
            crop_pixmaps = []
            for crop_img in crops:
                if crop_img is None:
                    crop_pixmaps.append(None)
                    continue
                cbuf = io.BytesIO()
                crop_img.save(cbuf, "PNG")
                cpix = QPixmap()
                cpix.loadFromData(cbuf.getvalue(), "PNG")
                crop_pixmaps.append(cpix)
            self._outfit_panel.set_crops(crop_pixmaps)
        else:
            self._anime_panel.set_result(pixmap)

        # Step 4: Show outfit data + search
        if self._outfit_data:
            self._outfit_panel.set_analysis(self._outfit_data)
            items = self._outfit_data.get("items", [])
            tags = self._outfit_data.get("tags", [])
            self._search_worker = SearchWorker(items, tags)
            self._search_worker.finished.connect(self._on_search_done)
            self._search_worker.start()

        self._analyze_btn.setText("开始分析")
        self._analyze_btn.setEnabled(True)

    def _on_anime_error(self, msg: str):
        self._anime_panel.set_error(msg)
        if self._outfit_data:
            self._outfit_panel.set_analysis(self._outfit_data)
        self._analyze_btn.setText("开始分析")
        self._analyze_btn.setEnabled(True)

    def _on_search_done(self, data: dict):
        suggestions = data.get("suggestions", [])
        refs = data.get("references", [])
        self._outfit_panel.set_suggestions(suggestions, refs)

    def _export_anime(self):
        pix = self._anime_panel.current_pixmap
        if pix is None:
            QMessageBox.information(self, "提示", "还没有动漫化结果")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出动漫图", "anime_result.png",
            "PNG (*.png);;JPEG (*.jpg)"
        )
        if path:
            pix.save(path)
            QMessageBox.information(self, "导出成功", f"已保存到:\n{path}")

    def _copy_analysis(self):
        text = self._outfit_panel.get_analysis_text()
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)

    def _open_settings(self):
        SettingsDialog(self).exec()
