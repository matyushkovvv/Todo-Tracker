import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QLineEdit, QPushButton, QDateEdit,
                            QScrollArea, QCheckBox, QListWidget, QListWidgetItem,
                            QSizePolicy, QMessageBox, QFrame, QTabWidget,
                            QStackedWidget, QDialog, QComboBox, QGroupBox)
from PyQt5.QtCore import QDate, Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon
import requests

from config import BASE_URL
from api import get_all_users, get_friend_recommendations_api, get_workspace_stats, increment_workspace_stat

class CreateWorkspaceDialog(QDialog):
    def __init__(self, parent=None, friends=None):
        super().__init__(parent)
        self.setWindowTitle("Создать рабочую область")
        self.setModal(True)
        self.setFixedSize(400, 400)
        
        layout = QVBoxLayout()
        
        # Название рабочей области
        name_group = QGroupBox("Название рабочей области")
        name_layout = QVBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите название...")
        name_layout.addWidget(self.name_input)
        name_group.setLayout(name_layout)
        
        # Кнопки
        button_layout = QHBoxLayout()
        create_btn = QPushButton("Создать")
        create_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(create_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addWidget(name_group)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_data(self):
        return {
            'name': self.name_input.text()
        }

class WorkspaceWidget(QWidget):
    def __init__(self, workspace, user_id, username):
        super().__init__()
        self.workspace = workspace
        self.user_id = user_id
        self.username = username
        self.current_date = QDate.currentDate()
        self.init_ui()
        self.load_tasks()

        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(30000) 


    def closeEvent(self, event):
        """Останавливаем таймер при закрытии"""
        self.stats_timer.stop()
        super().closeEvent(event)

    def format_stat_name(self, stat: str) -> str:
        """Форматирует название статистики для красивого отображения в UI"""
        # Заменяем подчеркивания на пробелы и делаем первую букву заглавной
        formatted = stat.replace('_', ' ').title()
        
        # Специальные случаи
        replacements = {
            'Ws': 'Workspace',
            'Tasks': 'Task',
            'Members': 'Member'
        }
        
        for old, new in replacements.items():
            formatted = formatted.replace(old, new)
        
        return formatted
    
    def init_ui(self):
        # Основной контейнер с прокруткой
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        main_layout = QVBoxLayout(scroll_content)  # Определяем main_layout здесь
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Заголовок рабочей области
        self.header = QLabel(f"Рабочая область: {self.workspace['name']}")
        self.header.setFont(QFont("Arial", 16, QFont.Bold))
        self.header.setStyleSheet("color: #333; margin-bottom: 10px;")
        main_layout.addWidget(self.header)

        # Панель статистики
        self.stats_panel = QFrame()
        self.stats_panel.setFrameShape(QFrame.StyledPanel)
        self.stats_panel.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
        """)
        stats_layout = QHBoxLayout(self.stats_panel)
        stats_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.addWidget(self.stats_panel)

        # Панель управления (для администраторов)
        self.access_level = self.get_user_access_level()
        if self.access_level == 'admin':
            self.manage_panel = QHBoxLayout()
            
            self.add_member_btn = QPushButton("Добавить участника")
            self.add_member_btn.setStyleSheet("""
                QPushButton {
                    background: #4CAF50;
                    color: white;
                    padding: 8px;
                    border-radius: 4px;
                }
            """)
            self.add_member_btn.clicked.connect(self.show_add_member_dialog)
            
            self.manage_panel.addWidget(self.add_member_btn)
            self.manage_panel.addStretch()
            main_layout.addLayout(self.manage_panel)

        # Область участников
        self.members_scroll = QScrollArea()
        self.members_scroll.setWidgetResizable(True)
        self.members_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 8px;
                background: white;
            }
        """)
        
        self.members_container = QWidget()
        self.members_layout = QVBoxLayout(self.members_container)
        self.members_layout.setContentsMargins(5, 5, 5, 5)
        self.members_scroll.setWidget(self.members_container)
        main_layout.addWidget(self.members_scroll)

        # Панель с датой
        self.date_panel = QHBoxLayout()
        date_label = QLabel("Дата:")
        date_label.setFont(QFont("Arial", 12))
        
        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("dd MMMM yyyy")
        self.date_edit.setDate(self.current_date)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFont(QFont("Arial", 12))
        self.date_edit.dateChanged.connect(self.date_changed)
        
        self.date_panel.addWidget(date_label)
        self.date_panel.addWidget(self.date_edit)
        self.date_panel.addStretch()
        main_layout.addLayout(self.date_panel)
        
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
        main_layout.addWidget(self.tasks_list)
        
        # Панель добавления задачи (недоступна для viewer)
        if self.access_level != 'viewer':
            self.add_panel = QHBoxLayout()
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
            
            self.add_btn = QPushButton("Добавить")
            self.add_btn.setStyleSheet("""
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
            self.add_btn.clicked.connect(self.add_new_task)
            
            self.add_panel.addWidget(self.new_task_input)
            self.add_panel.addWidget(self.add_btn)
            main_layout.addLayout(self.add_panel)
        
        # Настройка основного виджета
        scroll_area.setWidget(scroll_content)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(scroll_area)
        
        # Загружаем данные
        self.update_members_list()
        self.update_stats()
        self.load_tasks()


    def update_stats(self):
        """Обновляет отображение статистики рабочей области"""
        # Очищаем текущую статистику
        for i in reversed(range(self.stats_panel.layout().count())):
            widget = self.stats_panel.layout().itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Получаем статистику
        stats = get_workspace_stats(self.workspace['_id'])
        
        if not stats:
            label = QLabel("Статистика недоступна")
            label.setStyleSheet("color: #6c757d; font-style: italic;")
            self.stats_panel.layout().addWidget(label)
            return
        
        # Добавляем статистику в панель
        for stat_name, value in stats.items():
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(5, 5, 5, 5)
            
            name_label = QLabel(self.format_stat_name(stat_name))
            name_label.setStyleSheet("font-size: 10px; color: #6c757d;")
            
            value_label = QLabel(str(value))
            value_label.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                color: #212529;
            """)
            value_label.setAlignment(Qt.AlignCenter)
            
            stat_layout.addWidget(name_label)
            stat_layout.addWidget(value_label)
            self.stats_panel.layout().addWidget(stat_widget)
        
        # Добавляем растягивающий элемент
        self.stats_panel.layout().addStretch()
    
    def date_changed(self, date):
        self.current_date = date
        self.load_tasks()
    
    def load_tasks(self):
        """Загружает только невыполненные задачи для текущей даты"""
        self.tasks_list.clear()
        
        date_str = self.current_date.toString("yyyy-MM-dd")
        response = requests.get(
            f"{BASE_URL}/workspaces/{self.workspace['_id']}/tasks?date={date_str}"
        )
        
        if response.status_code != 200:
            item = QListWidgetItem("Не удалось загрузить задачи")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            item.setForeground(Qt.gray)
            self.tasks_list.addItem(item)
            return
            
        tasks = response.json().get('tasks', [])
        
        # Фильтруем только невыполненные задачи
        incomplete_tasks = [task for task in tasks if not task.get('is_done', False)]
        
        if not incomplete_tasks:
            item = QListWidgetItem("Нет активных задач на эту дату")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            item.setForeground(Qt.gray)
            self.tasks_list.addItem(item)
            return
            
        for task in incomplete_tasks:
            self.add_task_item(task)
    
    def add_task_item(self, task):
        """Добавляет задачу в список с учетом прав доступа"""
        if not isinstance(task, dict):
            return
            
        task_id = task.get('_id') or task.get('task_id')
        if not task_id:
            return
            
        item = QListWidgetItem()
        widget = QWidget()
        widget.setFixedHeight(50)
        layout = QHBoxLayout(widget)
        
        # Чекбокс выполнения (только для editor и admin)
        if self.access_level in ['admin', 'editor']:
            checkbox = QCheckBox()
            checkbox.setChecked(False)
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
                lambda state, task_id=task_id: self.toggle_task(task_id, state == Qt.Checked)
            )
            layout.addWidget(checkbox, 0)
        
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

        if self.access_level == 'admin' or self.access_level == 'editor':
            delete_btn = QPushButton("Удалить")
            delete_btn.setFixedSize(60, 30)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background: #f44336;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #d32f2f;
                }
            """)
            delete_btn.clicked.connect(
                lambda _, task_id=task_id: self.delete_task(task_id)
            )
            layout.addWidget(delete_btn, 0, Qt.AlignRight)
        
        hide_btn = QPushButton("×")
        hide_btn.setFont(QFont("Arial", 14, QFont.Bold))
        hide_btn.setFixedSize(30, 30)
        hide_btn.setStyleSheet("""
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
        hide_btn.clicked.connect(
            lambda _, task_id=task_id: self.hide_task(task_id)
        )
    
        layout.addWidget(task_text, 1)
        # layout.addWidget(hide_btn, 0, Qt.AlignRight)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(15)
        
        item.setSizeHint(widget.sizeHint())
        self.tasks_list.addItem(item)
        self.tasks_list.setItemWidget(item, widget)

    def show_add_member_dialog(self):
        # Получаем список друзей
        response = requests.get(f"{BASE_URL}/friends/{self.user_id}")
        if response.status_code != 200:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список друзей")
            return
        
        friends_data = response.json().get('friends', [])
        
        # Получаем текущих участников рабочей области
        response = requests.get(f"{BASE_URL}/workspaces/{self.workspace['_id']}/members")
        if response.status_code != 200:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список участников")
            return
        
        current_members = [m['user_id'] for m in response.json().get('members', [])]
        
        # Фильтруем друзей, которые еще не в рабочей области
        available_friends = [
            f for f in friends_data 
            if f['user_id'] != self.user_id and f['user_id'] not in current_members
        ]
        
        dialog = AddMemberDialog(self, available_friends)
        if dialog.exec_() == QDialog.Accepted:
            selection = dialog.get_selection()
            if not selection['user_id']:
                return
                
            data = {
                "admin_id": self.user_id,
                "user_id": selection['user_id'],
                "role": selection['role']
            }
            
            response = requests.post(
                f"{BASE_URL}/workspaces/{self.workspace['_id']}/members",
                json=data
            )
            
            if response.status_code == 200:
                self.update_members_list()
                increment_workspace_stat(self.workspace['_id'], 'members_added')

    def get_user_access_level(self):
        response = requests.get(f"{BASE_URL}/workspaces/{self.workspace['_id']}/members")
        if response.status_code == 200:
            members = response.json().get('members', [])
            for member in members:
                if member['user_id'] == self.user_id:
                    return member['role']
        return 'viewer'
    

    def hide_task(self, task_id):
        """Помечает задачу как выполненную (скрывает из списка)"""
        if self.access_level not in ['admin', 'editor']:
            QMessageBox.warning(self, "Ошибка", "Недостаточно прав для выполнения этого действия")
            return
        
        confirm = QMessageBox.question(
            self,
            "Подтверждение",
            "Пометить задачу как выполненную?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                data = {
                    "user_id": self.user_id,
                    "is_done": True
                }
                
                response = requests.put(
                    f"{BASE_URL}/workspaces/{self.workspace['_id']}/tasks/{task_id}",
                    json=data
                )
                
                if response.status_code == 200:
                    self.load_tasks()  # Перезагружаем список задач
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось обновить задачу")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка соединения: {str(e)}")
    
    def update_members_list(self):
        """Обновляет список участников рабочей области с автоматической высотой"""
        # Очищаем текущий список
        for i in reversed(range(self.members_layout.count())): 
            widget = self.members_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Получаем данные участников
        try:
            response = requests.get(f"{BASE_URL}/workspaces/{self.workspace['_id']}/members")
            if response.status_code != 200:
                return
                
            members = response.json().get('members', [])
            
            users_response = requests.get(f"{BASE_URL}/users")
            if users_response.status_code != 200:
                return
                
            all_users = users_response.json().get('users', [])
            user_dict = {user['_id']: user['username'] for user in all_users}
            
            # Добавляем заголовок
            header = QLabel("Участники:")
            header.setFont(QFont("Arial", 10, QFont.Bold))
            self.members_layout.addWidget(header)
            
            # Добавляем участников
            for i, member in enumerate(members):
                username = user_dict.get(member['user_id'], "Неизвестный пользователь")
                
                member_widget = QWidget()
                member_layout = QHBoxLayout(member_widget)
                member_layout.setContentsMargins(5, 5, 5, 5)
                
                # Иконка роли
                role_icon = QLabel()
                if member['role'] == 'admin':
                    role_icon.setPixmap(QPixmap(":/icons/admin.png").scaled(16, 16))
                elif member['role'] == 'editor':
                    role_icon.setPixmap(QPixmap(":/icons/editor.png").scaled(16, 16))
                else:
                    role_icon.setPixmap(QPixmap(":/icons/viewer.png").scaled(16, 16))
                member_layout.addWidget(role_icon)
                
                # Информация о пользователе
                user_label = QLabel(f"{username} - {member['role']}")
                user_label.setWordWrap(True)
                user_label.setStyleSheet("""
                    QLabel {
                        font-size: 12px;
                        margin-left: 5px;
                        color: #333;
                    }
                """)
                user_label.setToolTip(f"{username} - {member['role']}")
                user_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                member_layout.addWidget(user_label, 1)
                
                # Кнопка удаления (только для админов)
                if self.access_level == 'admin' and member['user_id'] != self.user_id:
                    delete_btn = QPushButton("×")
                    delete_btn.setFixedSize(24, 24)
                    delete_btn.setStyleSheet("""
                        QPushButton {
                            border: none;
                            background: transparent;
                            color: #888;
                            border-radius: 12px;
                            font-weight: bold;
                            font-size: 14px;
                        }
                        QPushButton:hover {
                            background: #ffebee;
                            color: #f44336;
                        }
                    """)
                    delete_btn.clicked.connect(lambda _, uid=member['user_id']: self.remove_member(uid))
                    member_layout.addWidget(delete_btn)
                
                self.members_layout.addWidget(member_widget)
                
                # Добавляем разделитель (кроме последнего элемента)
                if i < len(members) - 1:
                    separator = QFrame()
                    separator.setFrameShape(QFrame.HLine)
                    separator.setStyleSheet("color: #eee; margin: 2px 0;")
                    self.members_layout.addWidget(separator)
            
            # Рассчитываем оптимальную высоту
            self.adjust_members_height()
            
        except Exception as e:
            print(f"Ошибка при обновлении списка участников: {str(e)}")


    def adjust_members_height(self):
        """Автоматически подстраивает высоту области участников"""
        # Рассчитываем необходимую высоту
        height = 0
        for i in range(self.members_layout.count()):
            item = self.members_layout.itemAt(i)
            if item.widget():
                height += item.widget().sizeHint().height()
        
        # Добавляем отступы (10px сверху/снизу + 5px между элементами)
        total_height = height + 20
        
        # Устанавливаем высоту с ограничением (мин 60px, макс 300px)
        new_height = max(60, min(total_height, 300))
        self.members_scroll.setFixedHeight(new_height)
        
        # Обновляем геометрию
        self.members_container.updateGeometry()
        
    def add_new_task(self):
        text = self.new_task_input.text().strip()
        if not text:
            return
            
        date_str = self.current_date.toString("yyyy-MM-dd")
        data = {
            "user_id": self.user_id,
            "text": text,
            "date": date_str
        }
        
        response = requests.post(
            f"{BASE_URL}/workspaces/{self.workspace['_id']}/tasks",
            json=data
        )
        
        if response.status_code == 201:
            self.new_task_input.clear()
            self.load_tasks()
            increment_workspace_stat(self.workspace['_id'], 'tasks_created')
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось добавить задачу")
    
    def toggle_task(self, task_id, completed):
        """Обновляет статус задачи (для чекбокса)"""
        if self.access_level not in ['admin', 'editor']:
            return
            
        try:
            data = {
                "user_id": self.user_id,
                "is_done": completed
            }
            
            response = requests.put(
                f"{BASE_URL}/workspaces/{self.workspace['_id']}/tasks/{task_id}",
                json=data
            )
            
            if response.status_code == 200:
                if completed:
                    self.load_tasks()  # Перезагружаем список, если задача выполнена
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось обновить задачу")
                self.load_tasks()  # Восстанавливаем состояние
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка соединения: {str(e)}")
            self.load_tasks()
    

    def remove_member(self, user_id):
        """Удаляет участника из рабочей области"""
        confirm = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить этого участника?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.No:
            return
        
        try:
            data = {
                "requester_id": self.user_id,
                "target_id": user_id
            }
            
            response = requests.delete(
                f"{BASE_URL}/workspaces/{self.workspace['_id']}/members",
                json=data
            )
            
            if response.status_code == 200:
                QMessageBox.information(self, "Успех", "Участник удален")
                self.update_members_list()
                increment_workspace_stat(self.workspace['_id'], 'members_removed')
            else:
                error = response.json().get('error', 'Неизвестная ошибка')
                QMessageBox.warning(self, "Ошибка", f"Не удалось удалить участника: {error}")
                
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка соединения: {str(e)}")

    def delete_task(self, task_id):
        """Удаляет задачу после подтверждения"""
        if self.access_level != 'admin':
            QMessageBox.warning(self, "Ошибка", "Только администратор может удалять задачи")
            return
        
        confirm = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить эту задачу?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.No:
            return
        
        try:
            data = {"user_id": self.user_id}
            response = requests.delete(
                f"{BASE_URL}/workspaces/{self.workspace['_id']}/tasks/{task_id}",
                json=data
            )
            
            if response.status_code == 200:
                QMessageBox.information(self, "Успех", "Задача удалена")
                self.load_tasks()  # Обновляем список задач
            else:
                error = response.json().get('error', 'Не удалось удалить задачу')
                QMessageBox.warning(self, "Ошибка", error)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка соединения: {str(e)}")

