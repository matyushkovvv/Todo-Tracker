import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QLineEdit, QPushButton, QDateEdit,
                            QScrollArea, QCheckBox, QListWidget, QListWidgetItem,
                            QSizePolicy, QMessageBox, QFrame, QTabWidget)
from PyQt5.QtCore import QDate, Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon
from api import add_friend_api, get_all_users, get_friend_recommendations_api, get_friends_api, get_tasks, add_task, remove_friend_api, update_task, delete_task

class TodoTracker(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        
        self.user_id = None
        users = get_all_users()
        for user in users:
            if isinstance(user, dict):
                if user.get('username', '') == self.username:
                    self.user_id = str(user.get('_id', None))

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
        
        # Создаем вкладки для друзей
        self.tabs = QTabWidget()
        
        # Вкладка с текущими друзьями
        self.friends_list = QListWidget()
        friends_tab = QWidget()
        friends_layout = QVBoxLayout(friends_tab)
        friends_layout.addWidget(self.friends_list)
        
        # Вкладка с предложенными друзьями
        self.suggested_list = QListWidget()
        suggested_tab = QWidget()
        suggested_layout = QVBoxLayout(suggested_tab)
        suggested_layout.addWidget(self.suggested_list)

        # Вкладка с рекомендациями
        self.recommendations_list = QListWidget()
        recommendations_tab = QWidget()
        recommendations_layout = QVBoxLayout(recommendations_tab)
        recommendations_layout.addWidget(self.recommendations_list)
        
        # Добавляем вкладки
        self.tabs.addTab(friends_tab, "Мои друзья")
        self.tabs.addTab(suggested_tab, "Добавить друзей")
        self.tabs.addTab(recommendations_tab, "Рекомендации")
        
        # Кнопка обновления
        refresh_btn = QPushButton("Обновить список")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        refresh_btn.clicked.connect(self.load_friends_data)
        
        # Собираем правую панель
        right_layout.addWidget(self.tabs)
        right_layout.addWidget(refresh_btn)
        
        # Собираем левую панель
        left_layout.addWidget(header)
        left_layout.addLayout(date_panel)
        left_layout.addWidget(self.tasks_list)
        left_layout.addLayout(add_panel)
        
        # Собираем главный интерфейс
        main_layout.addWidget(left_panel, 70)
        main_layout.addWidget(right_panel, 30)
        
        self.setCentralWidget(main_widget)
        self.load_friends_data()
    
    def load_friends_data(self):
        """Загрузка данных о друзьях и предложенных пользователях"""
        # Получаем текущих друзей

        friends_response = get_friends_api(self.user_id)
        current_friends = friends_response.get('friends', []) if friends_response else []
        friend_ids = {f['user_id'] for f in current_friends}
        
        # Получаем всех пользователей
        all_users = get_all_users()
        if not all_users:
            self.show_message_in_list(self.friends_list, "Не удалось загрузить друзей")
            self.show_message_in_list(self.suggested_list, "Не удалось загрузить пользователей")
            return
        
        # Разделяем на друзей и других пользователей
        friends = []
        suggested = []
    
        for user in all_users:
            if isinstance(user, dict):
                user_id = str(user.get('_id', ''))
                username = user.get('username', '').strip()
                    
                if not username or username.lower() == self.username.lower():
                    continue
                        
                if user_id in friend_ids:
                    friends.append(user)
                else:
                    suggested.append(user)
    
        # 4. Загружаем рекомендации (новый код)
        recommendations_response = get_friend_recommendations_api(self.user_id)
        recommendations = recommendations_response if recommendations_response else []
    
        # Фильтруем рекомендации - оставляем только тех, кто есть в suggested
        recommendation_ids = {rec['user_id'] for rec in recommendations}
        filtered_suggested = [user for user in suggested if str(user['_id']) not in recommendation_ids]
        
        # 5. Обогащаем рекомендации данными пользователей
        enriched_recommendations = []
        for rec in recommendations:
            user_data = next((u for u in all_users if str(u.get('_id', '')) == rec['user_id']), None)
            if user_data:
                enriched_recommendations.append({
                    **user_data,
                    'common_friends': rec.get('common_friends', 0)
                })
        
        # Отображаем друзей
        if friends:
            self.add_users_to_list(friends, self.friends_list, is_friend=True)
        else:
            self.show_message_in_list(self.friends_list, "У вас пока нет друзей")
        
        # Отображаем предложенных друзей
        if suggested:
            self.add_users_to_list(suggested, self.suggested_list, is_friend=False)
        else:
            self.show_message_in_list(self.suggested_list, "Нет пользователей для добавления")

        if enriched_recommendations:
            self.add_recommendations_to_list(enriched_recommendations)
        else:
            self.show_message_in_list(self.recommendations_list, "Нет рекомендаций")
    

    def add_recommendations_to_list(self, recommendations):
        """Добавляет рекомендации в список с дополнительной информацией"""
        self.recommendations_list.clear()
        
        for rec in recommendations:
            item = QListWidgetItem()
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(10, 5, 10, 5)

            # Аватар
            avatar = QLabel(rec['username'][0].upper())
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

            # Информация о пользователе
            info_layout = QVBoxLayout()
            name_label = QLabel(rec['username'])
            name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            
            common_label = QLabel(f"Общих друзей: {rec.get('common_friends', 0)}")
            common_label.setStyleSheet("font-size: 12px; color: #666;")
            
            info_layout.addWidget(name_label)
            info_layout.addWidget(common_label)
            layout.addWidget(avatar)
            layout.addLayout(info_layout)
            layout.addStretch()

            # Кнопка добавления
            add_btn = QPushButton("Добавить")
            add_btn.setStyleSheet("""
                QPushButton {
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background: #3e8e41;
                }
            """)
            add_btn.clicked.connect(lambda _, uid=rec['_id'], uname=rec['username']: 
                                self.add_friend(uid))
            
            layout.addWidget(add_btn)
            item.setSizeHint(widget.sizeHint())
            self.recommendations_list.addItem(item)
            self.recommendations_list.setItemWidget(item, widget)

    def show_message_in_list(self, list_widget, message):
        """Показывает сообщение в списке"""
        list_widget.clear()
        item = QListWidgetItem(message)
        item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
        list_widget.addItem(item)
    
    def add_users_to_list(self, users, list_widget, is_friend):
        """Добавляет пользователей в список с соответствующими кнопками"""
        list_widget.clear()
        
        for user in users:
            item = QListWidgetItem()
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(10, 5, 10, 5)

            # Аватар
            avatar = QLabel(user['username'][0].upper())
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
            name_label = QLabel(user['username'])
            name_label.setStyleSheet("font-size: 14px;")

            layout.addWidget(avatar)
            layout.addWidget(name_label)
            layout.addStretch()

            # Кнопка (разная для друзей и других пользователей)
            if is_friend:
                btn = QPushButton("Удалить")
                btn.setStyleSheet("""
                    QPushButton {
                        background: #f44336;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                        padding: 5px 10px;
                    }
                    QPushButton:hover {
                        background: #d32f2f;
                    }
                """)
                btn.clicked.connect(lambda _, uid=user['_id']: self.remove_friend(uid))
            else:
                btn = QPushButton("Добавить")
                btn.setStyleSheet("""
                    QPushButton {
                        background: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                        padding: 5px 10px;
                    }
                    QPushButton:hover {
                        background: #3e8e41;
                    }
                """)
                btn.clicked.connect(lambda _, uid=user['_id'], uname=user['username']: self.add_friend(uid))

            btn.setFixedSize(80, 30)
            layout.addWidget(btn)

            item.setSizeHint(widget.sizeHint())
            list_widget.addItem(item)
            list_widget.setItemWidget(item, widget)
    
    def add_friend(self, friend_id):
        """Добавление пользователя в друзья"""
        try:
            success = add_friend_api(self.user_id, friend_id)
            if success:
                self.load_friends_data()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить друга")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить друга: {str(e)}")
    
    def remove_friend(self, friend_id):
        """Удаление пользователя из друзей"""

        try:
            success = remove_friend_api(self.user_id, friend_id)
            if success:
                self.load_friends_data()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить друга")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось удалить друга: {str(e)}")


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