"""
Arayüz animasyonları
"""
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve

class Animations:
    @staticmethod
    def fade_in(widget, duration=300):
        anim = QPropertyAnimation(widget, b"windowOpacity")
        anim.setDuration(duration)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.start()

    @staticmethod
    def slide_in(widget, duration=400):
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setStartValue(widget.pos() + QPoint(-100, 0))
        anim.setEndValue(widget.pos())
        anim.setEasingCurve(QEasingCurve.OutBack)
        anim.start()