class TodoTracker(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username

        users = get_all_users()
        for user in users:
            if user['username'] == username:
                self.user_id = user['_id']

        self.current_date = QDate.currentDate()
        self.workspaces = []
        self.init_ui()
        self.load_workspaces()
        
    def init_ui(self):
        self.setWindowTitle(f"Todo Tracker - {self.username}")
        self.setGeometry(100, 100, 1100, 700)
        self.setStyleSheet(self.load_styles())
        
        # Главный контейнер с разделением на две части
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        
        # Левая панель (рабочие области) - 70% ширины
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(15)
        
        # Заголовок и кнопка создания рабочей области
        header_panel = QHBoxLayout()
        header = QLabel("Рабочие области")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setStyleSheet("color: #333; margin-bottom: 10px;")
        
        self.create_ws_btn = QPushButton("+ Создать")
        self.create_ws_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #3e8e41;
            }
        """)
        self.create_ws_btn.clicked.connect(self.show_create_workspace_dialog)
        
        header_panel.addWidget(header)
        header_panel.addStretch()
        header_panel.addWidget(self.create_ws_btn)
        
        # Список рабочих областей
        self.workspace_list = QListWidget()
        self.workspace_list.setStyleSheet("""
            QListWidget {
                background: #f5f7fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 4px;
            }
            QListWidget::item {
                background: white;
                border-radius: 6px;
                margin: 4px;
                padding: 10px;
            }
            QListWidget::item:hover {
                background: #f0f7ff;
            }
        """)
        self.workspace_list.itemClicked.connect(self.show_workspace)
        
        # Контейнер для виджета рабочей области
        self.workspace_container = QStackedWidget()
        
        # Собираем левую панель
        left_layout.addLayout(header_panel)
        left_layout.addWidget(self.workspace_list)
        left_layout.addWidget(self.workspace_container)
        
        # Правая панель (друзья) - 30% ширины
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.StyledPanel)
        right_panel.setFixedWidth(320)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(15)

        # Стиль для всех кнопок
        button_style = """
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
        """

        # Панель управления с кнопками
        control_panel = QFrame()
        control_panel.setStyleSheet("background: transparent;")
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(8)

        # Кнопки управления
        self.friends_btn = QPushButton("Мои друзья")
        self.suggested_btn = QPushButton("Добавить")
        self.recommend_btn = QPushButton("Общие")
        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setFixedSize(30, 30)

        # Применяем стили к кнопкам
        self.friends_btn.setStyleSheet(f"""
            {button_style}
            background: #5c6bc0;
            color: black;
        """)
        self.suggested_btn.setStyleSheet(f"""
            {button_style}
            background: #66bb6a;
            color: black;
        """)
        self.recommend_btn.setStyleSheet(f"""
            {button_style}
            background: #ffa726;
            color: black;
        """)
        self.refresh_btn.setStyleSheet(f"""
            {button_style}
            background: #78909c;
            color: black;
            font-size: 16px;
        """)

        # Добавляем кнопки на панель
        control_layout.addWidget(self.friends_btn)
        control_layout.addWidget(self.suggested_btn)
        control_layout.addWidget(self.recommend_btn)
        control_layout.addWidget(self.refresh_btn)

        # Создаем stacked widget для переключения между списками
        self.friends_stack = QStackedWidget()
        
        # Списки друзей
        self.friends_list = self.create_styled_list()
        self.suggested_list = self.create_styled_list()
        self.recommendations_list = self.create_styled_list()
        
        # Добавляем списки в stacked widget
        self.friends_stack.addWidget(self.friends_list)
        self.friends_stack.addWidget(self.suggested_list)
        self.friends_stack.addWidget(self.recommendations_list)

        # Подключаем кнопки к переключению
        self.friends_btn.clicked.connect(lambda: self.friends_stack.setCurrentIndex(0))
        self.suggested_btn.clicked.connect(lambda: self.friends_stack.setCurrentIndex(1))
        self.recommend_btn.clicked.connect(lambda: self.friends_stack.setCurrentIndex(2))
        self.refresh_btn.clicked.connect(self.load_friends_data)

        # Собираем правую панель
        right_layout.addWidget(control_panel)
        right_layout.addWidget(self.friends_stack)
        
        # Собираем главный интерфейс
        main_layout.addWidget(left_panel, 70)
        main_layout.addWidget(right_panel, 30)
        
        self.setCentralWidget(main_widget)
        self.load_friends_data()
    
    def load_workspaces(self):
        response = requests.get(f"{BASE_URL}/users/{self.user_id}/workspaces")
        if response.status_code == 200:
            self.workspaces = response.json().get('workspaces', [])
            self.workspace_list.clear()
            
            for ws in self.workspaces:
                item = QListWidgetItem(ws['name'])
                item.setData(Qt.UserRole, ws['_id'])
                self.workspace_list.addItem(item)
            
            if self.workspaces:
                self.show_workspace(self.workspace_list.item(0))
            else:
                
                while self.workspace_container.count() > 0:
                    widget = self.workspace_container.widget(0)
                    self.workspace_container.removeWidget(widget)
                    widget.deleteLater()

                label = QLabel("У вас нет рабочих областей. Создайте новую.")
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: #666; font-size: 14px;")
                self.workspace_container.addWidget(label)
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить рабочие области")
    
    def show_workspace(self, item):
        workspace_id = item.data(Qt.UserRole)
        workspace = next((ws for ws in self.workspaces if ws['_id'] == workspace_id), None)
        
        if workspace:
            # Удаляем предыдущий виджет, если он есть
            if self.workspace_container.count() > 0:
                old_widget = self.workspace_container.currentWidget()
                self.workspace_container.removeWidget(old_widget)
                old_widget.deleteLater()
            
            # Создаем и добавляем новый виджет рабочей области
            ws_widget = WorkspaceWidget(workspace, self.user_id, self.username)
            self.workspace_container.addWidget(ws_widget)
            self.workspace_container.setCurrentWidget(ws_widget)
    
    def show_create_workspace_dialog(self):
        dialog = CreateWorkspaceDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            data['user_id'] = self.user_id
            
            response = requests.post(
                f"{BASE_URL}/workspaces",
                json=data
            )
            
            if response.status_code == 201:
                self.load_workspaces()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось создать рабочую область")
    
    def create_styled_list(self):
        """Создает стилизованный QListWidget"""
        list_widget = QListWidget()
        list_widget.setStyleSheet("""
            QListWidget {
                background: #f5f7fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 4px;
            }
            QListWidget::item {
                background: white;
                border-radius: 6px;
                margin: 4px;
            }
            QListWidget::item:hover {
                background: #f0f7ff;
            }
            QScrollBar:vertical {
                border: none;
                background: #f5f7fa;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        list_widget.setSpacing(4)
        return list_widget
    
    def load_friends_data(self):
        """Загрузка данных о друзьях и предложенных пользователях"""
        # Получаем текущих друзей
        response = requests.get(f"{BASE_URL}/friends/{self.user_id}")
        if response.status_code == 200:
            friends_data = response.json().get('friends', [])
            friend_ids = {f['user_id'] for f in friends_data}
        else:
            friend_ids = set()
        
        # Получаем всех пользователей
        response = requests.get(f"{BASE_URL}/users")
        if response.status_code != 200:
            self.show_message_in_list(self.friends_list, "Не удалось загрузить друзей")
            self.show_message_in_list(self.suggested_list, "Не удалось загрузить пользователей")
            return
        
        all_users = response.json().get('users', [])
        
        # Разделяем на друзей и других пользователей
        friends = []
        suggested = []
    
        for user in all_users:
            user_id = user.get('_id', '')
            username = user.get('username', '').strip()
                
            if not username or username.lower() == self.username.lower():
                continue
                    
            if user_id in friend_ids:
                friends.append(user)
            else:
                suggested.append(user)
    
        # Получаем рекомендации
        recommendations = get_friend_recommendations_api(self.user_id)
        
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

        if recommendations:
            self.add_recommendations_to_list(recommendations)
        else:
            self.show_message_in_list(self.recommendations_list, "Нет рекомендаций")
    
    def add_recommendations_to_list(self, recommendations):
        """Добавляет рекомендации в список с дополнительной информацией"""
        self.recommendations_list.clear()

        all_users = get_all_users()
        users_dict = {user['_id']: user for user in all_users}
        
        for rec in recommendations:
            item = QListWidgetItem()
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(10, 5, 10, 5)

            # Аватар
            user_info = users_dict.get(rec['user_id'])
            if not user_info:
                continue

            avatar = QLabel(user_info['username'][0].upper())
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
            name_label = QLabel(user_info['username'])
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
            add_btn.clicked.connect(lambda _, uid=rec['user_id']: self.add_friend(uid))
            
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
        """Стилизованное добавление пользователей в список"""
        list_widget.clear()
        
        for user in users:
            item = QListWidgetItem()
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(10, 8, 10, 8)
            
            # Аватар с тенью
            avatar = QLabel(user['username'][0].upper())
            avatar.setAlignment(Qt.AlignCenter)
            avatar.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4a90e2, stop:1 #3a7bc8);
                color: white;
                font-weight: bold;
                border-radius: 15px;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
            """)
            
            # Имя пользователя
            name_label = QLabel(user['username'])
            name_label.setStyleSheet("""
                font-size: 14px;
                font-weight: 500;
                color: #333;
            """)
            
            # Кнопка действия
            action_btn = QPushButton("Удалить" if is_friend else "Добавить")
            action_btn.setFixedSize(80, 30)
            action_btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    border-radius: 4px;
                    padding: 5px;
                    font-size: 12px;
                    font-weight: 500;
                    color: white;
                    background: %s;
                }
                QPushButton:hover {
                    opacity: 0.9;
                }
            """ % ("#f44336" if is_friend else "#4CAF50"))
            
            if is_friend:
                action_btn.clicked.connect(lambda _, uid=user['_id']: self.remove_friend(uid))
            else:
                action_btn.clicked.connect(lambda _, uid=user['_id']: self.add_friend(uid))
            
            layout.addWidget(avatar)
            layout.addWidget(name_label)
            layout.addStretch()
            layout.addWidget(action_btn)
            
            item.setSizeHint(QSize(0, 48))
            list_widget.addItem(item)
            list_widget.setItemWidget(item, widget)
    
    def add_friend(self, friend_id):
        """Добавление пользователя в друзья"""
        data = {
            "user_id": self.user_id,
            "friend_id": friend_id
        }
        
        response = requests.post(
            f"{BASE_URL}/friends",
            json=data
        )
        
        if response.status_code == 200:
            self.load_friends_data()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось добавить друга")
    
    def remove_friend(self, friend_id):
        """Удаление пользователя из друзей"""
        data = {
            "user_id": self.user_id,
            "friend_id": friend_id
        }
        
        response = requests.delete(
            f"{BASE_URL}/friends",
            json=data
        )
        
        if response.status_code == 200:
            self.load_friends_data()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось удалить друга")

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

