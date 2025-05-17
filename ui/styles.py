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
        border: 1px solid #c4c4c4;
        border-radius: 4px;
        padding: 4px;
    }
    QTabBar::tab {
        background: #f0f0f0;
        padding: 8px 12px;
        border: 1px solid #c4c4c4;
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    QTabBar::tab:selected {
        background: #ffffff;
        border-bottom: 2px solid #2a82da;
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
        QWidget {
            background-color: #f5f5f5;
            color: #333333;
        }
        QTabBar::tab:selected {
            background: #ffffff;
            border-bottom: 2px solid #4CAF50;
        }
    """,
    'blue': """
        QWidget {
            background-color: #e6f3ff;
            color: #003366;
        }
        QTabBar::tab:selected {
            background: #ffffff;
            border-bottom: 2px solid #2196F3;
        }
    """,
    'professional': """
        QWidget {
            background-color: #f9f9f9;
            color: #222222;
            font-family: 'Segoe UI';
        }
        QTabBar::tab:selected {
            background: #ffffff;
            border-bottom: 2px solid #607D8B;
            font-weight: bold;
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

def apply_tab_styles(tab_widget):
    """Sekme stillerini uygular"""
    tab_widget.setStyleSheet("""
        QTabWidget::pane {
            border: 1px solid #c4c4c4;
            border-radius: 4px;
            padding: 4px;
        }
        QTabBar::tab {
            background: #f0f0f0;
            padding: 8px 12px;
            border: 1px solid #c4c4c4;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background: #ffffff;
            border-bottom: 2px solid #2a82da;
        }
    """)
