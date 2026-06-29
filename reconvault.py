import sys
import os
import sqlite3
import datetime
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QTextEdit, QFileDialog, QMessageBox, QDialog, QFormLayout,
    QComboBox, QFrame, QScrollArea, QMenu
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QAction, QIcon, QTextCharFormat

# --- CONFIGURATION & STYLES ---

DB_PATH = Path.home() / ".reconvault" / "reconvault.db"
os.makedirs(DB_PATH.parent, exist_ok=True)

DARK_BG = "#0d0d0d"
SURFACE_BG = "#1a1a1a"
ACCENT_RED = "#e63946"
TEXT_COLOR = "#e0e0e0"
BORDER_COLOR = "#333333"

STYLE_SHEET = f"""
QMainWindow, QDialog, QWidget {{
    background-color: {DARK_BG};
    color: {TEXT_COLOR};
    font-family: 'Courier New', monospace;
}}

QFrame#Sidebar {{
    background-color: {SURFACE_BG};
    border-right: 1px solid {BORDER_COLOR};
}}

QListWidget {{
    background-color: {SURFACE_BG};
    border: none;
    outline: none;
}}

QListWidget::item {{
    padding: 10px;
    border-bottom: 1px solid {BORDER_COLOR};
}}

QListWidget::item:selected {{
    background-color: {ACCENT_RED};
    color: white;
}}

QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    background: {DARK_BG};
}}

QTabBar::tab {{
    background: {SURFACE_BG};
    padding: 10px 20px;
    border: 1px solid {BORDER_COLOR};
    border-bottom: none;
}}

QTabBar::tab:selected {{
    background: {DARK_BG};
    border-top: 2px solid {ACCENT_RED};
}}

QTableWidget {{
    background-color: {DARK_BG};
    gridline-color: {BORDER_COLOR};
    border: 1px solid {BORDER_COLOR};
}}

QHeaderView::section {{
    background-color: {SURFACE_BG};
    color: {TEXT_COLOR};
    padding: 5px;
    border: 1px solid {BORDER_COLOR};
}}

QLineEdit, QTextEdit {{
    background-color: {SURFACE_BG};
    border: 1px solid {BORDER_COLOR};
    color: {TEXT_COLOR};
    padding: 5px;
}}

QPushButton {{
    background-color: {SURFACE_BG};
    border: 1px solid {ACCENT_RED};
    color: {ACCENT_RED};
    padding: 8px 15px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {ACCENT_RED};
    color: white;
}}

QLabel#Title {{
    font-size: 20px;
    font-weight: bold;
    color: {ACCENT_RED};
    margin-bottom: 10px;
}}

QLabel#Badge {{
    padding: 2px 5px;
    border-radius: 3px;
    font-weight: bold;
}}
"""

