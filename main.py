import sys
import requests
import json
import threading
import markdown  # Добавляем библиотеку для обработки markdown
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
        self.chat_area.append(f"<b>Вы:</b> {message}")
        self.input_field.clear()
        self.status_bar.showMessage("Отправка запроса...")

        # Запускаем запрос к API в отдельном потоке
        thread = threading.Thread(target=self.get_deepseek_response, args=(message,), daemon=True)
        thread.start()

    def format_response(self, text):
        # Обработка специальных символов
        text = text.replace("\\n", "<br>")  # Заменяем \n на перенос строки в HTML
        text = text.replace("\\t", "    ")  # Заменяем \t на 4 пробела
        text = text.strip()  # Удаляем лишние пробелы в начале и конце

        # Преобразуем markdown в HTML
        try:
            html_text = markdown.markdown(text)
            return html_text
        except Exception as e:
            print(f"Markdown conversion error: {e}")
            return text  # Если markdown не сработал, возвращаем текст как есть

    def get_deepseek_response(self, message):
        # Добавляем сообщение в историю
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
            bot_response = response.json()["choices"][0]["message"]["content"]
            print(f"Parsed response: {bot_response}")

            # Форматируем ответ
            formatted_response = self.format_response(bot_response)

            # Добавляем ответ бота в историю
            self.conversation_history.append({"role": "assistant", "content": bot_response})

            # Отображаем отформатированный ответ
            self.chat_area.append(f"<b>Чат-бот:</b>")
            self.chat_area.insertHtml(formatted_response + "<br>")
            self.status_bar.showMessage("Подключено к DeepSeek API")
        except Exception as e:
            print(f"Exception occurred: {str(e)}")
            self.chat_area.append(f"<b>Ошибка:</b> {str(e)}")
            self.status_bar.showMessage("Ошибка подключения")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatBotWindow()
    window.show()
    sys.exit(app.exec())