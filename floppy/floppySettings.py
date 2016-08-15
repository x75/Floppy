from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPoint, QSettings

class SettingsDialog(QDialog):
    def __init__(self, *args, settings=None, globals=None):
        self.globals = globals
        self.settings= settings
        self.dialogs = [('Default Connection', DefaultConnectionEdit(settings, globals, self)),
                        ('Node Font Size', FontSizeEdit(settings, globals, self)),
                        ('Node Font Offset', FontOffsetEdit(settings, globals, self)),
                        ('Node Title Font Size', TitleFontSizeEdit(settings, globals, self)),]
        super(SettingsDialog, self).__init__(*args)
        layout = QFormLayout()
        for name, widget in self.dialogs:
            layout.addRow(name, widget)
        self.setLayout(layout)

    def closeEvent(self, e):
        for name, widget in self.dialogs:
            widget.commit()
        self.settings.sync()
        super(SettingsDialog, self).closeEvent(e)

    def redraw(self):
        self.parent().drawer.repaint()
        # self.parent().drawer.update()
        # print('xxxx')


class DefaultConnectionEdit(QLineEdit):
    def __init__(self, settings, globals, parent):
        self.parent = parent
        self.globals = globals
        self.settings = settings
        super(DefaultConnectionEdit, self).__init__()
        v = settings.value('DefaultConnection', type=str)
        v = v if v else '127.0.0.1:7234'
        self.setText(v)

    def commit(self):
        self.settings.setValue('DefaultConnection', self.text())


class FontSizeEdit(QSpinBox):
    def __init__(self, settings, globals, parent):
        self.parent = parent
        self.globals = globals
        self.settings = settings
        super(FontSizeEdit, self).__init__()
        v = settings.value('NodeFontSize', type=int)
        v = v if v else 8
        self.setValue(v)
        self.valueChanged.connect(self.redraw)

    def commit(self):
        self.settings.setValue('NodeFontSize', self.value())
        self.globals['LINEEDITFONTSIZE'] = self.value()

    def redraw(self):
        self.globals['LINEEDITFONTSIZE'] = self.value()
        self.parent.redraw()


class FontOffsetEdit(QSpinBox):
    def __init__(self, settings, globals, parent):
        self.parent = parent
        self.globals = globals
        self.settings = settings
        super(FontOffsetEdit, self).__init__()
        v = settings.value('NodeFontOffset', type=int)
        v = v if v else 0
        self.setRange(-10, 10)
        self.setValue(v)
        self.valueChanged.connect(self.redraw)

    def commit(self):
        self.settings.setValue('NodeFontOffset', self.value())
        self.globals['TEXTYOFFSET'] = self.value()

    def redraw(self):
        self.globals['TEXTYOFFSET'] = self.value()
        self.parent.redraw()


class TitleFontSizeEdit(QSpinBox):
    def __init__(self, settings, globals, parent):
        self.parent = parent
        self.globals = globals
        self.settings = settings
        super(TitleFontSizeEdit, self).__init__()
        v = settings.value('TitleFontSize', type=int)
        v = v if v else 11
        self.setRange(1, 20)
        self.setValue(v)
        self.valueChanged.connect(self.redraw)

    def commit(self):
        self.settings.setValue('TitleFontSize', self.value())
        self.globals['NODETITLEFONTSIZE'] = self.value()

    def redraw(self):
        self.globals['NODETITLEFONTSIZE'] = self.value()
        self.parent.redraw()
