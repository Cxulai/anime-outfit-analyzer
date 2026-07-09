"""Outfit analysis panel — cropped clothing images + score + suggestions."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGroupBox, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap


class ClothingCropCard(QFrame):
    """Card showing a cropped clothing item image + label."""

    CATEGORY_ICONS = {
        "上衣": "👕", "下装": "👖", "鞋子": "👟",
        "配饰": "💍", "外套": "🧥", "连衣裙": "👗",
    }

    def __init__(self, item_data: dict | None = None, crop_pixmap: QPixmap | None = None, parent=None):
        super().__init__(parent)
        self._data = item_data or {}
        self._crop = crop_pixmap
        self._setup_ui()
        self.setObjectName("crop_card")

    def _setup_ui(self):
        self.setStyleSheet("""
            #crop_card {
                background-color: #1e1e2e;
                border-radius: 12px;
                border: 1px solid #313244;
            }
            #crop_card:hover { border: 1px solid #45475a; }
        """)
        self.setFixedSize(140, 180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Image
        self._img_label = QLabel()
        self._img_label.setFixedSize(124, 100)
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_label.setStyleSheet("""
            QLabel {
                background: #11111b; border-radius: 8px;
                border: 1px solid #313244;
            }
        """)
        if self._crop and not self._crop.isNull():
            scaled = self._crop.scaled(
                120, 96, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._img_label.setPixmap(scaled)
        else:
            icon = self.CATEGORY_ICONS.get(self._data.get("category", ""), "👔")
            self._img_label.setText(icon)
            self._img_label.setStyleSheet("""
                QLabel {
                    background: #11111b; border-radius: 8px;
                    border: 1px solid #313244; font-size: 36px;
                }
            """)
        layout.addWidget(self._img_label, 0, Qt.AlignmentFlag.AlignCenter)

        # Name
        name = self._data.get("name", "—")
        self._name_label = QLabel(name)
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_label.setStyleSheet("color: #cdd6f4; font-size: 13px; font-weight: bold; border: none;")
        self._name_label.setWordWrap(True)
        layout.addWidget(self._name_label)

        # Color tag
        color = self._data.get("color", "")
        if color and color != "—":
            color_tag = QLabel(color)
            color_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
            color_tag.setStyleSheet("color: #a6adc8; font-size: 11px; border: none;")
            layout.addWidget(color_tag)


class ScoreBar(QWidget):
    """Score display bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._score_label = QLabel("综合评分")
        self._score_label.setStyleSheet("color: #a6adc8; font-size: 13px;")
        layout.addWidget(self._score_label)

        self._stars = QLabel("")
        self._stars.setStyleSheet("color: #f9e2af; font-size: 18px;")
        layout.addWidget(self._stars)

        layout.addStretch()

    def set_score(self, score: int, breakdown: dict = None):
        filled = "★" * score
        empty = "☆" * (10 - score)
        self._stars.setText(filled + empty)
        tip = ""
        if breakdown:
            parts = [f"{k}:{v}" for k, v in breakdown.items()]
            tip = "  |  " + "  ".join(parts)
        self._score_label.setText(f"综合评分  {score}/10{tip}")


