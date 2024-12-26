import sys
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QTimeEdit,
                             QFileDialog, QMessageBox, QInputDialog, QListWidget, QListWidgetItem, QDialog,
                             QDialogButtonBox, QFormLayout)
from PyQt5.QtCore import QTime, QTimer, Qt
import pygame

# Инициализация Pygame для работы со звуком
pygame.mixer.init()

class AlarmClockApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Установим размер окна по пропорциям мобильного устройства
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        self.setGeometry(100, 100, int(screen_size.width() * 0.5), int(screen_size.height() * 0.9))

        self.setWindowTitle("MathAlarm")

        self.alarm_list = []
        self.max_volume = 10.0  # Максимальная громкость 1000% (10.0 = 1000%)
        self.warning_sound = pygame.mixer.Sound("nuclear_sound.mp3")
        self.warning_playing = False  # Флаг, чтобы сирена не воспроизводилась несколько раз

        # Таймер для проверки будильников
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_alarms)
        self.timer.start(1000)  # Проверяем будильники каждую секунду

        # Таймер для увеличения громкости
        self.volume_timer = QTimer(self)
        self.volume_timer.timeout.connect(self.increase_volume)

        # Стандартный звук будильника
        self.default_alarm_sound = pygame.mixer.Sound("default_sound.mp3")  # Убедитесь, что путь верный

        # Элементы интерфейса
        self.time_edit = QTimeEdit(self)
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime())

        self.set_alarm_button = QPushButton("Set Alarm", self)
        self.set_alarm_button.clicked.connect(self.set_alarm)

        self.choose_default_sound_button = QPushButton("Choose Default Sound", self)
        self.choose_default_sound_button.clicked.connect(self.choose_default_sound)

        self.alarm_list_widget = QListWidget(self)
        self.alarm_list_widget.itemDoubleClicked.connect(self.open_alarm_settings)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Set Alarm Time:", self))
        layout.addWidget(self.time_edit)
        layout.addWidget(self.set_alarm_button)
        layout.addWidget(self.choose_default_sound_button)
        layout.addWidget(QLabel("Alarm List:", self))
        layout.addWidget(self.alarm_list_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def choose_default_sound(self):
        # Выбор звукового файла для стандартного звука
        sound_path, _ = QFileDialog.getOpenFileName(self, "Choose Default Sound File", "", "Sound Files (*.wav *.mp3)")
        if sound_path:
            try:
                self.default_alarm_sound = pygame.mixer.Sound(sound_path)
                QMessageBox.information(self, "Sound Selected", "Default alarm sound selected successfully!")
            except pygame.error:
                QMessageBox.warning(self, "Error", "Failed to load sound file.")

    def set_alarm(self):
        # Установка времени будильника с нулевой громкостью
        alarm_time = self.time_edit.time()
        alarm_data = AlarmData(alarm_time, self.default_alarm_sound, self.max_volume)
        self.alarm_list.append(alarm_data)
        item = QListWidgetItem(f"Alarm set for {alarm_time.toString('HH:mm')}")
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Unchecked)
        self.alarm_list_widget.addItem(item)
        QMessageBox.information(self, "Alarm Set", f"Alarm set for {alarm_time.toString('HH:mm')}.")

    def check_alarms(self):
        # Проверка времени и активации будильника
        current_time = QTime.currentTime()
        for index, alarm_data in enumerate(self.alarm_list):
            if alarm_data.active and current_time.hour() == alarm_data.time.hour() and current_time.minute() == alarm_data.time.minute():
                self.trigger_alarm(alarm_data, index)
            elif self.alarm_list_widget.item(index).checkState() == Qt.Checked:
                alarm_data.active = True
            else:
                alarm_data.active = False

    def trigger_alarm(self, alarm_data, index):
        # Запуск звука, если он не играет
        if not pygame.mixer.get_busy() and not self.warning_playing:
            alarm_data.play_sound()

        # Запуск таймера для увеличения громкости
        self.volume_timer.start(1000)

        # Отображение задачи для отключения
        self.ask_math_problem(alarm_data, index)

    def increase_volume(self):
        # Увеличение громкости активного будильника
        for alarm_data in self.alarm_list:
            if alarm_data.active:
                alarm_data.increase_volume()

                # Остановка звука и переключение на предупреждение через 5 минут
                alarm_data.elapsed_time += 1
                if alarm_data.elapsed_time >= 300 and not self.warning_playing:
                    alarm_data.stop_sound()
                    self.warning_sound.set_volume(self.max_volume)
                    self.warning_sound.play(loops=-1)
                    self.warning_playing = True

    def ask_math_problem(self, alarm_data, index):
        # Генерация задачи для отключения будильника
        num1 = random.randint(1, 20)
        num2 = random.randint(1, 20)
        alarm_data.problem_answer = num1 * num2

        # Запрещаем закрывать окно задачи
        task_dialog = TaskDialog(num1, num2, alarm_data.problem_answer, self.stop_alarm, alarm_data, index)
        task_dialog.exec_()

    def stop_alarm(self, alarm_data, index):
        # Сброс счётчика времени и остановка будильника
        alarm_data.stop_alarm()
        pygame.mixer.stop()
        self.volume_timer.stop()
        alarm_data.elapsed_time = 0  # Сброс счётчика времени
        alarm_data.volume = 0.1  # Сброс громкости на начальное значение

        # Остановка сирены
        if self.warning_playing:
            self.warning_sound.stop()
            self.warning_playing = False

        # Убираем галочку с будильника в списке
        self.alarm_list_widget.item(index).setCheckState(Qt.Unchecked)

    def open_alarm_settings(self, item):
        # Открытие окна настроек будильника
        index = self.alarm_list_widget.row(item)
        alarm_data = self.alarm_list[index]

        dialog = AlarmSettingsDialog(alarm_data)
        if dialog.exec_():
            updated_data = dialog.get_data()
            alarm_data.time = updated_data["time"]
            alarm_data.sound = updated_data["sound"]
            item.setText(f"Alarm set for {alarm_data.time.toString('HH:mm')}")

            # Удаление будильника, если было выбрано
            if dialog.delete_requested:
                self.alarm_list.pop(index)
                self.alarm_list_widget.takeItem(index)


