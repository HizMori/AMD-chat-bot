import sys
import requests
import json
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QLineEdit, QPushButton, QFrame, QLabel, QStatusBar)
from PyQt6.QtCore import Qt

class ChatBotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMD ChatBot Support")
        self.setGeometry(100, 100, 900, 600)

        # Инициализация истории диалога
        self.conversation_history = [
            {"role": "system", "content": "Вы — технический помощник AMD. Отвечайте на вопросы о продуктах Ryzen и Radeon."}
        ]

        # Главный макет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Боковая панель (в стиле AMD Software)
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("background-color: #2A2A2A; border-right: 1px solid #444;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.addWidget(QLabel("AMD Support", styleSheet="color: #D32F2F; font-size: 18px; font-weight: bold;"))
        sidebar_layout.addWidget(QLabel("Chat Support", styleSheet="color: #FFFFFF; padding: 10px;"))
        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar)

        # Основная область
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Заголовок чата
        content_layout.addWidget(QLabel("Chat with AMD Support", styleSheet="color: #FFFFFF; font-size: 16px; padding: 5px;"))

        # Область чата
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("background-color: #252525; color: #FFFFFF; font-size: 14px; border: 1px solid #444444;")
        content_layout.addWidget(self.chat_area)

        # Панель ввода
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)

        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("background-color: #333333; color: #FFFFFF; padding: 5px; border-radius: 5px; border: 1px solid #555555;")
        input_layout.addWidget(self.input_field)

        send_button = QPushButton("Send")
        send_button.setStyleSheet("background-color: #D32F2F; color: #FFFFFF; padding: 5px; border-radius: 5px; border: none;")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)

        input_widget.setLayout(input_layout)
        content_layout.addWidget(input_widget)

        main_layout.addWidget(content_widget)

        # Добавляем статусную строку
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("color: #AAAAAA;")
        self.status_bar.showMessage("Подключено к DeepSeek API")
        self.setStatusBar(self.status_bar)

    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return

        # Отображаем сообщение пользователя
        self.chat_area.append(f"Вы: {message}")
        self.input_field.clear()
        self.status_bar.showMessage("Отправка запроса...")

        # Запускаем запрос к API в отдельном потоке
        threading.Thread(target=self.get_deepseek_response, args=(message,)).start()

    def get_deepseek_response(self, message):
        # Добавляем сообщение в историю
        self.conversation_history.append({"role": "user", "content": message})

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": "Bearer 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",  # Замените на ваш ключ OpenRouter
            "Content-Type": "application/json",
            "X-Title": "AMD ChatBot Support"  # Название вашего приложения (опционально)
        }
        data = {
            "model": "tngtech/deepseek-r1t-chimera:free",
            "messages": self.conversation_history
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
            print(response.text)
            response.raise_for_status()
            bot_response = response.json()["choices"][0]["message"]["content"]

            # Добавляем ответ бота в историю
            self.conversation_history.append({"role": "assistant", "content": bot_response})

            # Отображаем ответ
            self.chat_area.append(f"Чат-бот: {bot_response}")
            self.status_bar.showMessage("Подключено к DeepSeek API")
        except Exception as e:
            self.chat_area.append(f"Ошибка: {str(e)}")
            self.status_bar.showMessage("Ошибка подключения")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatBotWindow()
    window.show()
    sys.exit(app.exec())