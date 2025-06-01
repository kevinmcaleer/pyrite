import sys
import os
import re
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog,
                               QSplitter, QTextEdit, QListWidget, QVBoxLayout, QWidget, QLabel,
                               QListWidgetItem, QStatusBar, QPushButton, QHBoxLayout, QInputDialog)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QDir, QTimer
import markdown2
from datetime import datetime


class ObsidianClone(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Obsidian Clone - Python")
        self.setGeometry(100, 100, 1000, 600)

        self.vault_path = QFileDialog.getExistingDirectory(self, "Select Vault Folder", QDir.homePath())
        if not self.vault_path:
            sys.exit(0)

        self.current_file = None
        self.init_ui()
        self.load_file_list()
        self.setup_autosave()

    def init_ui(self):
        splitter = QSplitter(Qt.Horizontal)

        # Sidebar for file list and new note button
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.open_note)

        self.new_note_button = QPushButton("+ New Note")
        self.new_note_button.clicked.connect(self.create_new_note)

        file_panel = QWidget()
        file_layout = QVBoxLayout(file_panel)
        file_layout.addWidget(self.new_note_button)
        file_layout.addWidget(self.file_list)

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

        splitter.addWidget(file_panel)
        splitter.addWidget(right_splitter)
        splitter.setSizes([200, 800])

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(splitter)

        self.setCentralWidget(central_widget)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def load_file_list(self):
        self.file_list.clear()
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                if file.endswith(".md"):
                    relative_path = os.path.relpath(os.path.join(root, file), self.vault_path)
                    self.file_list.addItem(relative_path)

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
            item = QListWidgetItem(f"#{tag}")
            item.setForeground(Qt.darkBlue)
            item.setBackground(Qt.lightGray)
            item.setFont(self.editor.font())
            self.tags_panel.addItem(item)

    def setup_autosave(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave_note)
        self.autosave_timer.start(5000)  # Every 5 seconds

    def autosave_note(self):
        if self.current_file:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
                self.status_bar.showMessage("Note auto-saved", 2000)
            except Exception as e:
                print(f"Autosave failed: {e}")
                self.status_bar.showMessage("Autosave failed", 2000)

    def create_new_note(self):
        folder, ok = QInputDialog.getText(self, "Create New Note", "Enter folder path (or leave empty for root):")
        if not ok:
            return

        subdir = os.path.join(self.vault_path, folder) if folder else self.vault_path
        os.makedirs(subdir, exist_ok=True)

        filename = f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path = os.path.join(subdir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# New Note\n")
        self.load_file_list()

        relative_path = os.path.relpath(file_path, self.vault_path)
        items = self.file_list.findItems(relative_path, Qt.MatchExactly)
        if items:
            self.file_list.setCurrentItem(items[0])
            self.open_note(items[0])


def main():
    app = QApplication(sys.argv)
    window = ObsidianClone()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
