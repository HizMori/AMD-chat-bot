import sys
import requests
import json
import threading
import markdown
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QLineEdit, QPushButton, QFrame, QLabel, QStatusBar)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot

class ChatBotWindow(QMainWindow):
    update_chat_signal = pyqtSignal(str)
    update_status_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AMD ChatBot Support")
        self.setGeometry(100, 100, 800, 600)

        self.setStyleSheet("background-color: rgba(37, 37, 37, 200);")
        self.setWindowOpacity(0.95)

        self.conversation_history = [
            {"role": "system", "content": "Вы — технический помощник AMD. Отвечайте на вопросы о продуктах Ryzen и Radeon."}
        ]

        self.update_chat_signal.connect(self.update_chat_area)
        self.update_status_signal.connect(self.update_status_bar)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        top_bar = QFrame()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background-color: #1E1E1E; border-bottom: 1px solid #444;")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.addWidget(QLabel("AMD", styleSheet="color: #D32F2F; font-size: 18px; font-weight: bold; padding: 5px;"))
        top_bar_layout.addWidget(QLabel("Дом | Игры | Производительность | Smart Technology", 
                                       styleSheet="color: #AAAAAA; font-size: 14px; padding: 5px;"))
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(QLineEdit(placeholderText="Поиск", 
                                          styleSheet="background-color: #333333; color: #FFFFFF; width: 150px;"))
        top_bar_layout.addWidget(QLabel("★", styleSheet="color: #AAAAAA; padding: 5px;"))
        top_bar_layout.addWidget(QLabel("🔔", styleSheet="color: #AAAAAA; padding: 5px;"))
        top_bar_layout.addWidget(QLabel("⚙️", styleSheet="color: #AAAAAA; padding: 5px;"))
        top_bar_layout.addWidget(QLabel("❌", styleSheet="color: #D32F2F; padding: 5px;"))
        main_layout.addWidget(top_bar)

        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)

        chat_layout.addWidget(QLabel("Чат с поддержкой AMD", 
                                    styleSheet="color: #FFFFFF; font-size: 16px; padding: 10px; background-color: #252525;"))

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("background-color: #252525; color: #FFFFFF; font-size: 14px; border: 1px solid #444444;")
        chat_layout.addWidget(self.chat_area)

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

        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("color: #AAAAAA; background-color: #1E1E1E;")
        self.status_bar.showMessage("Подключено к DeepSeek API")
        self.setStatusBar(self.status_bar)

    @pyqtSlot(str)
    def update_chat_area(self, text):
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
            
            # Проверяем, где находится текст: в content или в reasoning
            bot_response = response_data["choices"][0]["message"].get("content", "")
            if not bot_response:  # Если content пустой, берём из reasoning
                bot_response = response_data["choices"][0]["message"].get("reasoning", "")
            print(f"Parsed response (content or reasoning): {bot_response}")

            # Форматируем ответ
            formatted_response = self.format_response(bot_response)
            print(f"Formatted response: {formatted_response}")

            # Добавляем ответ бота в историю
            self.conversation_history.append({"role": "assistant", "content": bot_response})

            # Отправляем сигнал для обновления чата
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