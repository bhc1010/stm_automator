import numpy as np
from enum import Enum
from typing import Callable, List, Union

from PySide6 import QtCore, QtGui
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
import qtawesome as fa

from core.exponentialnumber import ExponentialNumber
from core.tasksetdata import TaskSetData, SweepParameter
from core.taskdata import TaskData, TaskType
from core.imagedata import ImageData
from core.specdata import SpecData

def clamp10(value):
    return max(min(value, 1.0), 0.0)

class TaskSetBar(QWidget):
    def __init__(self, value = 0.0, padding = 5, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.value = clamp10(value)
        self._background_color = None
        self._bar_color = None
        self._padding = padding
        self._paint_rect = QRect(QRect(self._padding, self._padding, self.size().width() - 2*self._padding, self.size().height() - 2*self._padding))
        self._vertical_margin = 0
        self.setFixedHeight(60)

    def updateColor(self, status):
        match(status):
            case TaskSet.Status.Ready:
                self._background_color = QColor(235, 235, 235)
                self._bar_color = QColor(200, 200, 200)
            case TaskSet.Status.Working:
                self._background_color = QColor(102, 157, 246)
                self._bar_color = QColor(21, 101, 192)
            case TaskSet.Status.Finished:
                print("WHAT")
                self._background_color = QColor(66, 219, 99)
                self._bar_color = self._background_color
            case TaskSet.Status.Error:
                self._background_color = QColor(255, 78, 78)
                self._bar_color = QColor(255, 41, 41)

    def getPaintRect(self):
        return self._paint_rect
    
    def setPaintRect(self, paint_rect):
        self._paint_rect = paint_rect
        self.update()

    paint_rect = Property(QRect, getPaintRect, setPaintRect)

    def resizeEvent(self, event) -> None:
        self.setPaintRect(QRect(self._paint_rect.top(), self._paint_rect.left(), self.size().width() - 2*self._padding, self.size().height() - 2*self._padding))

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        brush = QtGui.QBrush()
        brush.setStyle(Qt.SolidPattern)
        path = QtGui.QPainterPath()
        
        # Background
        brush.setColor(self._background_color)
        self._paint_rect.setHeight(self._paint_rect.height() + self._vertical_margin)
        path.addRoundedRect(self._paint_rect, 15, 15)
        painter.fillPath(path, brush)

        path.clear()

        # Progress Bar
        brush.setColor(self._bar_color)
        _progress_rect = QRect(self._paint_rect)
        _progress_rect.setWidth(self._paint_rect.width() * self.value)
        _progress_rect.setHeight(_progress_rect.height() + self._vertical_margin)
        path.addRoundedRect(_progress_rect, 15, 15)
        painter.fillPath(path, brush)

class TaskSetInput(QLineEdit):
    def __init__(self, text: str):
        super().__init__(text)
        self._text = text

        self.textChanged.connect(self.updateText)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def updateText(self, text):
        self._text = text
    
    def elideText(self):
        padding = 8
        elidedText = self.fontMetrics().elidedText(self._text, Qt.TextElideMode.ElideRight, self.width() - padding)
        _text = self._text
        self.setText(elidedText)
        self.updateText(_text)
        self.setCursorPosition(0)

    def focusInEvent(self, event) -> None:
        self.setText(self._text)

        return super().focusInEvent(event)

    def focusOutEvent(self, event) -> None:
        self.elideText()

        return super().focusOutEvent(event)

class TaskItem(QCheckBox):
    def __init__(self, data: TaskData, sweep_param: SweepParameter):
        super().__init__(checked=True)
        self.data = data
        self.dtype = data.dtype

        match sweep_param:
            case SweepParameter.bias:
                self.setText(f'Bias: {self.data.inner.bias}V')
            case SweepParameter.size:
                self.setText(f'Size: {self.data.inner.size}m')

    def set_completed(self, val: bool):
        self.data.completed = val

class TaskSetInfo(QWidget):
    def __init__(self, data: TaskSetData, tasks: List[TaskData], remove_task_btn: QPushButton):
        super().__init__(minimumHeight=0, maximumHeight=0)
        self.task_items = list()

        self.background = QColor(245, 245, 245)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self._content = QScrollArea()
        self._content.setStyleSheet('background: transparent')
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(20,5,20,10)
    
        sublayout = QGridLayout()
        bias = QLabel(f'Bias : {data.bias}V')
        set_point = QLabel(f"Set point: {data.set_point}A")
        size = QLabel(f"Size: {data.size}m")
        position = QLabel(f"Position: ({data.x_offset}m, {data.y_offset}m)")
        lines_per_frame = QLabel(f"Lines per frame: {data.lines_per_frame}")
        line_time = QLabel(f"Line time: {data.line_time.to_float()}s")
        sublayout.addWidget(bias, 0, 0)
        sublayout.addWidget(set_point, 0, 1)
        sublayout.addWidget(size, 1, 0)
        sublayout.addWidget(position, 1, 1)
        sublayout.addWidget(line_time, 2, 0)
        sublayout.addWidget(lines_per_frame, 2, 1)

        match data.sweep_parameter:
            case SweepParameter.bias:
                bias.setText("Bias: -")
            case SweepParameter.size:
                size.setText("Size: -")

        self._layout.addLayout(sublayout)
        repetitions = QLabel(f"Repetitions: {data.repetitions}")
        self._layout.addWidget(repetitions)
        self._layout.addWidget(QLabel(f"Total Tasks: {len(tasks)}"))
        self._layout.addWidget(QLabel(f"Time remaining: {data.time_to_finish}"))
        
        for task in tasks:
            self.task_items.append(TaskItem(task, data.sweep_parameter))
            self._layout.addWidget(self.task_items[-1])
        self._layout.addWidget(remove_task_btn)

        self.setLayout(QGridLayout())
        self.layout().addWidget(self._content)
        self.layout().setContentsMargins(0,0,0,0)
            
    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        brush = QtGui.QBrush()
        brush.setStyle(Qt.SolidPattern)
        path = QtGui.QPainterPath()
        
        # Background
        brush.setColor(self.background)
        vertical_margin = 15
        background_rect = QRect(self.rect().left(), self.rect().top() - vertical_margin, self.rect().width(), self.rect().height() + vertical_margin)
        path.addRoundedRect(background_rect, 15, 15)
        painter.fillPath(path, brush)

class TaskSet(QWidget):
    Status = Enum('Status', ['Ready', 'Working', 'Finished', 'Error'])

    def __init__(self, name: str, data: TaskSetData, idx: int, dropFunc: Callable):
        super().__init__()
        self.status = TaskSet.Status.Ready
        self.index = idx
        self.data = data
        self.tasks = self.create_tasks(data)
        self.dropFunc = dropFunc
        self._selected = False

        self.setMaximumHeight(60)
        self._content = QWidget()
        self._task_bar = TaskSetBar()
        self._task_bar.updateColor(self.status)
        self._icon = QLabel(pixmap=fa.icon('fa5.circle', color='black').pixmap(24, 24))
        self._icon.setFixedWidth(24)
        self._name = TaskSetInput(name)
        self._name.textChanged.connect(self.adjustTextWidth)
        self._name.setStyleSheet('QLineEdit { background: transparent; color: black; border: 0px;}')
        self._drag = QLabel(pixmap=fa.icon('fa5s.ellipsis-v', color='black').pixmap(24,24))
        self._drag.setFixedWidth(20)
        self._content.setFixedHeight(self._task_bar.rect().height())

        self._content_layout = QGridLayout(self._content)
        self._content_layout.addWidget(self._task_bar, 0, 0, 3, 7)
        self._content_layout.addItem(QSpacerItem(10, 60), 1, 0)
        self._content_layout.addWidget(self._icon, 1, 1)
        self._content_layout.addItem(QSpacerItem(10, 60, QSizePolicy.Expanding, QSizePolicy.Expanding), 1, 2)
        self._content_layout.addWidget(self._name, 1, 3)
        self._content_layout.addItem(QSpacerItem(10, 60, QSizePolicy.Expanding, QSizePolicy.Expanding), 1, 4)
        self._content_layout.addWidget(self._drag, 1, 5)
        self._content_layout.addItem(QSpacerItem(10, 60), 1, 6)
        self._content_layout.setContentsMargins(0,0,0,0)
        
        self._remove_task_btn = QPushButton("Remove Task")
        self._remove_task_btn.clicked.connect(self.dropSelf)
        self._info = TaskSetInfo(self.data, self.tasks, self._remove_task_btn)

        self._layout = QGridLayout(self)
        self._layout.addWidget(self._info, 1, 0)
        self._layout.addWidget(self._content, 0, 0)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0,0,0,0)

        self.installEventFilter(self)

        self._task_bar_hover_anim = QPropertyAnimation(self._task_bar, b"paint_rect")
        self._task_bar_hover_anim.setDuration(100)
        
        self._info_anim = QParallelAnimationGroup(self)
        self.setInfoAnimation()
        
    def create_tasks(self, data: TaskSetData) -> List[TaskData]:
        tasks = list()
        match data.sweep_parameter:
            case SweepParameter.none:
                img = ImageData(data)
                tasks.append(TaskData(inner=img, dtype=TaskType.Image))
            case SweepParameter.bias:
                bias_range = np.arange(start=data.sweep_start.to_float(), stop=data.sweep_stop.to_float() + data.sweep_step.to_float(), step=data.sweep_step.to_float()) 
                for bias in bias_range:
                    img = ImageData(data)
                    img.bias = ExponentialNumber.from_float(bias)
                    tasks.append(TaskData(inner=img, dtype=TaskType.Image, completed=False))
            case SweepParameter.size:
                size_range = np.arange(start=data.sweep_start.to_float(), stop=data.sweep_stop.to_float() + data.sweep_step.to_float(), step=data.sweep_step.to_float())
                for size in size_range:
                    img = ImageData(data)
                    img.size = ExponentialNumber.from_float(size)
                    tasks.append(TaskData(inner=img, dtype=TaskType.Image))

        return tasks

    def setInfoAnimation(self):
        self._info_anim.clear()
        self._info_anim.addAnimation(QPropertyAnimation(self, b"minimumHeight"))
        self._info_anim.addAnimation(QPropertyAnimation(self, b"maximumHeight"))
        self._info_anim.addAnimation(QPropertyAnimation(self._info, b"maximumHeight"))
        
        collapsed_height = self.sizeHint().height() - self._info.maximumHeight()
        content_height = self._info._layout.sizeHint().height()

        anims = [self._info_anim.animationAt(i) for i in range(self._info_anim.animationCount())]
        for anim in anims[:-1]:
            anim.setDuration(250)
            anim.setStartValue(collapsed_height)
            anim.setEndValue(collapsed_height + content_height)  
        anims[-1].setStartValue(0)
        anims[-1].setEndValue(content_height)
        

        self._name.elideText()

    def setStatus(self, status: Status):
        self.status = status
        self._task_bar.updateColor(status)
        self.update_task_bar()

    def eventFilter(self, obj, ev):
        
        if ev.type() == QtCore.QEvent.Enter:
            if not self._selected:
                self._task_bar_hover_anim.setEndValue(self._task_bar.rect())
                self._task_bar_hover_anim.start()

        if ev.type() == QtCore.QEvent.Leave:
            if not self._selected:
                self._task_bar_hover_anim.setEndValue(QRect(self._task_bar._padding, self._task_bar._padding, self._content.size().width() - 2*self._task_bar._padding, self._content.size().height() - 2*self._task_bar._padding))
                self._task_bar_hover_anim.start()
            
        if ev.type() == QtCore.QEvent.MouseButtonPress:
            self._lastpos = ev.pos()
            
        if ev.type() == QtCore.QEvent.MouseButtonRelease:
            widget_on_press = obj.childAt(ev.pos())
            widget_on_release = obj.childAt(self._lastpos)
            
            if widget_on_press == self._task_bar and widget_on_press == widget_on_release:
                if not self._selected:
                    self._selected = True
                    self._info_anim.setDirection(QtCore.QAbstractAnimation.Forward)
                    self._task_bar._vertical_margin = 10
                else:
                    self._selected = False
                    self._info_anim.setDirection(QtCore.QAbstractAnimation.Backward)
                    self._task_bar._vertical_margin = 0
                    
                self._info_anim.start()

        return False
    
    def adjustTextWidth(self):
        width = self._name.fontMetrics().boundingRect(self._name.text()).width()
        padding = 25
        fixedWidth = min(width + padding, 0.6 * self.rect().width())
        self._name.setFixedWidth(fixedWidth)

    def update_task_bar(self):
        completed_tasks = [item for item in self._info.task_items if item.data.completed]
        val = len(completed_tasks) / len(self._info.task_items)
        self._task_bar.value = val
        self._task_bar.repaint()

    def setIndex(self, i):
        self.index = i

    def dropSelf(self):
        self.dropFunc(self.index)

    def resizeEvent(self, event) -> None:
        self.adjustTextWidth()
        return super().resizeEvent(event)
    
    