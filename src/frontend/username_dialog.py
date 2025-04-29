from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QFrame)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from api import create_user

class UsernameDialog(QDialog):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.setup_ui()
        self.setup_animations()
        self.setup_styles()
        
    def setup_ui(self):
        self.setWindowTitle("Добро пожаловать")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Основной контейнер
        self.container = QFrame()
        self.container.setObjectName("mainContainer")
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Логотип
        self.logo = QLabel()
        self.logo.setPixmap(QPixmap("assets/logo.png").scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo.setAlignment(Qt.AlignCenter)
        
        # Заголовок
        self.title = QLabel("Введите ваше имя")
        self.title.setObjectName("titleLabel")
        self.title.setAlignment(Qt.AlignCenter)
        
        # Поле ввода
        self.username_input = QLineEdit()
        self.username_input.setObjectName("nameInput")
        self.username_input.setPlaceholderText("Как вас зовут?")
        self.username_input.setAlignment(Qt.AlignCenter)
        
        # Кнопка
        self.submit_btn = QPushButton("Начать")
        self.submit_btn.setObjectName("submitButton")
        self.submit_btn.clicked.connect(self.handle_submit)
        
        # Собираем интерфейс
        layout.addWidget(self.logo)
        layout.addWidget(self.title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.submit_btn)
        
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.container)
        self.layout().setContentsMargins(0, 0, 0, 0)
    
    def setup_animations(self):
        # Анимация появления
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(300)
        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)
        
        # Анимация встряски при ошибке
        self.shake_anim = QPropertyAnimation(self.container, b"pos")
        self.shake_anim.setDuration(500)
        self.shake_anim.setEasingCurve(QEasingCurve.InOutQuad)
        
    def setup_styles(self):
        self.setStyleSheet("""
            #mainContainer {
                background-color: #ffffff;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            }
            
            #titleLabel {
                font-family: 'Segoe UI';
                font-size: 24px;
                font-weight: 600;
                color: #333333;
                margin-bottom: 10px;
            }
            
            #nameInput {
                font-family: 'Segoe UI';
                font-size: 16px;
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                background-color: #f9f9f9;
                color: #333333;
            }
            
            #nameInput:focus {
                border-color: #4a90e2;
                background-color: #ffffff;
            }
            
            #submitButton {
                font-family: 'Segoe UI';
                font-size: 16px;
                font-weight: 500;
                color: white;
                background-color: #4a90e2;
                padding: 12px;
                border: none;
                border-radius: 10px;
                min-width: 120px;
            }
            
            #submitButton:hover {
                background-color: #3a7bc8;
            }
            
            #submitButton:pressed {
                background-color: #2a5a9c;
            }
        """)
        
        # Устанавливаем шрифты
        font = QFont("Segoe UI", 12)
        self.username_input.setFont(font)
        self.submit_btn.setFont(font)
        
        title_font = QFont("Segoe UI", 24)
        title_font.setWeight(QFont.DemiBold)
        self.title.setFont(title_font)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.opacity_anim.start()
    
    def handle_submit(self):
        username = self.username_input.text().strip()
        if not username:
            self.shake_dialog()
            return
            
        user_data = create_user(username)
        if user_data:
            self.on_success(username)
        else:
            self.shake_dialog()
    
    def shake_dialog(self):
        """Анимация встряски при ошибке"""
        start_pos = self.container.pos()
        self.shake_anim.setKeyValues([
            (0.0, start_pos),
            (0.2, start_pos + QPoint(15, 0)),
            (0.4, start_pos + QPoint(-15, 0)),
            (0.6, start_pos + QPoint(10, 0)),
            (0.8, start_pos + QPoint(-10, 0)),
            (1.0, start_pos)
        ])
        self.shake_anim.start()
    
    def mousePressEvent(self, event):
        """Перемещение окна за любую область"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Перемещение окна"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPos() - self.drag_position)
            event.accept()