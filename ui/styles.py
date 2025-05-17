class Styles:
    MAIN_WINDOW = """
    QWidget {
        background-color: #f6f8f9;
        color: #2c3e50;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 14px;
    }
    QMainWindow {
        background-color: #e5ebee;
        border-radius: 12px;
    }
    """

    TAB_STYLES = """
    QTabWidget::pane {
        background: rgba(255, 255, 255, 230);
        border: 2px solid #bdc3c7;
        border-radius: 12px;
    }
    QTabBar::tab {
        background-color: #34495e;
        color: white;
        padding: 12px 20px;
        margin-right: 6px;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        min-width: 120px;
        font-weight: bold;
    }
    QTabBar::tab:hover {
        background-color: #3498db;
    }
    QTabBar::tab:selected {
        background-color: #2980b9;
        color: white;
    }
    """

    TABLE = """
    QTableWidget {
        background-color: white;
        border: 1px solid #bdc3c7;
        border-radius: 6px;
        gridline-color: #ecf0f1;
    }
    QTableWidget::item {
        padding: 6px;
        border-bottom: 1px solid #ecf0f1;
    }
    QHeaderView::section {
        background-color: #34495e;
        color: white;
        padding: 8px;
        border: 1px solid #2c3e50;
        font-weight: bold;
    }
    """

    BUTTONS = """
    QPushButton {
        background-color: #3498db;
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #2980b9;
    }
    QPushButton:pressed {
        background-color: #21618c;
    }
    """

    INPUT_STYLES = """
    QLineEdit, QDateEdit, QComboBox {
        padding: 6px;
        border: 1px solid #ced4da;
        border-radius: 4px;
        background-color: white;
    }
    QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
        border-color: #007bff;
    }
    """

from PyQt5.QtGui import QColor

MODERN_DARK = """
QMainWindow {
    background-color: #2d2d2d;
    color: #f0f0f0;
}
QPushButton {
    background-color: #3a3a3a;
    border-radius: 4px;
    padding: 5px;
    min-width: 80px;
}
QPushButton:hover {
    background-color: #4a4a4a;
}
QChartView {
    background: transparent;
    border: 1px solid #444;
    border-radius: 8px;
}
"""

THEMES = {
    'dark': MODERN_DARK,
    'light': """
QMainWindow {
    background-color: #f5f5f5;
}
"""
}

def apply_global_styles(app):
    # Global stil ayarları
    app.setStyle('Fusion')
    
    # Modern ve profesyonel stil
    app.setStyleSheet(f'''
        {Styles.MAIN_WINDOW}
        {Styles.TAB_STYLES}
        {Styles.TABLE}
        {Styles.BUTTONS}
        {Styles.INPUT_STYLES}
    ''')

def apply_theme(app, theme_name='dark'):
    app.setStyleSheet(THEMES.get(theme_name, MODERN_DARK))