class AlarmData:
    def __init__(self, time, sound, max_volume):
        self.time = time
        self.sound = sound
        self.max_volume = max_volume
        self.volume = 0.1  # Начальная громкость
        self.active = False
        self.elapsed_time = 0  # Время с момента начала звонка
        self.problem_answer = None

    def play_sound(self):
        # Запуск звука с минимальной громкостью
        self.sound.set_volume(self.volume)
        self.sound.play(loops=-1)

    def stop_sound(self):
        # Остановка звука
        self.sound.stop()

    def increase_volume(self):
        # Увеличение громкости на 10% каждую секунду, до максимума
        self.volume = min(self.volume + 0.1, self.max_volume)
        self.sound.set_volume(self.volume)

    def stop_alarm(self):
        # Остановка будильника
        self.active = False


class TaskDialog(QDialog):
    def __init__(self, num1, num2, correct_answer, stop_alarm_func, alarm_data, index):
        super().__init__()
        self.setWindowTitle("Solve to Stop Alarm")
        self.setModal(True)

        self.num1 = num1
        self.num2 = num2
        self.correct_answer = correct_answer
        self.stop_alarm_func = stop_alarm_func
        self.alarm_data = alarm_data
        self.index = index

        # Добавляем счётчик правильных ответов подряд
        self.correct_streak = 0

        layout = QVBoxLayout()
        self.label = QLabel(f"What is {self.num1} * {self.num2}?")
        layout.addWidget(self.label)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.check_answer)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # Отключаем стандартное закрытие окна
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)

    def check_answer(self):
        answer, ok = QInputDialog.getInt(self, "Answer", "Your answer:")
        if ok and answer == self.correct_answer:
            # Увеличиваем счётчик правильных ответов подряд
            self.correct_streak += 1
            if self.correct_streak >= 3:  # Проверяем, если 3 правильных ответа подряд
                self.stop_alarm_func(self.alarm_data, self.index)
                self.accept()
            else:
                # Генерируем новую задачу
                self.num1 = random.randint(1, 20)
                self.num2 = random.randint(1, 20)
                self.correct_answer = self.num1 * self.num2
                self.label.setText(f"What is {self.num1} * {self.num2}?")
        else:
            # Если ответ неверный, сбрасываем счётчик правильных ответов
            self.correct_streak = 0
            # Появляется всплывающее окно
            QMessageBox.warning(self, "Incorrect", "Incorrect answer! Try again.")
            # Генерируем новую задачу
            self.num1 = random.randint(1, 20)
            self.num2 = random.randint(1, 20)
            self.correct_answer = self.num1 * self.num2
            self.label.setText(f"What is {self.num1} * {self.num2}?")


class AlarmSettingsDialog(QDialog):
    def __init__(self, alarm_data):
        super().__init__()

        self.alarm_data = alarm_data
        self.setWindowTitle("Alarm Settings")

        self.time_edit = QTimeEdit(self)
        self.time_edit.setTime(self.alarm_data.time)

        self.sound_button = QPushButton("Change Sound", self)
        self.sound_button.clicked.connect(self.choose_sound)

        self.delete_button = QPushButton("Delete Alarm", self)

        layout = QFormLayout()
        layout.addRow("Set Time:", self.time_edit)
        layout.addRow("Sound:", self.sound_button)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

        self.delete_requested = False
        self.delete_button.clicked.connect(self.delete_alarm)

    def choose_sound(self):
        sound_path, _ = QFileDialog.getOpenFileName(self, "Choose Sound File", "", "Sound Files (*.wav *.mp3)")
        if sound_path:
            self.alarm_data.sound = pygame.mixer.Sound(sound_path)

    def delete_alarm(self):
        self.delete_requested = True
        self.accept()

    def get_data(self):
        return {"time": self.time_edit.time(), "sound": self.alarm_data.sound}


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AlarmClockApp()
    window.show()
    sys.exit(app.exec_())
