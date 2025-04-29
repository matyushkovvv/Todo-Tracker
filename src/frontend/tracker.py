import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QLineEdit, QPushButton, QDateEdit,
                            QScrollArea, QCheckBox, QListWidget, QListWidgetItem,
                            QSizePolicy, QMessageBox, QFrame)
from PyQt5.QtCore import QDate, Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon
from api import add_friend_api, get_all_users, get_tasks, add_task, update_task, delete_task

class TodoTracker(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.current_date = QDate.currentDate()
        self.init_ui()
        self.load_tasks()
        
    def init_ui(self):
        self.setWindowTitle(f"Todo Tracker - {self.username}")
        self.setGeometry(100, 100, 1100, 700)
        self.setStyleSheet(self.load_styles())
        
        # Главный контейнер с разделением на две части
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        
        # Левая панель (задачи) - 70% ширины
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(15)
        
        # Заголовок задач
        header = QLabel("Мои задачи")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setStyleSheet("color: #333; margin-bottom: 10px;")
        
        # Панель с датой
        date_panel = QHBoxLayout()
        date_label = QLabel("Дата:")
        date_label.setFont(QFont("Arial", 12))
        
        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("dd MMMM yyyy")
        self.date_edit.setDate(self.current_date)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFont(QFont("Arial", 12))
        self.date_edit.dateChanged.connect(self.date_changed)
        
        date_panel.addWidget(date_label)
        date_panel.addWidget(self.date_edit)
        date_panel.addStretch()
        
        # Список задач
        self.tasks_list = QListWidget()
        self.tasks_list.setStyleSheet("""
            QListWidget {
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #eee;
                height: 50px;
            }
            QListWidget::item:selected {
                background: #f0f7ff;
            }
        """)
        self.tasks_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Панель добавления задачи
        add_panel = QHBoxLayout()
        self.new_task_input = QLineEdit()
        self.new_task_input.setPlaceholderText("Добавить новую задачу...")
        self.new_task_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        self.new_task_input.returnPressed.connect(self.add_new_task)
        
        add_btn = QPushButton("Добавить")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #4a90e2;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #3a7bc8;
            }
        """)
        add_btn.clicked.connect(self.add_new_task)
        
        add_panel.addWidget(self.new_task_input)
        add_panel.addWidget(add_btn)
        
        # Правая панель (друзья) - 30% ширины
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.StyledPanel)
        right_panel.setFixedWidth(300)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(15)
        
        # Заголовок друзей
        friends_header = QLabel("Друзья")
        friends_header.setFont(QFont("Arial", 18, QFont.Bold))
        friends_header.setStyleSheet("color: #333; margin-bottom: 10px;")
        
        # Список друзей
        self.friends_list = QListWidget()
        self.friends_list.setStyleSheet("""
            QListWidget {
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 0;
            }
        """)
        
        # Панель управления друзьями
        friends_control = QHBoxLayout()
        refresh_btn = QPushButton("Обновить")
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                border-radius: 4px;
                background: #f0f0f0;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        refresh_btn.clicked.connect(self.load_friends)
        
        friends_control.addWidget(refresh_btn)
        friends_control.addStretch()
        
        # Собираем правую панель
        right_layout.addWidget(friends_header)
        right_layout.addWidget(self.friends_list)
        right_layout.addLayout(friends_control)
        
        # Собираем левую панель
        left_layout.addWidget(header)
        left_layout.addLayout(date_panel)
        left_layout.addWidget(self.tasks_list)
        left_layout.addLayout(add_panel)
        
        # Собираем главный интерфейс
        main_layout.addWidget(left_panel, 70)  # 70% ширины
        main_layout.addWidget(right_panel, 30) # 30% ширины
        
        self.setCentralWidget(main_widget)
        self.load_friends()
    
    def load_friends(self):
        """Загрузка списка всех пользователей (кроме текущего)"""
        self.friends_list.clear()
        
        users = get_all_users()
        if not users:  # Если None или пустой список
            item = QListWidgetItem("Не удалось загрузить пользователей")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.friends_list.addItem(item)
            return
        
        # Получаем и нормализуем текущего пользователя
        current_user = None
        if hasattr(self, 'user_data') and isinstance(self.user_data, dict):
            current_user = {
                'id': str(self.user_data.get('_id', '')),
                'username': self.user_data.get('username', '').strip().lower()
            }
        else:
            current_username = self.username.strip().lower()
        
        for user in users:
            # Обрабатываем разные форматы данных
            user_data = {}
            if isinstance(user, dict):
                user_data = {
                    'id': str(user.get('_id', '')),
                    'username': user.get('username', '').strip()
                }
            elif isinstance(user, str):
                user_data = {
                    'id': '',
                    'username': user.strip()
                }
            
            # Пропускаем некорректные данные
            if not user_data.get('username'):
                continue
                
            # Проверяем, что это не текущий пользователь
            is_current_user = False
            if current_user:
                # Сравниваем по ID если есть
                if user_data['id'] and current_user['id']:
                    is_current_user = user_data['id'] == current_user['id']
                # Иначе сравниваем по username
                if not is_current_user:
                    is_current_user = (user_data['username'].lower() == current_user['username'])
            else:
                is_current_user = (user_data['username'].lower() == current_username)
            
            if is_current_user:
                continue
                
            # Создаем элемент интерфейса
            item = QListWidgetItem()
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(10, 5, 10, 5)
            
            # Аватар
            avatar = QLabel(user_data['username'][0].upper())
            avatar.setAlignment(Qt.AlignCenter)
            avatar.setStyleSheet("""
                background: #4a90e2;
                color: white;
                font-weight: bold;
                border-radius: 15px;
                min-width: 30px;
                max-width: 30px;
                min-height: 30px;
                max-height: 30px;
            """)
            
            # Имя пользователя
            name_label = QLabel(user_data['username'])
            name_label.setStyleSheet("font-size: 14px;")
            
            # Кнопка добавления
            add_btn = QPushButton("Добавить")
            add_btn.setProperty('user_id', user_data['id'])
            add_btn.setProperty('username', user_data['username'])
            add_btn.setFixedSize(80, 30)
            add_btn.setStyleSheet("""
                QPushButton {
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #3e8e41;
                }
                QPushButton:disabled {
                    background: #cccccc;
                }
            """)
            
            # Активируем кнопку только если есть ID
            if user_data['id']:
                add_btn.clicked.connect(
                    lambda _, uid=user_data['id'], uname=user_data['username']: 
                    self.add_friend(uname)
                )
            else:
                add_btn.setEnabled(False)
            
            layout.addWidget(avatar)
            layout.addWidget(name_label)
            layout.addStretch()
            layout.addWidget(add_btn)
            
            item.setSizeHint(widget.sizeHint())
            self.friends_list.addItem(item)
            self.friends_list.setItemWidget(item, widget)

    def add_friend(self, friend_username):
        """Добавление друга с обработкой через API"""
        # 1. Получаем данные обоих пользователей
        users = get_all_users()
        if not users:
            QMessageBox.warning(self, "Ошибка", "Не удалось получить список пользователей")
            return
        
        # 2. Находим ID обоих пользователей
        current_user = None
        friend_user = None
        
        for user in users:
            if user['username'] == self.username:
                current_user = user
            elif user['username'] == friend_username:
                friend_user = user
        
        if not current_user or not friend_user:
            return
        
        # 3. Проверяем, что это не попытка добавить самого себя
        if current_user['_id'] == friend_user['_id']:
            return
        
        # 4. Добавляем связь через API
        try:
            success = add_friend_api(str(current_user['_id']), str(friend_user['_id']))
            
            if success:
                self.load_friends()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить друга")
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", 
                            f"Не удалось добавить друга: {str(e)}")

    def load_styles(self):
        return """
            QMainWindow {
                background: #f5f7fa;
                font-family: Arial;
            }
            QLabel {
                color: #333;
            }
            QDateEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 8px;
                background: white;
            }
            QScrollArea {
                border: none;
            }
            QWidget#left_panel {
                border-right: 1px solid #e0e0e0;
                padding-right: 20px;
            }
        """
    
    def date_changed(self, date):
        self.current_date = date
        self.load_tasks()
    
    def load_tasks(self):
        self.tasks_list.clear()
        
        date_str = self.current_date.toString("yyyy-MM-dd")
        response = get_tasks(self.username, date_str)
        
        if not response or "tasks" not in response:
            item = QListWidgetItem("Нет задач на эту дату")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            item.setForeground(Qt.gray)
            self.tasks_list.addItem(item)
            return
            
        tasks = response["tasks"]
        if not tasks:
            item = QListWidgetItem("Нет задач на эту дату")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            item.setForeground(Qt.gray)
            self.tasks_list.addItem(item)
            return
            
        for task in tasks:
            self.add_task_item(task)
    
    def add_task_item(self, task):
        if isinstance(task, str):
            return
            
        item = QListWidgetItem()
        widget = QWidget()
        widget.setFixedHeight(50)  # Фиксированная высота элемента
        layout = QHBoxLayout(widget)
        
        # Чекбокс выполнения
        checkbox = QCheckBox()
        checkbox.setChecked(task.get('status', False))
        checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #4a90e2;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #4a90e2;
            }
        """)
        checkbox.stateChanged.connect(
            lambda state, t=task: self.toggle_task(t['task_id'], state == Qt.Checked)
        )
        
        # Текст задачи
        task_text = QLabel(task.get('text', ''))
        task_text.setWordWrap(True)
        task_text.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 5px 0;
                margin-right: 15px;
                min-width: 300px;
            }
        """)
        task_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Кнопка удаления (используем символ крестика вместо иконки)
        delete_btn = QPushButton("×")
        delete_btn.setFont(QFont("Arial", 14, QFont.Bold))
        delete_btn.setFixedSize(30, 30)
        delete_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #888;
                border-radius: 15px;
            }
            QPushButton:hover {
                background: #ffebee;
                color: #f44336;
            }
        """)
        delete_btn.clicked.connect(
            lambda _, t=task: self.delete_task(t['task_id'])
        )
        
        layout.addWidget(checkbox, 0)
        layout.addWidget(task_text, 1)  # Растягиваем текст
        layout.addWidget(delete_btn, 0, Qt.AlignRight)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(15)
        
        item.setSizeHint(widget.sizeHint())
        self.tasks_list.addItem(item)
        self.tasks_list.setItemWidget(item, widget)
        self.tasks_list.setMinimumWidth(400)
    
    def add_new_task(self):
        text = self.new_task_input.text().strip()
        if not text:
            return
            
        date_str = self.current_date.toString("yyyy-MM-dd")
        success = add_task(self.username, date_str, text)
        
        if success:
            self.new_task_input.clear()
            self.load_tasks()
    
    def toggle_task(self, task_id, completed):
        update_task(task_id, completed)
    
    def delete_task(self, task_id):
        if delete_task(task_id):
            self.load_tasks()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = TodoTracker("test_user")
    window.show()
    sys.exit(app.exec_())