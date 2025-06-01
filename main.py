import sys
import os
import re
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog,
                               QSplitter, QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QLabel,
                               QStatusBar, QPushButton, QInputDialog, QMenu, QMessageBox)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QDir, QTimer, QPoint
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QDrag
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

    from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QObject, Slot

class Bridge(QObject):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    @Slot(str)
    def openNote(self, noteName):
        for root, _, files in os.walk(self.parent.vault_path):
            for file in files:
                if file.endswith(".md") and os.path.splitext(file)[0] == noteName:
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.parent.editor.setPlainText(content)
                    self.parent.current_file = file_path
                    self.parent.update_tags_panel(content)
                    self.parent.update_backlinks_panel(noteName)
                    return


def init_ui(self):
        self.backlinks_panel = QTreeWidget()
        self.backlinks_panel.setHeaderHidden(True)
        self.backlinks_label = QLabel("Backlinks")
        self.backlinks_label.setAlignment(Qt.AlignCenter)
        self.backlinks_widget = QWidget()
        backlinks_layout = QVBoxLayout(self.backlinks_widget)
        backlinks_layout.addWidget(self.backlinks_label)
        backlinks_layout.addWidget(self.backlinks_panel)
        splitter = QSplitter(Qt.Horizontal)

        self.tree_view = QTreeWidget()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setDragEnabled(True)
        self.tree_view.setAcceptDrops(True)
        self.tree_view.setDropIndicatorShown(True)
        self.tree_view.setDragDropMode(QTreeWidget.InternalMove)
        self.tree_view.itemDoubleClicked.connect(self.open_note)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.tree_view.dropEvent = self.handle_drop_event

        self.new_note_button = QPushButton("+ New Note")
        self.new_note_button.clicked.connect(self.create_new_note)

        file_panel = QWidget()
        file_layout = QVBoxLayout(file_panel)
        file_layout.addWidget(self.new_note_button)
        file_layout.addWidget(self.tree_view)

        self.editor = QTextEdit()
        self.editor.textChanged.connect(self.update_preview)

        self.preview = QWebEngineView()
        self.channel = QWebChannel()

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
        right_right_splitter = QSplitter(Qt.Vertical)
        right_right_splitter.addWidget(self.tags_widget)
        right_right_splitter.addWidget(self.backlinks_widget)
        right_right_splitter.setSizes([50, 50])
        right_splitter.addWidget(right_right_splitter)
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

    def handle_drop_event(self, event: QDropEvent):
        target_item = self.tree_view.itemAt(event.position().toPoint())
        if not target_item:
            event.ignore()
            return
        dest_path = target_item.data(0, Qt.UserRole)
        if not os.path.isdir(dest_path):
            dest_path = os.path.dirname(dest_path)

        selected_items = self.tree_view.selectedItems()
        for item in selected_items:
            src_path = item.data(0, Qt.UserRole)
            if os.path.exists(src_path):
                new_path = os.path.join(dest_path, os.path.basename(src_path))
                if src_path != new_path:
                    self.update_links_on_rename(src_path, new_path)
                    os.rename(src_path, new_path)
        self.load_tree_view()
        event.accept()

    def open_note(self, item, column):
        path = item.data(0, Qt.UserRole)
        if os.path.isfile(path) and path.endswith(".md"):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.current_file = path
            self.update_tags_panel(content)
            self.update_backlinks_panel(os.path.splitext(os.path.basename(path))[0])

    def update_preview(self):
        markdown_text = self.editor.toPlainText()

        def link_replacer(match):
            content = match.group(1)
            if '|' in content:
                target, label = content.split('|', 1)
            else:
                target, label = content, content
            return f'<a href="#" style="color: blue; text-decoration: underline;" onclick=\"window.noteOpen(\'{target}\')\">{label}</a>'

        wikilink_pattern = re.compile(r'\[\[(.*?)\]\]')
        processed_text = wikilink_pattern.sub(link_replacer, markdown_text)

        script = """
        <script>
        window.noteOpen = function(noteName) {
            new QWebChannel(qt.webChannelTransport, function(channel) {
                channel.objects.bridge.openNote(noteName);
            });
        };
        </script>
        """

        html = f"""
        <html>
        <head><style>a:hover {{ color: darkblue; }}</style></head>
        <body>{markdown2.markdown(processed_text)}{script}</body>
        </html>
        """
        self.preview.setHtml(html)
        self.update_tags_panel(markdown_text)

    def update_backlinks_panel(self, current_note):
        self.backlinks_panel.clear()
        self.backlinks_panel.itemClicked.connect(self.open_backlink_note)
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        basename = os.path.basename(file_path)
                        if ((f'[[{current_note}]]' in content or f'![[{current_note}]]' in content)
                                and os.path.splitext(basename)[0] != current_note):
                            item = QTreeWidgetItem([os.path.splitext(basename)[0]])
                            item.setData(0, Qt.UserRole, file_path)
                            self.backlinks_panel.addTopLevelItem(item)
                    except Exception as e:
                        print(f"Failed to read backlinks in {file_path}: {e}")

    def open_backlink_note(self, item):
        path = item.data(0, Qt.UserRole)
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.current_file = path
            self.update_tags_panel(content)
            self.update_backlinks_panel(os.path.splitext(os.path.basename(path))[0])

    def update_tags_panel(self, text):
        tags = sorted(set(re.findall(r'(?<!\w)#(\w+)', text)))
        self.tags_panel.clear()
        for tag in tags:
            item = QTreeWidgetItem([f"#{tag}"])
            item.setForeground(0, Qt.darkBlue)
            self.tags_panel.addTopLevelItem(item)

    def update_links_on_rename(self, old_path, new_path):
        old_name = os.path.splitext(os.path.basename(old_path))[0]
        new_name = os.path.splitext(os.path.basename(new_path))[0]
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        updated = re.sub(rf'\[\[{re.escape(old_name)}\]\]', f'[[{new_name}]]', content)
                        if content != updated:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(updated)
                    except Exception as e:
                        print(f"Failed to update links in {file_path}: {e}")

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
                    self.update_links_on_rename(path, new_path)
                    os.rename(path, new_path)
                    self.load_tree_view()
            elif action == rename_action:
                new_name, ok = QInputDialog.getText(self, "Rename Note", "New note name:")
                if ok:
                    new_path = os.path.join(os.path.dirname(path), new_name)
                    if not new_path.endswith(".md"):
                        new_path += ".md"
                    self.update_links_on_rename(path, new_path)
                    os.rename(path, new_path)
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