class OutfitPanel(QWidget):
    """Bottom panel — cropped items + score + suggestions."""

    export_text_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 4, 0, 0)
        main_layout.setSpacing(8)

        # Score bar
        self._score_bar = ScoreBar()
        main_layout.addWidget(self._score_bar)

        # Cropped items row
        self._crops_container = QWidget()
        self._crops_layout = QHBoxLayout(self._crops_container)
        self._crops_layout.setContentsMargins(0, 0, 0, 0)
        self._crops_layout.setSpacing(10)
        self._crops_layout.addStretch()

        self._crop_cards = []
        placeholders = ["上衣", "下装", "鞋子", "配饰"]
        for cat in placeholders:
            card = ClothingCropCard({"category": cat, "name": "—", "color": "—"})
            self._crop_cards.append(card)
            self._crops_layout.addWidget(card)

        self._crops_layout.addStretch()
        main_layout.addWidget(self._crops_container)

        # Suggestions + refs
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)

        # Suggestions
        suggest_group = QGroupBox("搭配建议")
        suggest_group.setStyleSheet("""
            QGroupBox {
                color: #f9e2af; font-size: 12px; font-weight: bold;
                border: 1px solid #313244; border-radius: 8px;
                padding: 12px 8px 8px 8px; margin-top: 6px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; }
        """)
        suggest_layout = QVBoxLayout(suggest_group)
        suggest_layout.setContentsMargins(6, 4, 6, 4)

        self._suggestions_label = QLabel("加载图片后开始分析...")
        self._suggestions_label.setStyleSheet("color: #6c7086; font-size: 12px; border: none;")
        self._suggestions_label.setWordWrap(True)
        suggest_layout.addWidget(self._suggestions_label)
        bottom_row.addWidget(suggest_group, 3)

        # Right side: refs + buttons
        right_col = QVBoxLayout()
        right_col.setSpacing(6)

        self._refs_label = QLabel("")
        self._refs_label.setStyleSheet("color: #89b4fa; font-size: 11px; border: none;")
        self._refs_label.setOpenExternalLinks(True)
        self._refs_label.setWordWrap(True)
        right_col.addWidget(self._refs_label)

        btn_row = QHBoxLayout()
        self._copy_btn = QPushButton("复制分析")
        self._copy_btn.clicked.connect(self.export_text_requested.emit)
        self._copy_btn.setEnabled(False)
        self._copy_btn.setStyleSheet("""
            QPushButton {
                background: #313244; color: #cdd6f4; border: none;
                border-radius: 6px; padding: 5px 12px; font-size: 12px;
            }
            QPushButton:hover { background: #45475a; }
            QPushButton:disabled { color: #585b70; }
        """)
        btn_row.addWidget(self._copy_btn)
        btn_row.addStretch()
        right_col.addLayout(btn_row)

        bottom_row.addLayout(right_col, 1)
        main_layout.addLayout(bottom_row)

    def set_loading(self):
        self._suggestions_label.setText("分析中...")
        self._suggestions_label.setStyleSheet("color: #f9e2af; font-size: 12px; border: none;")
        self._copy_btn.setEnabled(False)

    def set_crops(self, pixmaps: list):
        """Update crop cards with actual cropped images."""
        for i, pix in enumerate(pixmaps):
            if i < len(self._crop_cards):
                card = self._crop_cards[i]
                if pix and not pix.isNull():
                    scaled = pix.scaled(
                        120, 96, Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    card._img_label.setPixmap(scaled)
                    card._img_label.setStyleSheet("""
                        QLabel {
                            background: #11111b; border-radius: 8px;
                            border: 1px solid #313244;
                        }
                    """)
                else:
                    icon = card.CATEGORY_ICONS.get(card._data.get("category", ""), "👔")
                    card._img_label.setText(icon)
                    card._img_label.setStyleSheet("""
                        QLabel {
                            background: #11111b; border-radius: 8px;
                            border: 1px solid #313244; font-size: 36px;
                        }
                    """)

    def set_analysis(self, data: dict):
        items = data.get("items", [])
        score = data.get("score", 0)
        breakdown = data.get("score_breakdown", {})

        self._score_bar.set_score(score, breakdown)

        for i, item in enumerate(items):
            if i < len(self._crop_cards):
                card = self._crop_cards[i]
                card._data = item
                card._name_label.setText(item.get("name", "—"))
                card.show()

        for i in range(len(items), len(self._crop_cards)):
            self._crop_cards[i].hide()

        self._copy_btn.setEnabled(True)

    def set_suggestions(self, suggestions: list[str], refs: list[dict]):
        if suggestions:
            text = "\n".join(f"• {s}" for s in suggestions)
            self._suggestions_label.setText(text)
            self._suggestions_label.setStyleSheet("color: #cdd6f4; font-size: 12px; border: none;")

        if refs:
            links = "  |  ".join(
                f'<a href="{r["url"]}" style="color:#89b4fa;">{r.get("title", "链接")}</a>'
                for r in refs[:3]
            )
            self._refs_label.setText(f"参考 {links}")

    def set_error(self, msg: str):
        self._suggestions_label.setText(f"分析失败: {msg}")
        self._suggestions_label.setStyleSheet("color: #f38ba8; font-size: 12px; border: none;")

    def reset(self):
        self._score_bar.set_score(0)
        self._suggestions_label.setText("加载图片后开始分析...")
        self._suggestions_label.setStyleSheet("color: #6c7086; font-size: 12px; border: none;")
        self._refs_label.setText("")
        self._copy_btn.setEnabled(False)
        for i, card in enumerate(self._crop_cards):
            card.show()
            card._data = {"category": card._data.get("category", "—"), "name": "—", "color": "—"}
            card._name_label.setText("—")
            icon = card.CATEGORY_ICONS.get(card._data.get("category", ""), "👔")
            card._img_label.setText(icon)
            card._img_label.setStyleSheet("""
                QLabel {
                    background: #11111b; border-radius: 8px;
                    border: 1px solid #313244; font-size: 36px;
                }
            """)

    def get_analysis_text(self) -> str:
        parts = []
        for card in self._crop_cards:
            if not card.isVisible():
                continue
            d = card._data
            parts.append(f"{d.get('category', '')}: {d.get('name', '')} ({d.get('color', '')})")
        return "\n".join(parts)
