import sys
import os
import re
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog,
                               QSplitter, QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QLabel,
                               QStatusBar, QPushButton, QInputDialog, QMenu, QMessageBox)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QDir, QTimer, QPoint
from PySide6.QtGui import QIcon
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
        self.load_tree_view()
        self.setup_autosave()

    def init_ui(self):
        splitter = QSplitter(Qt.Horizontal)

        self.tree_view = QTreeWidget()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.itemDoubleClicked.connect(self.open_note)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)

        self.new_note_button = QPushButton("+ New Note")
        self.new_note_button.clicked.connect(self.create_new_note)

        file_panel = QWidget()
        file_layout = QVBoxLayout(file_panel)
        file_layout.addWidget(self.new_note_button)
        file_layout.addWidget(self.tree_view)

        self.editor = QTextEdit()
        self.editor.textChanged.connect(self.update_preview)

        self.preview = QWebEngineView()

        editor_preview_split = QSplitter(Qt.Vertical)
        editor_preview_split.addWidget(self.editor)
        editor_preview_split.addWidget(self.preview)

        self.tags_panel = QTreeWidget()
        self.tags_panel.setHeaderHidden(True)
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
        splitter.setSizes([300, 700])

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(splitter)
        self.setCentralWidget(central_widget)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def load_tree_view(self):
        self.tree_view.clear()

        def add_items(parent_item, path):
            for entry in sorted(os.listdir(path)):
                full_path = os.path.join(path, entry)
                item = QTreeWidgetItem([entry])
                item.setData(0, Qt.UserRole, full_path)
                if os.path.isdir(full_path):
                    item.setIcon(0, QIcon.fromTheme("folder"))
                    add_items(item, full_path)
                else:
                    item.setIcon(0, QIcon.fromTheme("text-x-generic"))
                parent_item.addChild(item)

        root_item = QTreeWidgetItem([os.path.basename(self.vault_path)])
        root_item.setData(0, Qt.UserRole, self.vault_path)
        root_item.setIcon(0, QIcon.fromTheme("folder"))
        self.tree_view.addTopLevelItem(root_item)
        add_items(root_item, self.vault_path)
        root_item.setExpanded(True)

    def open_note(self, item, column):
        path = item.data(0, Qt.UserRole)
        if os.path.isfile(path) and path.endswith(".md"):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.current_file = path
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
            item = QTreeWidgetItem([f"#{tag}"])
            item.setForeground(0, Qt.darkBlue)
            self.tags_panel.addTopLevelItem(item)

    def setup_autosave(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave_note)
        self.autosave_timer.start(5000)

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

        self.load_tree_view()

    def show_context_menu(self, point: QPoint):
        item = self.tree_view.itemAt(point)
        if not item:
            return
        path = item.data(0, Qt.UserRole)
        menu = QMenu(self)

        if os.path.isdir(path):
            create_action = menu.addAction("Create Folder")
            delete_action = menu.addAction("Delete Folder")
            rename_action = menu.addAction("Rename Folder")
            action = menu.exec(self.tree_view.mapToGlobal(point))
            if action == create_action:
                name, ok = QInputDialog.getText(self, "Create Folder", "Folder name:")
                if ok:
                    os.makedirs(os.path.join(path, name), exist_ok=True)
                    self.load_tree_view()
            elif action == delete_action:
                try:
                    os.rmdir(path)
                    self.load_tree_view()
                except OSError:
                    QMessageBox.warning(self, "Error", "Folder must be empty to delete.")
            elif action == rename_action:
                new_name, ok = QInputDialog.getText(self, "Rename Folder", "New folder name:")
                if ok:
                    new_path = os.path.join(os.path.dirname(path), new_name)
                    os.rename(path, new_path)
                    self.load_tree_view()

        elif os.path.isfile(path):
            move_action = menu.addAction("Move Note...")
            rename_action = menu.addAction("Rename Note")
            action = menu.exec(self.tree_view.mapToGlobal(point))
            if action == move_action:
                dest, ok = QInputDialog.getText(self, "Move Note", "Enter destination folder:")
                if ok:
                    dest_path = os.path.join(self.vault_path, dest)
                    os.makedirs(dest_path, exist_ok=True)
                    new_path = os.path.join(dest_path, os.path.basename(path))
                    os.rename(path, new_path)
                    self.load_tree_view()
            elif action == rename_action:
                new_name, ok = QInputDialog.getText(self, "Rename Note", "New note name:")
                if ok:
                    new_path = os.path.join(os.path.dirname(path), new_name)
                    if not new_path.endswith(".md"):
                        new_path += ".md"
                    os.rename(path, new_path)
                    self.load_tree_view()


def main():
    app = QApplication(sys.argv)
    window = ObsidianClone()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()