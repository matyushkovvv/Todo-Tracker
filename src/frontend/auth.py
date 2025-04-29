from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
                            QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt
from api import login_user, register_user
from styles import auth_style

class AuthWindow(QWidget):
    def __init__(self, on_success_callback):
        super().__init__()
        self.on_success = on_success_callback
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Авторизация")
        self.setFixedSize(400, 300)
        self.setStyleSheet(auth_style)
        
        self.stacked = QStackedWidget()
        
        # Форма авторизации
        self.login_form = self.create_login_form()
        # Форма регистрации
        self.register_form = self.create_register_form()
        
        self.stacked.addWidget(self.login_form)
        self.stacked.addWidget(self.register_form)
        
        layout = QVBoxLayout()
        layout.addWidget(self.stacked)
        self.setLayout(layout)
    
    def create_login_form(self):
        form = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Вход в систему")
        title.setAlignment(Qt.AlignCenter)
        
        self.login_input = QLineEdit(placeholderText="Логин")
        self.password_input = QLineEdit(placeholderText="Пароль", echoMode=QLineEdit.Password)
        
        login_btn = QPushButton("Войти")
        login_btn.clicked.connect(self.handle_login)
        
        register_btn = QPushButton("Регистрация")
        register_btn.clicked.connect(lambda: self.stacked.setCurrentIndex(1))
        
        layout.addWidget(title)
        layout.addWidget(self.login_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_btn)
        layout.addWidget(register_btn)
        
        form.setLayout(layout)
        return form
    
    def create_register_form(self):
        form = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Регистрация")
        title.setAlignment(Qt.AlignCenter)
        
        self.reg_username = QLineEdit(placeholderText="Имя пользователя")
        self.reg_login = QLineEdit(placeholderText="Логин")
        self.reg_password = QLineEdit(placeholderText="Пароль", echoMode=QLineEdit.Password)
        self.reg_confirm = QLineEdit(placeholderText="Подтвердите пароль", echoMode=QLineEdit.Password)
        
        register_btn = QPushButton("Зарегистрироваться")
        register_btn.clicked.connect(self.handle_register)
        
        back_btn = QPushButton("Назад")
        back_btn.clicked.connect(lambda: self.stacked.setCurrentIndex(0))
        
        layout.addWidget(title)
        layout.addWidget(self.reg_username)
        layout.addWidget(self.reg_login)
        layout.addWidget(self.reg_password)
        layout.addWidget(self.reg_confirm)
        layout.addWidget(register_btn)
        layout.addWidget(back_btn)
        
        form.setLayout(layout)
        return form
    
    def handle_login(self):
        login = self.login_input.text()
        password = self.password_input.text()
        
        user_id = login_user(login, password)
        if user_id:
            self.on_success(user_id)
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
    
    def handle_register(self):
        if self.reg_password.text() != self.reg_confirm.text():
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return
            
        success = register_user(
            self.reg_username.text(),
            self.reg_login.text(),
            self.reg_password.text()
        )
        
        if success:
            QMessageBox.information(self, "Успех", "Регистрация прошла успешно!")
            self.stacked.setCurrentIndex(0)
        else:
            QMessageBox.warning(self, "Ошибка", "Такой пользователь уже существует")