# --- DATABASE LOGIC ---

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH))
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Targets table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                domain TEXT,
                platform TEXT,
                date_added TEXT,
                last_modified TEXT
            )
        """)
        # Subdomains table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS subdomains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER,
                subdomain TEXT,
                ip TEXT,
                status TEXT,
                tech_stack TEXT,
                notes TEXT,
                FOREIGN KEY(target_id) REFERENCES targets(id) ON DELETE CASCADE
            )
        """)
        # Ports table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER,
                ip TEXT,
                port TEXT,
                protocol TEXT,
                service TEXT,
                version TEXT,
                notes TEXT,
                FOREIGN KEY(target_id) REFERENCES targets(id) ON DELETE CASCADE
            )
        """)
        # Endpoints table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS endpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER,
                url TEXT,
                method TEXT,
                parameters TEXT,
                status_code TEXT,
                notes TEXT,
                FOREIGN KEY(target_id) REFERENCES targets(id) ON DELETE CASCADE
            )
        """)
        # Vulnerabilities table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER,
                title TEXT,
                severity TEXT,
                status TEXT,
                cve_cwe TEXT,
                description TEXT,
                FOREIGN KEY(target_id) REFERENCES targets(id) ON DELETE CASCADE
            )
        """)
        # Notes table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER UNIQUE,
                content TEXT,
                last_modified TEXT,
                FOREIGN KEY(target_id) REFERENCES targets(id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    def update_last_modified(self, target_id):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("UPDATE targets SET last_modified = ? WHERE id = ?", (now, target_id))
        self.conn.commit()

# --- DIALOGS ---

class NewTargetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Target")
        self.setFixedSize(400, 300)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.domain_edit = QLineEdit()
        self.platform_edit = QComboBox()
        self.platform_edit.addItems(["HackerOne", "Bugcrowd", "Intigriti", "CTF", "Private", "Other"])
        self.platform_edit.setEditable(True)

        layout.addRow("Target Name:", self.name_edit)
        layout.addRow("Main Domain:", self.domain_edit)
        layout.addRow("Platform:", self.platform_edit)

        self.buttons = QHBoxLayout()
        self.save_btn = QPushButton("CREATE")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.clicked.connect(self.reject)
        self.buttons.addWidget(self.save_btn)
        self.buttons.addWidget(self.cancel_btn)
        layout.addRow(self.buttons)

    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "domain": self.domain_edit.text(),
            "platform": self.platform_edit.currentText()
        }

# --- CUSTOM WIDGETS ---

class ReconTable(QTableWidget):
    data_changed = pyqtSignal(int) # target_id

    def __init__(self, columns, target_id, db, table_name):
        super().__init__(0, len(columns))
        self.columns = columns
        self.target_id = target_id
        self.db = db
        self.table_name = table_name
        self.setHorizontalHeaderLabels(columns)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.itemChanged.connect(self.handle_item_changed)
        self._updating = False

    def load_data(self, rows):
        self._updating = True
        self.setRowCount(0)
        for row_data in rows:
            row_idx = self.rowCount()
            self.insertRow(row_idx)
            # row_data[0] is ID, row_data[1] is target_id
            for col_idx, value in enumerate(row_data[2:]):
                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setData(Qt.ItemDataRole.UserRole, row_data[0]) # Store DB ID
                self.setItem(row_idx, col_idx, item)
        self._updating = False

    def handle_item_changed(self, item):
        if self._updating: return
        db_id = item.data(Qt.ItemDataRole.UserRole)
        col_name = self.columns[item.column()].lower().replace(" ", "_").replace("&", "").replace("/", "_")
        # Map specific columns to DB schema names if they differ
        mapping = {"cve/cwe": "cve_cwe", "tech_stack": "tech_stack", "status_code": "status_code"}
        db_col = mapping.get(col_name, col_name)
        
        query = f"UPDATE {self.table_name} SET {db_col} = ? WHERE id = ?"
        self.db.cursor.execute(query, (item.text(), db_id))
        self.db.conn.commit()
        self.db.update_last_modified(self.target_id)
        self.data_changed.emit(self.target_id)

    def show_context_menu(self, pos):
        menu = QMenu()
        add_act = QAction("Add Row", self)
        add_act.triggered.connect(self.add_new_row)
        del_act = QAction("Delete Row", self)
        del_act.triggered.connect(self.delete_selected_row)
        copy_act = QAction("Copy Row", self)
        copy_act.triggered.connect(self.copy_row)
        
        menu.addAction(add_act)
        if self.currentRow() >= 0:
            menu.addAction(del_act)
            menu.addAction(copy_act)
        menu.exec(self.mapToGlobal(pos))

    def add_new_row(self):
        cols_str = ", ".join([c.lower().replace(" ", "_").replace("&", "").replace("/", "_") for c in self.columns])
        # Fix mapping for insert
        mapping = {"cve/cwe": "cve_cwe", "tech_stack": "tech_stack", "status_code": "status_code"}
        cols_db = ", ".join([mapping.get(c.lower().replace(" ", "_").replace("&", "").replace("/", "_"), c.lower().replace(" ", "_").replace("&", "").replace("/", "_")) for c in self.columns])
        placeholders = ", ".join(["?" for _ in self.columns])
        
        query = f"INSERT INTO {self.table_name} (target_id, {cols_db}) VALUES (?, {placeholders})"
        vals = [self.target_id] + ["" for _ in self.columns]
        self.db.cursor.execute(query, vals)
        self.db.conn.commit()
        self.db.update_last_modified(self.target_id)
        self.refresh_needed()

    def delete_selected_row(self):
        row = self.currentRow()
        if row < 0: return
        item = self.item(row, 0)
        db_id = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(self, "Confirm", "Delete this row?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (db_id,))
            self.db.conn.commit()
            self.db.update_last_modified(self.target_id)
            self.removeRow(row)

    def copy_row(self):
        row = self.currentRow()
        if row < 0: return
        data = []
        for c in range(self.columnCount()):
            data.append(self.item(row, c).text())
        QApplication.clipboard().setText("\t".join(data))

    def refresh_needed(self):
        # This will be connected to the parent's reload logic
        self.data_changed.emit(self.target_id)

# --- MAIN APPLICATION ---

class ReconVault(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.current_target_id = None
        self.init_ui()
        self.load_targets()
        self.show_dashboard()

    def init_ui(self):
        self.setWindowTitle("ReconVault")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(STYLE_SHEET)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Top Bar ---
        top_bar = QFrame()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet(f"background-color: {SURFACE_BG}; border-bottom: 1px solid {BORDER_COLOR};")
        top_layout = QHBoxLayout(top_bar)
        
        logo_label = QLabel("RECONVAULT")
        logo_label.setObjectName("Title")
        top_layout.addWidget(logo_label)
        
        top_layout.addStretch()
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Global Search...")
        self.search_bar.setFixedWidth(400)
        self.search_bar.returnPressed.connect(self.perform_global_search)
        top_layout.addWidget(self.search_bar)
        
        new_target_btn = QPushButton("+ NEW TARGET")
        new_target_btn.clicked.connect(self.create_new_target)
        top_layout.addWidget(new_target_btn)
        
        main_layout.addWidget(top_bar)

        # --- Content Area ---
        content_layout = QHBoxLayout()
        
        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(self.sidebar)
        
        dash_btn = QPushButton("DASHBOARD")
        dash_btn.clicked.connect(self.show_dashboard)
        sidebar_layout.addWidget(dash_btn)
        
        sidebar_layout.addWidget(QLabel("TARGETS"))
        self.target_list = QListWidget()
        self.target_list.itemClicked.connect(self.on_target_selected)
        sidebar_layout.addWidget(self.target_list)
        
        content_layout.addWidget(self.sidebar)

        # Main Workspace (Stacked)
        self.workspace = QStackedWidget()
        content_layout.addWidget(self.workspace)
        
        main_layout.addLayout(content_layout)

        # Initialize Dashboard and Workspace pages
        self.init_dashboard_ui()
        self.init_target_workspace_ui()

    def init_dashboard_ui(self):
        self.dash_page = QWidget()
        layout = QVBoxLayout(self.dash_page)
        layout.setContentsMargins(40, 40, 40, 40)
        
        layout.addWidget(QLabel("DASHBOARD", objectName="Title"))
        
        # Stats cards
        stats_layout = QHBoxLayout()
        self.total_targets_lbl = QLabel("Total Targets: 0")
        self.total_vulns_lbl = QLabel("Total Vulnerabilities: 0")
        stats_layout.addWidget(self.total_targets_lbl)
        stats_layout.addWidget(self.total_vulns_lbl)
        layout.addLayout(stats_layout)
        
        # Severity Breakdown
        layout.addWidget(QLabel("\nVulnerability Severity Breakdown:"))
        self.severity_stats = QLabel("...")
        layout.addWidget(self.severity_stats)
        
        # Recent Activity
        layout.addWidget(QLabel("\nRecent Activity:"))
        self.recent_list = QListWidget()
        self.recent_list.setFixedHeight(200)
        layout.addWidget(self.recent_list)
        
        layout.addStretch()
        self.workspace.addWidget(self.dash_page)

    def init_target_workspace_ui(self):
        self.target_page = QWidget()
        layout = QVBoxLayout(self.target_page)
        
        # Target Header
        header = QHBoxLayout()
        self.target_title = QLabel("Target Name")
        self.target_title.setObjectName("Title")
        header.addWidget(self.target_title)
        header.addStretch()
        
        export_btn = QPushButton("EXPORT MARKDOWN")
        export_btn.clicked.connect(self.export_target_markdown)
        header.addWidget(export_btn)
        
        delete_btn = QPushButton("DELETE TARGET")
        delete_btn.setStyleSheet(f"border-color: {ACCENT_RED}; color: {ACCENT_RED};")
        delete_btn.clicked.connect(self.delete_current_target)
        header.addWidget(delete_btn)
        
        layout.addLayout(header)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Tab 1: Subdomains
        self.subdomains_tab = QWidget()
        sub_layout = QVBoxLayout(self.subdomains_tab)
        self.sub_table = ReconTable(["Subdomain", "IP", "Status", "Tech Stack", "Notes"], None, self.db, "subdomains")
        self.sub_table.data_changed.connect(self.refresh_dashboard)
        sub_layout.addWidget(self.sub_table)
        sub_btns = QHBoxLayout()
        import_sub_btn = QPushButton("Import from TXT")
        import_sub_btn.clicked.connect(self.import_subdomains)
        sub_btns.addWidget(import_sub_btn)
        sub_layout.addLayout(sub_btns)
        self.tabs.addTab(self.subdomains_tab, "SUBDOMAINS")
        
        # Tab 2: Ports
        self.ports_tab = QWidget()
        port_layout = QVBoxLayout(self.ports_tab)
        self.port_table = ReconTable(["IP", "Port", "Protocol", "Service", "Version", "Notes"], None, self.db, "ports")
        self.port_table.data_changed.connect(self.refresh_dashboard)
        port_layout.addWidget(self.port_table)
        port_btns = QHBoxLayout()
        import_nmap_btn = QPushButton("Import Nmap (-oN)")
        import_nmap_btn.clicked.connect(self.import_nmap)
        port_btns.addWidget(import_nmap_btn)
        port_layout.addLayout(port_btns)
        self.tabs.addTab(self.ports_tab, "PORTS & SERVICES")
        
        # Tab 3: Endpoints
        self.endpoints_tab = QWidget()
        end_layout = QVBoxLayout(self.endpoints_tab)
        self.end_table = ReconTable(["URL", "Method", "Parameters", "Status Code", "Notes"], None, self.db, "endpoints")
        self.end_table.data_changed.connect(self.refresh_dashboard)
        end_layout.addWidget(self.end_table)
        self.tabs.addTab(self.endpoints_tab, "ENDPOINTS")
        
        # Tab 4: Vulnerabilities
        self.vulns_tab = QWidget()
        vuln_layout = QVBoxLayout(self.vulns_tab)
        self.vuln_table = ReconTable(["Title", "Severity", "Status", "CVE/CWE", "Description"], None, self.db, "vulnerabilities")
        self.vuln_table.data_changed.connect(self.refresh_dashboard)
        vuln_layout.addWidget(self.vuln_table)
        self.tabs.addTab(self.vulns_tab, "VULNERABILITIES")
        
        # Tab 5: Notes
        self.notes_tab = QWidget()
        notes_layout = QVBoxLayout(self.notes_tab)
        self.notes_editor = QTextEdit()
        self.notes_editor.setFont(QFont("Courier New", 11))
        self.notes_editor.textChanged.connect(self.on_notes_changed)
        notes_layout.addWidget(self.notes_editor)
        self.notes_timer = QTimer()
        self.notes_timer.setSingleShot(True)
        self.notes_timer.timeout.connect(self.save_notes)
        self.tabs.addTab(self.notes_tab, "NOTES")
        
        layout.addWidget(self.tabs)
        self.workspace.addWidget(self.target_page)

    # --- ACTIONS ---

    def load_targets(self):
        self.target_list.clear()
        self.db.cursor.execute("SELECT id, name, domain, platform FROM targets ORDER BY name ASC")
        for row in self.db.cursor.fetchall():
            item = QListWidgetItem(f"{row[1]}\n{row[2]} [{row[3]}]")
            item.setData(Qt.ItemDataRole.UserRole, row[0])
            self.target_list.addItem(item)

    def create_new_target(self):
        dialog = NewTargetDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.cursor.execute(
                "INSERT INTO targets (name, domain, platform, date_added, last_modified) VALUES (?, ?, ?, ?, ?)",
                (data['name'], data['domain'], data['platform'], now, now)
            )
            target_id = self.db.cursor.lastrowid
            # Create empty notes entry
            self.db.cursor.execute("INSERT INTO notes (target_id, content, last_modified) VALUES (?, ?, ?)", (target_id, "", now))
            self.db.conn.commit()
            self.load_targets()
            self.refresh_dashboard()

    def on_target_selected(self, item):
        target_id = item.data(Qt.ItemDataRole.UserRole)
        self.open_target(target_id)

    def open_target(self, target_id):
        self.current_target_id = target_id
        self.db.cursor.execute("SELECT name FROM targets WHERE id = ?", (target_id,))
        name = self.db.cursor.fetchone()[0]
        self.target_title.setText(name)
        
        # Update table target IDs
        self.sub_table.target_id = target_id
        self.port_table.target_id = target_id
        self.end_table.target_id = target_id
        self.vuln_table.target_id = target_id
        
        # Load data
        self.refresh_target_data()
        self.workspace.setCurrentWidget(self.target_page)

    def refresh_target_data(self):
        if not self.current_target_id: return
        
        # Subdomains
        self.db.cursor.execute("SELECT * FROM subdomains WHERE target_id = ?", (self.current_target_id,))
        self.sub_table.load_data(self.db.cursor.fetchall())
        
        # Ports
        self.db.cursor.execute("SELECT * FROM ports WHERE target_id = ?", (self.current_target_id,))
        self.port_table.load_data(self.db.cursor.fetchall())
        
        # Endpoints
        self.db.cursor.execute("SELECT * FROM endpoints WHERE target_id = ?", (self.current_target_id,))
        self.end_table.load_data(self.db.cursor.fetchall())
        
        # Vulns
        self.db.cursor.execute("SELECT * FROM vulnerabilities WHERE target_id = ?", (self.current_target_id,))
        self.vuln_table.load_data(self.db.cursor.fetchall())
        
        # Notes
        self.db.cursor.execute("SELECT content FROM notes WHERE target_id = ?", (self.current_target_id,))
        note = self.db.cursor.fetchone()
        self.notes_editor.blockSignals(True)
        self.notes_editor.setPlainText(note[0] if note else "")
        self.notes_editor.blockSignals(False)

    def delete_current_target(self):
        if not self.current_target_id: return
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this target and all its data?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.cursor.execute("DELETE FROM targets WHERE id = ?", (self.current_target_id,))
            self.db.conn.commit()
            self.current_target_id = None
            self.load_targets()
            self.show_dashboard()

    def show_dashboard(self):
        self.current_target_id = None
        self.refresh_dashboard()
        self.workspace.setCurrentWidget(self.dash_page)

    def refresh_dashboard(self):
        # Stats
        self.db.cursor.execute("SELECT COUNT(*) FROM targets")
        self.total_targets_lbl.setText(f"Total Targets: {self.db.cursor.fetchone()[0]}")
        
        self.db.cursor.execute("SELECT COUNT(*) FROM vulnerabilities")
        self.total_vulns_lbl.setText(f"Total Vulnerabilities: {self.db.cursor.fetchone()[0]}")
        
        # Severity breakdown
        self.db.cursor.execute("SELECT severity, COUNT(*) FROM vulnerabilities GROUP BY severity")
        counts = dict(self.db.cursor.fetchall())
        sev_text = f"CRITICAL: {counts.get('Critical', 0)} | HIGH: {counts.get('High', 0)} | MEDIUM: {counts.get('Medium', 0)} | LOW: {counts.get('Low', 0)} | INFO: {counts.get('Info', 0)}"
        self.severity_stats.setText(sev_text)
        
        # Recent activity
        self.recent_list.clear()
        self.db.cursor.execute("SELECT name, last_modified FROM targets ORDER BY last_modified DESC LIMIT 5")
        for row in self.db.cursor.fetchall():
            self.recent_list.addItem(f"{row[0]} - modified {row[1]}")

    def on_notes_changed(self):
        self.notes_timer.start(1000) # 1 second debounce

    def save_notes(self):
        if not self.current_target_id: return
        content = self.notes_editor.toPlainText()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.cursor.execute("UPDATE notes SET content = ?, last_modified = ? WHERE target_id = ?", (content, now, self.current_target_id))
        self.db.conn.commit()
        self.db.update_last_modified(self.current_target_id)

    # --- IMPORTS ---

    def import_subdomains(self):
        if not self.current_target_id: return
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Subdomains", "", "Text Files (*.txt)")
        if file_path:
            with open(file_path, 'r') as f:
                for line in f:
                    sub = line.strip()
                    if sub:
                        self.db.cursor.execute("INSERT INTO subdomains (target_id, subdomain) VALUES (?, ?)", (self.current_target_id, sub))
            self.db.conn.commit()
            self.db.update_last_modified(self.current_target_id)
            self.refresh_target_data()

    def import_nmap(self):
        if not self.current_target_id: return
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Nmap Output", "", "Nmap Files (*.nmap *.txt)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    current_ip = ""
                    for line in f:
                        if "Nmap scan report for" in line:
                            parts = line.split()
                            current_ip = parts[-1].strip("()")
                        elif "/tcp" in line or "/udp" in line:
                            parts = line.split()
                            # 80/tcp open http
                            port_proto = parts[0].split("/")
                            port = port_proto[0]
                            proto = port_proto[1]
                            state = parts[1]
                            service = parts[2]
                            version = " ".join(parts[3:]) if len(parts) > 3 else ""
                            if state == "open":
                                self.db.cursor.execute(
                                    "INSERT INTO ports (target_id, ip, port, protocol, service, version) VALUES (?, ?, ?, ?, ?, ?)",
                                    (self.current_target_id, current_ip, port, proto, service, version)
                                )
                self.db.conn.commit()
                self.db.update_last_modified(self.current_target_id)
                self.refresh_target_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to parse Nmap file: {str(e)}")

    # --- SEARCH & EXPORT ---

    def perform_global_search(self):
        query = self.search_bar.text().strip()
        if not query: return
        
        results_dialog = QDialog(self)
        results_dialog.setWindowTitle(f"Search Results: {query}")
        results_dialog.setMinimumSize(600, 400)
        layout = QVBoxLayout(results_dialog)
        
        res_list = QListWidget()
        layout.addWidget(res_list)
        
        # Search targets
        self.db.cursor.execute("SELECT id, name FROM targets WHERE name LIKE ? OR domain LIKE ?", (f"%{query}%", f"%{query}%"))
        for r in self.db.cursor.fetchall():
            item = QListWidgetItem(f"[Target] {r[1]}")
            item.setData(Qt.ItemDataRole.UserRole, r[0])
            res_list.addItem(item)
            
        # Search Subdomains
        self.db.cursor.execute("SELECT t.id, t.name, s.subdomain FROM subdomains s JOIN targets t ON s.target_id = t.id WHERE s.subdomain LIKE ? OR s.notes LIKE ?", (f"%{query}%", f"%{query}%"))
        for r in self.db.cursor.fetchall():
            item = QListWidgetItem(f"[Subdomain] {r[2]} (Target: {r[1]})")
            item.setData(Qt.ItemDataRole.UserRole, r[0])
            res_list.addItem(item)
            
        # Search Vulns
        self.db.cursor.execute("SELECT t.id, t.name, v.title FROM vulnerabilities v JOIN targets t ON v.target_id = t.id WHERE v.title LIKE ? OR v.description LIKE ?", (f"%{query}%", f"%{query}%"))
        for r in self.db.cursor.fetchall():
            item = QListWidgetItem(f"[Vulnerability] {r[2]} (Target: {r[1]})")
            item.setData(Qt.ItemDataRole.UserRole, r[0])
            res_list.addItem(item)

        def on_res_clicked(item):
            target_id = item.data(Qt.ItemDataRole.UserRole)
            self.open_target(target_id)
            results_dialog.accept()

        res_list.itemClicked.connect(on_res_clicked)
        results_dialog.exec()

    def export_target_markdown(self):
        if not self.current_target_id: return
        
        self.db.cursor.execute("SELECT name, domain FROM targets WHERE id = ?", (self.current_target_id,))
        target_info = self.db.cursor.fetchone()
        name = target_info[0]
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        file_name = f"reconvault_{name.replace(' ', '_')}_{date_str}.md"
        default_path = Path.home() / "Desktop" / file_name
        
        # Ensure Desktop exists or fallback to home
        if not os.path.exists(default_path.parent):
            default_path = Path.home() / file_name

        md = f"# ReconVault Report — {name}\n"
        md += f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Subdomains
        md += "## Subdomains\n| Subdomain | IP | Status | Tech Stack | Notes |\n|---|---|---|---|---|\n"
        self.db.cursor.execute("SELECT subdomain, ip, status, tech_stack, notes FROM subdomains WHERE target_id = ?", (self.current_target_id,))
        for r in self.db.cursor.fetchall():
            md += f"| {' | '.join([str(x) if x else '' for x in r])} |\n"
        
        # Ports
        md += "\n## Ports & Services\n| IP | Port | Proto | Service | Version | Notes |\n|---|---|---|---|---|---|\n"
        self.db.cursor.execute("SELECT ip, port, protocol, service, version, notes FROM ports WHERE target_id = ?", (self.current_target_id,))
        for r in self.db.cursor.fetchall():
            md += f"| {' | '.join([str(x) if x else '' for x in r])} |\n"
            
        # Endpoints
        md += "\n## Endpoints\n| URL | Method | Params | Status | Notes |\n|---|---|---|---|---|\n"
        self.db.cursor.execute("SELECT url, method, parameters, status_code, notes FROM endpoints WHERE target_id = ?", (self.current_target_id,))
        for r in self.db.cursor.fetchall():
            md += f"| {' | '.join([str(x) if x else '' for x in r])} |\n"
            
        # Vulns
        md += "\n## Vulnerabilities\n| Title | Severity | Status | CVE/CWE | Description |\n|---|---|---|---|---|\n"
        self.db.cursor.execute("SELECT title, severity, status, cve_cwe, description FROM vulnerabilities WHERE target_id = ?", (self.current_target_id,))
        for r in self.db.cursor.fetchall():
            md += f"| {' | '.join([str(x) if x else '' for x in r])} |\n"
            
        # Notes
        md += "\n## Notes\n"
        self.db.cursor.execute("SELECT content FROM notes WHERE target_id = ?", (self.current_target_id,))
        note = self.db.cursor.fetchone()
        md += note[0] if note else ""
        
        try:
            with open(default_path, 'w') as f:
                f.write(md)
            QMessageBox.information(self, "Export Successful", f"Report saved to: {default_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not save file: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set global palette for some native dialogs
    palette = QPalette()
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Window, QColor(DARK_BG))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.WindowText, QColor(TEXT_COLOR))
    app.setPalette(palette)
    
    window = ReconVault()
    window.show()
    sys.exit(app.exec())
