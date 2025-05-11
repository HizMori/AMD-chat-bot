import sys
import requests
import json
import threading
import markdown
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextBrowser, QLineEdit, QPushButton, QFrame, QLabel, QStatusBar)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QKeyEvent, QIcon

class ChatBotWindow(QMainWindow):
    update_chat_signal = pyqtSignal(str)
    update_status_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMD ChatBot Support")
        self.setGeometry(100, 100, 800, 600)

        # Убираем стандартный заголовок
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background-color: rgba(37, 37, 37, 200);")

        self.conversation_history = [
            {"role": "system", "content": "Вы — технический помощник AMD. Отвечайте на вопросы о продуктах Ryzen и Radeon. Если нужно предоставить ссылку, используйте Markdown-формат, например [AMD](https://www.amd.com)."}
        ]

        self.update_chat_signal.connect(self.update_chat_area)
        self.update_status_signal.connect(self.update_status_bar)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Кастомная тёмная полоска с кнопками
        title_bar = QFrame()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet("background-color: #1E1E1E; border: none;")
        self.title_bar = title_bar  # Сохраняем для перетаскивания
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(5, 0, 5, 0)
        title_bar_layout.setSpacing(0)

        title_bar_layout.addStretch()  # Размещаем кнопки справа

        # Кнопка сворачивания с эффектом наведения
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
        title_bar_layout.addWidget(minimize_button)

        # Кнопка разворачивания/нормального режима с эффектом наведения
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
        title_bar_layout.addWidget(self.maximize_button)
        
        # Кнопка закрытия с эффектом наведения
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

        main_layout.addWidget(title_bar)

        # Существующая верхняя панель (top_bar) без крестика
        top_bar = QFrame()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background-color: #1E1E1E !important; border-bottom: 1px solid #444;")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.addWidget(QLabel("AMD", styleSheet="color: #D32F2F; font-size: 18px; font-weight: bold; padding: 5px;"))
        top_bar_layout.addWidget(QLabel("Дом | Игры | Производительность | Smart Technology", 
                                       styleSheet="color: #AAAAAA; font-size: 14px; padding: 5px;"))
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(QLineEdit(placeholderText="Поиск", 
                                          styleSheet="background-color: #333333 !important; color: #FFFFFF; width: 150px;"))

        # Кнопка ★ с серой иконкой
        star_button = QPushButton()
        star_button.setIcon(QIcon("path/to/star_icon.png"))  # Замените на путь к серой иконке звезды
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
        top_bar_layout.addWidget(star_button)

        # Кнопка 🔔 с серой иконкой
        bell_button = QPushButton()
        bell_button.setIcon(QIcon("path/to/bell_icon.png"))  # Замените на путь к серой иконке колокольчика
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
        top_bar_layout.addWidget(bell_button)

        # Кнопка ⚙️ с серой иконкой
        settings_button = QPushButton()
        settings_button.setIcon(QIcon("path/to/settings_icon.png"))  # Замените на путь к серой иконке настроек
        settings_button.setIconSize(QSize(16, 16))
        settings_button.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none; 
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        top_bar_layout.addWidget(settings_button)

        main_layout.addWidget(top_bar)

        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)

        chat_layout.addWidget(QLabel("Чат с поддержкой AMD", 
                                    styleSheet="color: #AAAAAA; font-size: 16px; padding: 10px; background-color: #252525 !important;"))

        self.chat_area = QTextBrowser()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("background-color: #252525 !important; color: #FFFFFF; font-size: 14px; border: 1px solid #444444; a { color: #00B7EB; }")
        self.chat_area.setOpenExternalLinks(True)
        chat_layout.addWidget(self.chat_area)

        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("background-color: #333333 !important; color: #FFFFFF; padding: 5px; border-radius: 5px; border: 1px solid #555555;")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        send_button = QPushButton("Отправить")
        send_button.setStyleSheet("background-color: #D32F2F; color: #FFFFFF; padding: 5px; border-radius: 5px; border: none;")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        input_widget.setStyleSheet("background-color: #252525 !important;")
        input_widget.setLayout(input_layout)
        chat_layout.addWidget(input_widget)

        main_layout.addWidget(chat_widget)

        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("color: #AAAAAA; background-color: #1E1E1E !important;")
        self.status_bar.showMessage("Подключено к DeepSeek API")
        self.setStatusBar(self.status_bar)

    # Методы для перетаскивания окна
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.title_bar.geometry().contains(event.pos()):
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_position') and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'drag_position'):
            del self.drag_position

    # Метод для переключения между максимальным и нормальным режимами
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

        self.update_chat_signal.emit(f"<b>Вы:</b> {message}")
        self.input_field.clear()
        self.update_status_signal.emit("Отправка запроса...")

        thread = threading.Thread(target=self.get_deepseek_response, args=(message,), daemon=True)
        thread.start()

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatBotWindow()
    window.show()
    sys.exit(app.exec())