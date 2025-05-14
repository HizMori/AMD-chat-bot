import sys
import requests
import json
import threading
import markdown
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextBrowser, QLineEdit, QPushButton, QFrame, QLabel, QStatusBar,
                             QFileDialog, QMenu, QDialog, QStackedWidget, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize, QDir, QPoint, QTimer, QRect, QEvent, QPropertyAnimation, QPointF
from PyQt6.QtGui import QKeyEvent, QIcon, QCursor, QScreen, QColor

# Новый класс для кастомных всплывающих подсказок с тенью
class CustomTooltip(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            background-color: #333333; /* Тёмный фон */
            color: #AAAAAA; /* Серый текст */
            border: 1px solid #555555; /* Тонкая рамка */
            padding: 2px; /* Отступы внутри текста */
            border-radius: 3px; /* Закруглённые углы */
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(5)
        shadow.setXOffset(2)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 127))
        self.setGraphicsEffect(shadow)
        self.setWindowFlags(Qt.WindowType.ToolTip)
        self.hide()

    def show_at_position(self, pos):
        self.move(pos.x() + 15, pos.y() + 15)
        self.adjustSize()
        self.show()

class NotificationWindow(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background-color: rgba(37, 37, 37, 200); border: 1px solid #444444;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        title_bar = QFrame()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet("background-color: #1E1E1E; border: none;")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(5, 0, 5, 0)
        title_bar_layout.setSpacing(0)
        title_label = QLabel("Уведомление")
        title_label.setStyleSheet("color: #AAAAAA; font-size: 14px; padding: 5px;")
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        close_button = QPushButton("✖")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F; 
                color: #FFFFFF; 
                font-size: 12px; 
                padding: 2px 8px; 
                border: none; 
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #E04F4F;
            }
        """)
        close_button.setFixedSize(30, 20)
        close_button.clicked.connect(self.close)
        title_bar_layout.addWidget(close_button)
        layout.addWidget(title_bar)
        message_label = QLabel(message)
        message_label.setStyleSheet("color: #FFFFFF; font-size: 14px; padding: 10px;")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        self.setMinimumWidth(300)
        self.setMinimumHeight(100)
        self.adjustSize()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close)
        self.timer.start(3000)
        self.drag_position = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

class ChatBotWindow(QMainWindow):
    update_chat_signal = pyqtSignal(str)
    update_status_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMD ChatBot Support")
        self.setGeometry(100, 100, 800, 600)
        icon_path = os.path.join(os.path.dirname(__file__), "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Файл значка {icon_path} не найден!")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background-color: rgba(37, 37, 37, 200);")
        self.resizing = False
        self.resize_direction = None
        self.grip_size = 3
        self.minimum_width = 400
        self.minimum_height = 300
        self.conversation_history = [
            {"role": "system", "content": "Вы — технический помощник AMD. Отвечайте на вопросы о продуктах Ryzen и Radeon. Если нужно предоставить ссылку, используйте Markdown-формат, например [AMD](https://www.amd.com)."}
        ]
        self.message_history = []
        self.history_index = -1
        self.update_chat_signal.connect(self.update_chat_area)
        self.update_status_signal.connect(self.update_status_bar)
        self.custom_tooltips = []
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        title_bar = QFrame()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet("background-color: #1E1E1E; border: none;")
        self.title_bar = title_bar
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(5, 0, 5, 0)
        title_bar_layout.setSpacing(0)
        title_bar_layout.addStretch()
        minimize_button = QPushButton("-")
        minimize_button.setStyleSheet("""
            QPushButton {
                background-color: #333333; 
                color: #FFFFFF; 
                font-size: 12px; 
                padding: 2px 8px; 
                border: none; 
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
        minimize_button.setFixedSize(30, 20)
        minimize_button.clicked.connect(self.showMinimized)
        minimize_tooltip = CustomTooltip("Свернуть", self)
        self.custom_tooltips.append(minimize_tooltip)
        minimize_button.enterEvent = lambda event: minimize_tooltip.show_at_position(QCursor.pos())
        minimize_button.leaveEvent = lambda event: minimize_tooltip.hide()
        title_bar_layout.addWidget(minimize_button)
        self.maximize_button = QPushButton("□")
        self.maximize_button.setStyleSheet("""
            QPushButton {
                background-color: #333333; 
                color: #FFFFFF; 
                font-size: 12px; 
                padding: 2px 8px; 
                border: none; 
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
        self.maximize_button.setFixedSize(30, 20)
        self.maximize_button.clicked.connect(self.toggleMaximize)
        maximize_tooltip = CustomTooltip("Развернуть/Восстановить", self)
        self.custom_tooltips.append(maximize_tooltip)
        self.maximize_button.enterEvent = lambda event: maximize_tooltip.show_at_position(QCursor.pos())
        self.maximize_button.leaveEvent = lambda event: maximize_tooltip.hide()
        title_bar_layout.addWidget(self.maximize_button)
        close_button = QPushButton("✖")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F; 
                color: #FFFFFF; 
                font-size: 12px; 
                padding: 2px 8px; 
                border: none; 
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #E04F4F;
            }
        """)
        close_button.setFixedSize(30, 20)
        close_button.clicked.connect(self.close)
        close_tooltip = CustomTooltip("Закрыть", self)
        self.custom_tooltips.append(close_tooltip)
        close_button.enterEvent = lambda event: close_tooltip.show_at_position(QCursor.pos())
        close_button.leaveEvent = lambda event: close_tooltip.hide()
        title_bar_layout.addWidget(close_button)
        main_layout.addWidget(title_bar)
        top_bar = QFrame()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background-color: #1E1E1E !important;")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.addWidget(QLabel("AMD", styleSheet="color: #D32F2F; font-size: 18px; font-weight: bold; padding: 5px;"))
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        self.buttons = []
        button_texts = ["Дом", "Игры", "Производительность", "Smart Technology", "ИИ-помощник"]
        for i, text in enumerate(button_texts):
            button = QPushButton(text)
            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #AAAAAA;
                    font-size: 14px;
                    padding: 5px 10px;
                    border: none;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #333333;
                }
            """)
            button.clicked.connect(lambda checked, idx=i: self.set_active_screen(idx))
            nav_tooltip = CustomTooltip(text, self)
            self.custom_tooltips.append(nav_tooltip)
            button.enterEvent = lambda event, tt=nav_tooltip: tt.show_at_position(QCursor.pos())
            button.leaveEvent = lambda event, tt=nav_tooltip: tt.hide()
            button_layout.addWidget(button)
            self.buttons.append(button)
        top_bar_layout.addWidget(button_container)
        top_bar_layout.addStretch()
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Поиск")
        self.search_field.setStyleSheet("""
            QLineEdit {
                background-color: #333333 !important; 
                color: #FFFFFF; 
                width: 100px; 
                padding: 5px; 
                border: 1px solid #555555; 
                border-radius: 4px 0 0 4px;
            }
        """)
        search_layout.addWidget(self.search_field)
        search_button = QPushButton()
        icon_path = os.path.join(os.path.dirname(__file__), "search_icon.png")
        if os.path.exists(icon_path):
            search_button.setIcon(QIcon(icon_path))
        else:
            print(f"Файл иконки лупы {icon_path} не найден!")
        search_button.setIconSize(QSize(16, 16))
        search_button.setStyleSheet("""
            QPushButton {
                background-color: #333333 !important; 
                border: 1px solid #555555; 
                border-left: none; 
                border-radius: 0 4px 4px 0; 
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
        search_tooltip = CustomTooltip("Поиск", self)
        self.custom_tooltips.append(search_tooltip)
        search_button.enterEvent = lambda event: search_tooltip.show_at_position(QCursor.pos())
        search_button.leaveEvent = lambda event: search_tooltip.hide()
        search_layout.addWidget(search_button)
        top_bar_layout.addWidget(search_widget)
        star_button = QPushButton()
        icon_path = os.path.join(os.path.dirname(__file__), "star_icon.png")
        if os.path.exists(icon_path):
            star_button.setIcon(QIcon(icon_path))
        else:
            print(f"Файл иконки звезды {icon_path} не найден!")
        star_button.setIconSize(QSize(16, 16))
        star_button.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none; 
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        star_tooltip = CustomTooltip("Избранное", self)
        self.custom_tooltips.append(star_tooltip)
        star_button.enterEvent = lambda event: star_tooltip.show_at_position(QCursor.pos())
        star_button.leaveEvent = lambda event: star_tooltip.hide()
        top_bar_layout.addWidget(star_button)
        bell_button = QPushButton()
        icon_path = os.path.join(os.path.dirname(__file__), "bell_icon.png")
        if os.path.exists(icon_path):
            bell_button.setIcon(QIcon(icon_path))
        else:
            print(f"Файл иконки колокольчика {icon_path} не найден!")
        bell_button.setIconSize(QSize(16, 16))
        bell_button.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none; 
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        bell_tooltip = CustomTooltip("Уведомления", self)
        self.custom_tooltips.append(bell_tooltip)
        bell_button.enterEvent = lambda event: bell_tooltip.show_at_position(QCursor.pos())
        bell_button.leaveEvent = lambda event: bell_tooltip.hide()
        top_bar_layout.addWidget(bell_button)
        self.settings_button = QPushButton()
        icon_path = os.path.join(os.path.dirname(__file__), "settings_icon.png")
        if os.path.exists(icon_path):
            self.settings_button.setIcon(QIcon(icon_path))
        else:
            print(f"Файл иконки настроек {icon_path} не найден!")
        self.settings_button.setIconSize(QSize(16, 16))
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none; 
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        settings_tooltip = CustomTooltip("Настройки", self)
        self.custom_tooltips.append(settings_tooltip)
        self.settings_button.enterEvent = lambda event: settings_tooltip.show_at_position(QCursor.pos())
        self.settings_button.leaveEvent = lambda event: settings_tooltip.hide()
        self.settings_menu = QMenu(self)
        self.settings_menu.setStyleSheet("""
            QMenu {
                background-color: #1E1E1E;
                color: #AAAAAA;
                border: 1px solid #444444;
            }
            QMenu::item:selected {
                background-color: #333333;
                color: #FFFFFF;
            }
        """)
        self.settings_menu.addAction("Очистить чат", self.clear_chat)
        self.settings_menu.addAction("Экспорт чата", self.export_chat)
        self.settings_button.clicked.connect(self.show_settings_menu)
        top_bar_layout.addWidget(self.settings_button)
        main_layout.addWidget(top_bar)
        self.stacked_widget = QStackedWidget()
        self.create_screens()
        main_layout.addWidget(self.stacked_widget)
        self.set_active_screen(0)
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("color: #AAAAAA; background-color: #1E1E1E !important;")
        self.status_bar.showMessage("Подключено к DeepSeek API")
        self.setStatusBar(self.status_bar)

    def create_screens(self):
        home_screen = QWidget()
        home_layout = QVBoxLayout(home_screen)
        home_layout.addWidget(QLabel("Содержимое для Дом", styleSheet="color: #FFFFFF; font-size: 16px; padding: 20px;"))
        self.stacked_widget.addWidget(home_screen)

        games_screen = QWidget()
        games_layout = QVBoxLayout(games_screen)
        games_layout.addWidget(QLabel("Содержимое для Игры", styleSheet="color: #FFFFFF; font-size: 16px; padding: 20px;"))
        self.stacked_widget.addWidget(games_screen)

        performance_screen = QWidget()
        performance_layout = QVBoxLayout(performance_screen)
        performance_layout.addWidget(QLabel("Содержимое для Производительность", styleSheet="color: #FFFFFF; font-size: 16px; padding: 20px;"))
        self.stacked_widget.addWidget(performance_screen)

        tech_screen = QWidget()
        tech_layout = QVBoxLayout(tech_screen)
        tech_layout.addWidget(QLabel("Содержимое для Smart Technology", styleSheet="color: #FFFFFF; font-size: 16px; padding: 20px;"))
        self.stacked_widget.addWidget(tech_screen)

        self.chat_widget = QWidget()
        chat_layout = QVBoxLayout(self.chat_widget)

        chat_layout.addWidget(QLabel("Чат с поддержкой AMD", 
                                    styleSheet="color: #AAAAAA; font-size: 16px; padding: 10px; background-color: #252525 !important;"))

        self.chat_area = QTextBrowser()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("""
            QTextBrowser {
                background-color: #333333 !important; /* Более светлый фон */
                color: #FFFFFF; 
                font-size: 14px; 
                border: 1px solid #444444; 
                a { color: #00B7EB; }
            }
        """)
        self.chat_area.setOpenExternalLinks(True)
        chat_area_shadow = QGraphicsDropShadowEffect(self.chat_area)
        chat_area_shadow.setBlurRadius(8)
        chat_area_shadow.setXOffset(2)
        chat_area_shadow.setYOffset(2)
        chat_area_shadow.setColor(QColor(0, 0, 0, 100))
        self.chat_area.setGraphicsEffect(chat_area_shadow)
        chat_layout.addWidget(self.chat_area)

        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #333333 !important; 
                color: #FFFFFF; 
                padding: 5px; 
                border-radius: 5px; 
                border: 1px solid #555555;
            }
        """)
        input_field_shadow = QGraphicsDropShadowEffect(self.input_field)
        input_field_shadow.setBlurRadius(8)
        input_field_shadow.setXOffset(2)
        input_field_shadow.setYOffset(2)
        input_field_shadow.setColor(QColor(0, 0, 0, 100))
        self.input_field.setGraphicsEffect(input_field_shadow)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        send_button = QPushButton("Отправить")
        shadow_effect = QGraphicsDropShadowEffect(send_button)
        shadow_effect.setBlurRadius(8)
        shadow_effect.setXOffset(2)
        shadow_effect.setYOffset(2)
        shadow_effect.setColor(QColor(0, 0, 0, 100))
        send_button.setGraphicsEffect(shadow_effect)

        send_button.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: #FFFFFF;
                padding: 5px 10px; /* Базовые отступы */
                border-radius: 5px;
                border: 1px solid #B71C1C;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #F44336;
            }
            QPushButton:pressed {
                background-color: #B71C1C;
                padding: 6px 11px 4px 9px; /* Смещение текста вниз и вправо */
            }
        """)

        # Анимация для эффекта тени
        press_animation = QPropertyAnimation(shadow_effect, b"offset")
        press_animation.setDuration(100)  # Длительность анимации в миллисекундах
        press_animation.setStartValue(QPointF(2, 2))
        press_animation.setEndValue(QPointF(-2, -2))

        blur_press_animation = QPropertyAnimation(shadow_effect, b"blurRadius")
        blur_press_animation.setDuration(100)
        blur_press_animation.setStartValue(8)
        blur_press_animation.setEndValue(4)

        release_animation = QPropertyAnimation(shadow_effect, b"offset")
        release_animation.setDuration(100)
        release_animation.setStartValue(QPointF(-2, -2))
        release_animation.setEndValue(QPointF(2, 2))

        blur_release_animation = QPropertyAnimation(shadow_effect, b"blurRadius")
        blur_release_animation.setDuration(100)
        blur_release_animation.setEndValue(8)

        def start_press_animation():
            press_animation.start()
            blur_press_animation.start()

        def start_release_animation():
            release_animation.start()
            blur_release_animation.start()

        send_button.pressed.connect(start_press_animation)
        send_button.released.connect(start_release_animation)

        send_button.clicked.connect(self.send_message)
        send_tooltip = CustomTooltip("Отправить сообщение", self)
        self.custom_tooltips.append(send_tooltip)
        send_button.enterEvent = lambda event: send_tooltip.show_at_position(QCursor.pos())
        send_button.leaveEvent = lambda event: send_tooltip.hide()
        input_layout.addWidget(send_button)
        input_widget.setStyleSheet("background-color: #252525 !important;")
        input_widget.setLayout(input_layout)
        chat_layout.addWidget(input_widget)

        self.stacked_widget.addWidget(self.chat_widget)

    def set_active_screen(self, index):
        for i, button in enumerate(self.buttons):
            if i == index:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #FFFFFF;
                        font-size: 14px;
                        padding: 5px 10px;
                        border: none;
                        text-align: left;
                        border-bottom: 2px solid #D32F2F;
                    }
                    QPushButton:hover {
                        background-color: #333333;
                    }
                """)
            else:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #AAAAAA;
                        font-size: 14px;
                        padding: 5px 10px;
                        border: none;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background-color: #333333;
                    }
                """)
        self.stacked_widget.setCurrentIndex(index)

    def get_resize_region(self, pos):
        rect = self.rect()
        grip = self.grip_size
        left = QRect(0, 0, grip, rect.height())
        right = QRect(rect.width() - grip, 0, grip, rect.height())
        top = QRect(0, 0, rect.width(), grip)
        bottom = QRect(0, rect.height() - grip, rect.width(), grip)
        top_left = QRect(0, 0, grip, grip)
        top_right = QRect(rect.width() - grip, 0, grip, grip)
        bottom_left = QRect(0, rect.height() - grip, grip, grip)
        bottom_right = QRect(rect.width() - grip, rect.height() - grip, grip, grip)
        if top_left.contains(pos):
            return "top_left"
        elif top_right.contains(pos):
            return "top_right"
        elif bottom_left.contains(pos):
            return "bottom_left"
        elif bottom_right.contains(pos):
            return "bottom_right"
        elif left.contains(pos):
            return "left"
        elif right.contains(pos):
            return "right"
        elif top.contains(pos):
            return "top"
        elif bottom.contains(pos):
            return "bottom"
        return None

    def get_screen_geometry(self):
        screen = QScreen.availableGeometry(QApplication.primaryScreen())
        return screen

    def mouseMoveEvent(self, event):
        pos = event.pos()
        resize_region = self.get_resize_region(pos)
        if resize_region == "left" or resize_region == "right":
            self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
        elif resize_region == "top" or resize_region == "bottom":
            self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
        elif resize_region == "top_left" or resize_region == "bottom_right":
            self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        elif resize_region == "top_right" or resize_region == "bottom_left":
            self.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        if self.resizing and event.buttons() == Qt.MouseButton.LeftButton:
            current_geometry = self.geometry()
            screen_geometry = self.get_screen_geometry()
            new_x = current_geometry.x()
            new_y = current_geometry.y()
            new_width = current_geometry.width()
            new_height = current_geometry.height()
            delta_x = event.globalPosition().toPoint().x() - self.resize_start_pos.x()
            delta_y = event.globalPosition().toPoint().y() - self.resize_start_pos.y()
            if "left" in self.resize_direction:
                new_width = self.resize_start_geometry.width() - delta_x
                if new_width >= self.minimum_width:
                    new_x = self.resize_start_geometry.x() + delta_x
                else:
                    new_width = self.minimum_width
                    new_x = self.resize_start_geometry.x() + (self.resize_start_geometry.width() - new_width)
                new_x = max(0, min(new_x, screen_geometry.width() - new_width))
            if "right" in self.resize_direction:
                new_width = self.resize_start_geometry.width() + delta_x
                new_width = max(self.minimum_width, min(new_width, screen_geometry.width()))
            if "top" in self.resize_direction:
                new_height = self.resize_start_geometry.height() - delta_y
                if new_height >= self.minimum_height:
                    new_y = self.resize_start_geometry.y() + delta_y
                else:
                    new_height = self.minimum_height
                    new_y = self.resize_start_geometry.y() + (self.resize_start_geometry.height() - new_height)
                new_y = max(0, min(new_y, screen_geometry.height() - new_height))
            if "bottom" in self.resize_direction:
                new_height = self.resize_start_geometry.height() + delta_y
                new_height = max(self.minimum_height, min(new_height, screen_geometry.height()))
            self.setGeometry(new_x, new_y, new_width, new_height)
            event.accept()
            return
        if hasattr(self, 'drag_position') and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            resize_region = self.get_resize_region(pos)
            if resize_region:
                self.resizing = True
                self.resize_direction = resize_region
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_geometry = self.geometry()
                event.accept()
                return
            if self.title_bar.geometry().contains(pos):
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.resize_direction = None
            if hasattr(self, 'drag_position'):
                del self.drag_position
            event.accept()

    def toggleMaximize(self):
        if self.isMaximized():
            self.showNormal()
            self.maximize_button.setText("□")
        else:
            self.showMaximized()
            self.maximize_button.setText("🗖")

    @pyqtSlot(str)
    def update_chat_area(self, text):
        if "<" in text and ">" in text:
            self.chat_area.insertHtml(text + "<br>")
        else:
            self.chat_area.append(text)

    @pyqtSlot(str)
    def update_status_bar(self, message):
        self.status_bar.showMessage(message)

    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return
        self.message_history.append(message)
        self.history_index = len(self.message_history)
        self.update_chat_signal.emit(f"<b>Вы:</b> {message}")
        self.input_field.clear()
        self.update_status_signal.emit("Отправка запроса...")
        thread = threading.Thread(target=self.get_deepseek_response, args=(message,), daemon=True)
        thread.start()

    def show_settings_menu(self):
        self.settings_menu.exec(self.settings_button.mapToGlobal(QPoint(0, self.settings_button.height())))

    def clear_chat(self):
        self.chat_area.clear()
        self.conversation_history = [
            {"role": "system", "content": "Вы — технический помощник AMD. Отвечайте на вопросы о продуктах Ryzen и Radeon. Если нужно предоставить ссылку, используйте Markdown-формат, например [AMD](https://www.amd.com)."}
        ]
        self.message_history = []
        self.history_index = -1
        notification = NotificationWindow("Чат успешно очищен!", self)
        notification.move(self.geometry().center() - notification.rect().center())
        notification.exec()

    def export_chat(self):
        chat_text = self.chat_area.toPlainText()
        if not chat_text:
            notification = NotificationWindow("Чат пуст, нечего экспортировать", self)
            notification.move(self.geometry().center() - notification.rect().center())
            notification.exec()
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить чат как", "", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(chat_text)
                notification = NotificationWindow(f"Чат успешно сохранён в\n{file_path}", self)
                notification.move(self.geometry().center() - notification.rect().center())
                notification.exec()
            except Exception as e:
                notification = NotificationWindow(f"Ошибка при сохранении:\n{str(e)}", self)
                notification.move(self.geometry().center() - notification.rect().center())
                notification.exec()

    def format_response(self, text):
        text = text.replace("\\n", "<br>")
        text = text.replace("\\t", "    ")
        text = text.strip()
        try:
            html_text = markdown.markdown(text)
            return html_text
        except Exception as e:
            print(f"Markdown conversion error: {e}")
            return text

    def get_deepseek_response(self, message):
        self.conversation_history.append({"role": "user", "content": message})
        print(f"Conversation history: {self.conversation_history}")
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": "Bearer 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",
            "Content-Type": "application/json",
            "X-Title": "AMD ChatBot Support"
        }
        data = {
            "model": "tngtech/deepseek-r1t-chimera:free",
            "messages": self.conversation_history
        }
        print(f"Sending request with data: {data}")
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
            print(f"Raw response: {response.text}")
            response.raise_for_status()
            response_data = response.json()
            bot_response = response_data["choices"][0]["message"].get("content", "")
            if not bot_response:
                bot_response = response_data["choices"][0]["message"].get("reasoning", "")
            print(f"Parsed response (content or reasoning): {bot_response}")
            if "http" not in bot_response:
                bot_response += "<br>Для дополнительной информации посетите [сайт AMD](https://www.amd.com)."
            formatted_response = self.format_response(bot_response)
            print(f"Formatted response: {formatted_response}")
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            self.update_chat_signal.emit(f"<b>Чат-бот:</b>")
            self.update_chat_signal.emit(formatted_response + "<br>")
            self.update_status_signal.emit("Подключено к DeepSeek API")
        except Exception as e:
            print(f"Exception occurred: {str(e)}")
            self.update_chat_signal.emit(f"<b>Ошибка:</b> {str(e)}")
            self.update_status_signal.emit("Ошибка подключения")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up and self.stacked_widget.currentIndex() == 4:
            if not self.message_history:
                return
            self.history_index = max(-1, self.history_index - 1)
            if 0 <= self.history_index < len(self.message_history):
                self.input_field.setText(self.message_history[self.history_index])
            event.accept()
        elif event.key() == Qt.Key.Key_Down and self.stacked_widget.currentIndex() == 4:
            if not self.message_history:
                return
            self.history_index = min(len(self.message_history), self.history_index + 1)
            if self.history_index == len(self.message_history):
                self.input_field.clear()
            else:
                self.input_field.setText(self.message_history[self.history_index])
            event.accept()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatBotWindow()
    window.show()
    sys.exit(app.exec())