class AddMemberDialog(QDialog):
    def __init__(self, parent=None, friends=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить участника")
        self.setModal(True)
        self.setFixedSize(400, 500)
        
        self.friends = friends or []
        self.selected_user_id = None
        self.selected_role = "viewer"
        
        layout = QVBoxLayout()
        
        # Список друзей
        self.friends_list = QListWidget()
        for friend in self.friends:
            item = QListWidgetItem(friend['username'])
            item.setData(Qt.UserRole, friend['user_id'])
            self.friends_list.addItem(item)
        
        self.friends_list.itemClicked.connect(self.select_user)
        
        # Выбор уровня доступа
        role_group = QGroupBox("Уровень доступа")
        role_layout = QVBoxLayout()
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["viewer", "editor", "admin"])
        self.role_combo.currentTextChanged.connect(self.select_role)
        
        role_layout.addWidget(self.role_combo)
        role_group.setLayout(role_layout)
        
        # Кнопки
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addWidget(QLabel("Выберите друга:"))
        layout.addWidget(self.friends_list)
        layout.addWidget(role_group)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def select_user(self, item):
        self.selected_user_id = item.data(Qt.UserRole)
    
    def select_role(self, role):
        self.selected_role = role
    
    def get_selection(self):
        return {
            "user_id": self.selected_user_id,
            "role": self.selected_role
        }
