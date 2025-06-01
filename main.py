import sys
import os
import re
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog,
                               QSplitter, QTextEdit, QListWidget, QVBoxLayout, QWidget, QLabel)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QDir
import markdown2


class ObsidianClone(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Obsidian Clone - Python")
        self.setGeometry(100, 100, 1000, 600)

        self.vault_path = QFileDialog.getExistingDirectory(self, "Select Vault Folder", QDir.homePath())
        if not self.vault_path:
            sys.exit(0)

        self.init_ui()
        self.load_file_list()

    def init_ui(self):
        splitter = QSplitter(Qt.Horizontal)

        # Sidebar for file list
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.open_note)

        # Editor and Preview
        self.editor = QTextEdit()
        self.editor.textChanged.connect(self.update_preview)

        self.preview = QWebEngineView()

        editor_preview_split = QSplitter(Qt.Vertical)
        editor_preview_split.addWidget(self.editor)
        editor_preview_split.addWidget(self.preview)

        # Right-side tags panel
        self.tags_panel = QListWidget()
        self.tags_label = QLabel("Tags")
        self.tags_label.setAlignment(Qt.AlignCenter)
        self.tags_widget = QWidget()
        tags_layout = QVBoxLayout(self.tags_widget)
        tags_layout.addWidget(self.tags_label)
        tags_layout.addWidget(self.tags_panel)

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(editor_preview_split)
        right_splitter.addWidget(self.tags_widget)
        right_splitter.setSizes([500, 100])

        splitter.addWidget(self.file_list)
        splitter.addWidget(right_splitter)
        splitter.setSizes([200, 800])

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(splitter)

        self.setCentralWidget(central_widget)

    def load_file_list(self):
        self.file_list.clear()
        for file in os.listdir(self.vault_path):
            if file.endswith(".md"):
                self.file_list.addItem(file)

    def open_note(self, item):
        file_path = os.path.join(self.vault_path, item.text())
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.editor.setPlainText(content)
        self.current_file = file_path
        self.update_tags_panel(content)

    def update_preview(self):
        markdown_text = self.editor.toPlainText()
        html = markdown2.markdown(markdown_text)
        self.preview.setHtml(html)
        self.update_tags_panel(markdown_text)

    def update_tags_panel(self, text):
        tags = sorted(set(re.findall(r'(?<!\w)#(\w+)', text)))
        self.tags_panel.clear()
        for tag in tags:
            self.tags_panel.addItem(f"#{tag}")


def main():
    app = QApplication(sys.argv)
    window = ObsidianClone()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()