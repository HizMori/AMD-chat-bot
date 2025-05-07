import sys
import requests
import json
import threading
import markdown
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QLineEdit, QPushButton, QFrame, QLabel, QStatusBar)
from PyQt6.QtCore import Qt

class ChatBotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMD ChatBot Support")
        self.setGeometry(100, 100, 800, 600)

        # Устанавливаем тёмный фон и полупрозрачность
        self.setStyleSheet("background-color: rgba(37, 37, 37, 200);")  # Тёмный полупрозрачный фон
        self.setWindowOpacity(0.95)  # Лёгкая прозрачность (0.0 - полностью прозрачно, 1.0 - непрозрачно)

        # Инициализация истории диалога
        self.conversation_history = [
            {"role": "system", "content": "Вы — технический помощник AMD. Отвечайте на вопросы о продуктах Ryzen и Radeon."}
        ]

        # Главный макет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Верхняя панель (увеличиваем высоту до 50 пикселей)
        top_bar = QFrame()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background-color: #1E1E1E; border-bottom: 1px solid #444;")
        top_bar_layout = QHBoxLayout(top_bar)
        
        # Логотип AMD (красный)
        top_bar_layout.addWidget(QLabel("AMD", styleSheet="color: #D32F2F; font-size: 18px; font-weight: bold; padding: 5px;"))
        
        # Меню (серый текст)
        top_bar_layout.addWidget(QLabel("Дом | Игры | Производительность | Smart Technology", 
                                       styleSheet="color: #AAAAAA; font-size: 14px; padding: 5px;"))
        top_bar_layout.addStretch()
        
        # Поиск и иконки (серый текст)
        top_bar_layout.addWidget(QLineEdit(placeholderText="Поиск", 
                                          styleSheet="background-color: #333333; color: #FFFFFF; width: 150px;"))
        top_bar_layout.addWidget(QLabel("★", styleSheet="color: #AAAAAA; padding: 5px;"))
        top_bar_layout.addWidget(QLabel("🔔", styleSheet="color: #AAAAAA; padding: 5px;"))
        top_bar_layout.addWidget(QLabel("⚙️", styleSheet="color: #AAAAAA; padding: 5px;"))
        top_bar_layout.addWidget(QLabel("❌", styleSheet="color: #D32F2F; padding: 5px;"))
        main_layout.addWidget(top_bar)

        # Центральная область (чат)
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)

        # Заголовок чата
        chat_layout.addWidget(QLabel("Чат с поддержкой AMD", 
                                    styleSheet="color: #FFFFFF; font-size: 16px; padding: 10px; background-color: #252525;"))

        # Область чата
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("background-color: #252525; color: #FFFFFF; font-size: 14px; border: 1px solid #444444;")
        chat_layout.addWidget(self.chat_area)

        # Панель ввода
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("background-color: #333333; color: #FFFFFF; padding: 5px; border-radius: 5px; border: 1px solid #555555;")
        input_layout.addWidget(self.input_field)
        send_button = QPushButton("Отправить")
        send_button.setStyleSheet("background-color: #D32F2F; color: #FFFFFF; padding: 5px; border-radius: 5px; border: none;")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        input_widget.setLayout(input_layout)
        chat_layout.addWidget(input_widget)

        main_layout.addWidget(chat_widget)

        # Статусная строка
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("color: #AAAAAA; background-color: #1E1E1E;")
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
        text = text.replace("\\n", "<br>")
        text = text.replace("\\t", "    ")
        text = text.strip()

        # Преобразуем markdown в HTML
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
            bot_response = response.json()["choices"][0]["message"]["content"]
            print(f"Parsed response: {bot_response}")

            # Форматируем ответ
            formatted_response = self.format_response(bot_response)
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