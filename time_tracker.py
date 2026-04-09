#!/usr/bin/env python3
"""
TimeTrack — PySide6 dark-themed time tracking app.
Multi-project, Jira worklog sync, manual entry, nested session log.
"""

import sys
import os
import json
import time
import csv
import io
import requests
from datetime import datetime, timedelta, date as date_type

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox, QCheckBox,
    QTextEdit, QScrollArea, QFrame, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QSizePolicy, QAbstractItemView, QHeaderView,
    QSpacerItem, QDateEdit, QTimeEdit, QSplitter,
    QFileDialog, QButtonGroup, QSystemTrayIcon, QMenu, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QDate, QTime, QSize, QPoint
from PySide6.QtGui import QFont, QColor, QFontDatabase, QPixmap, QPainter, QBrush, QPen, QIcon, QAction

# ── Theme system ─────────────────────────────────────────────────────────────
DATA_FILE = os.path.expanduser("~/.timetrack_data.json")

DARK_THEME = {
    "BG":       "#1a1a2e", "SURFACE":  "#16213e", "CARD":     "#0f3460",
    "ACCENT":   "#e94560", "ACCENT2":  "#533483", "TEXT":     "#eaeaea",
    "TEXT_DIM": "#8892b0", "SUCCESS":  "#64ffda", "WARNING":  "#ffd166",
    "BORDER":   "#2a2a4a", "ALT_ROW":  "#1c2440", "TREE_HOVER":"#1e2d50",
}
LIGHT_THEME = {
    "BG":        "#f5f6fa", "SURFACE":   "#ffffff", "CARD":      "#eef0f6",
    "ACCENT":    "#e94560", "ACCENT2":   "#6a4fc8", "TEXT":      "#1a1a2e",
    "TEXT_DIM":  "#5e6278", "SUCCESS":   "#0a8f6f", "WARNING":   "#b06000",
    "BORDER":    "#d0d4e4", "ALT_ROW":   "#f0f2f8", "TREE_HOVER":"#e4e8f4",
}

# Mutable globals — updated by set_theme()
BG = DARK_THEME["BG"]; SURFACE = DARK_THEME["SURFACE"]; CARD = DARK_THEME["CARD"]
ACCENT = DARK_THEME["ACCENT"]; ACCENT2 = DARK_THEME["ACCENT2"]
TEXT = DARK_THEME["TEXT"]; TEXT_DIM = DARK_THEME["TEXT_DIM"]
SUCCESS = DARK_THEME["SUCCESS"]; WARNING = DARK_THEME["WARNING"]
BORDER = DARK_THEME["BORDER"]; ALT_ROW = DARK_THEME["ALT_ROW"]
TREE_HOVER = DARK_THEME["TREE_HOVER"]

# Fixed colors (same in both themes)
JIRA_BLUE = "#0052cc"
GREEN     = "#27ae60"; GREEN_H = "#2ecc71"
RED       = "#c0392b"; RED_H   = "#e74c3c"
GREY      = "#7f8c8d"; GREY_H  = "#95a5a6"
PURPLE    = "#8e44ad"; PURPLE_H = "#9b59b6"
BLUE      = "#2980b9"; BLUE_H   = "#3498db"

def set_theme(name):
    """Update all colour globals for the chosen theme ('dark' or 'light')."""
    import builtins
    palette = DARK_THEME if name == "dark" else LIGHT_THEME
    g = globals()
    for k, v in palette.items():
        g[k] = v

CURRENT_THEME = "dark"

def build_stylesheet():
    """Generate the Qt stylesheet using the current theme globals."""
    return f"""
QMainWindow, QDialog, QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: -apple-system, "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
}}
QLineEdit {{
    background-color: {CARD};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 7px 10px;
    font-size: 12px;
    selection-background-color: {JIRA_BLUE};
}}
QLineEdit:focus {{ border: 1px solid {JIRA_BLUE}; }}
QSpinBox {{
    background-color: {CARD};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 24px;
    font-weight: bold;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {SURFACE};
    border: none;
    width: 22px;
    border-radius: 3px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {BORDER};
}}
QCheckBox {{ color: {TEXT}; spacing: 8px; font-size: 12px; }}
QCheckBox::indicator {{
    width: 17px; height: 17px;
    background-color: {CARD}; border: 1px solid {BORDER}; border-radius: 4px;
}}
QCheckBox::indicator:checked {{
    background-color: {JIRA_BLUE}; border: 1px solid {JIRA_BLUE};
}}
QTextEdit {{
    background-color: {SURFACE}; color: {TEXT};
    border: none; padding: 10px; font-size: 12px;
    selection-background-color: {ACCENT2};
}}
QScrollBar:vertical {{
    background: {SURFACE}; width: 8px; border: none; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 4px; min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {SURFACE}; height: 8px; border: none; margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER}; border-radius: 4px; min-width: 24px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollArea {{ border: none; background-color: {SURFACE}; }}
QTreeWidget {{
    background-color: {SURFACE}; color: {TEXT};
    border: none; outline: none;
    alternate-background-color: {ALT_ROW};
    show-decoration-selected: 1;
}}
QTreeWidget::item {{ height: 38px; padding-left: 2px; border: none; }}
QTreeWidget::item:selected {{ background-color: {ACCENT2}; color: {TEXT}; }}
QTreeWidget::item:hover:!selected {{ background-color: {TREE_HOVER}; }}
QTreeWidget::branch {{
    background-color: {SURFACE};
}}
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {{
    border-image: none; image: none;
}}
QHeaderView::section {{
    background-color: {CARD}; color: {TEXT_DIM};
    border: none; border-right: 1px solid {BORDER};
    padding: 8px 6px; font-size: 10px; font-weight: bold;
}}
QHeaderView::section:last {{ border-right: none; }}
QDateEdit, QTimeEdit {{
    background-color: {CARD}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 5px;
    padding: 7px 10px; font-size: 13px;
}}
QDateEdit:focus, QTimeEdit:focus {{ border: 1px solid {JIRA_BLUE}; }}
QDateEdit::drop-down, QTimeEdit::drop-down {{
    border: none; background: {SURFACE}; width: 20px;
}}
QCalendarWidget QWidget {{ background-color: {SURFACE}; color: {TEXT}; }}
QCalendarWidget QAbstractItemView {{
    background-color: {SURFACE}; color: {TEXT};
    selection-background-color: {JIRA_BLUE};
}}
QMessageBox {{ background-color: {SURFACE}; }}
QMessageBox QLabel {{ color: {TEXT}; font-size: 13px; }}
QMessageBox QPushButton {{
    background-color: {JIRA_BLUE}; color: white;
    border: none; border-radius: 5px;
    padding: 7px 22px; font-weight: bold; min-width: 80px;
}}
QMessageBox QPushButton:hover {{ background-color: #0065ff; }}
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"projects": [], "sessions": [],
            "jira": {"url": "", "email": "", "token": ""},
            "ticket_map": {}, "categories": [], "category_map": {},
            "archived_projects": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def fmt_duration(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def parse_hms(h, m, s):
    try:
        total = int(h) * 3600 + int(m) * 60 + int(s)
        return total if total > 0 else None
    except (ValueError, TypeError):
        return None

def total_seconds_for_project(sessions, project):
    return sum(s["duration"] for s in sessions if s["project"] == project)

def styled_btn(text, color, hover, text_color="#ffffff", font_size=11, bold=True, min_w=None):
    """Return a styled QPushButton."""
    b = QPushButton(text)
    weight = "bold" if bold else "normal"
    b.setStyleSheet(f"""
        QPushButton {{
            background-color: {color}; color: {text_color};
            border: none; border-radius: 5px;
            padding: 6px 14px; font-size: {font_size}px; font-weight: {weight};
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {color}; }}
    """)
    b.setCursor(Qt.PointingHandCursor)
    if min_w:
        b.setMinimumWidth(min_w)
    return b

def card_frame(bg=CARD, border=BORDER, radius=8):
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background-color: {bg};
            border: 1px solid {border};
            border-radius: {radius}px;
        }}
    """)
    return f

def section_label(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; font-weight: bold; background: transparent; border: none;")
    return lbl

def dim_label(text, size=10):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: {size}px; background: transparent; border: none;")
    return lbl


# ── Stat window presets ───────────────────────────────────────────────────────
# Each value is a tuple: (display_label, fn(sessions) -> total_seconds)

def _window_fn(sessions, start_date_str=None, end_date_str=None):
    total = 0
    for s in sessions:
        d = s.get("date", "")
        if start_date_str and d < start_date_str:
            continue
        if end_date_str and d > end_date_str:
            continue
        total += s["duration"]
    return total

def _today_str():     return datetime.now().strftime("%Y-%m-%d")
def _yesterday_str(): return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
def _n_days_ago(n):   return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")
def _month_start():   return datetime.now().replace(day=1).strftime("%Y-%m-%d")
def _week_start():    return (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
def _year_start():    return datetime.now().replace(month=1, day=1).strftime("%Y-%m-%d")

STAT_WINDOWS = {
    "today":       ("Today",        lambda s: _window_fn(s, _today_str(),     _today_str())),
    "yesterday":   ("Yesterday",    lambda s: _window_fn(s, _yesterday_str(), _yesterday_str())),
    "this_week":   ("This Week",    lambda s: _window_fn(s, _week_start())),
    "last_7":      ("Last 7 Days",  lambda s: _window_fn(s, _n_days_ago(7))),
    "this_month":  ("This Month",   lambda s: _window_fn(s, _month_start())),
    "last_30":     ("Last 30 Days", lambda s: _window_fn(s, _n_days_ago(30))),
    "last_90":     ("Last 90 Days", lambda s: _window_fn(s, _n_days_ago(90))),
    "last_180":    ("Last 6 Months",lambda s: _window_fn(s, _n_days_ago(180))),
    "this_year":   ("This Year",    lambda s: _window_fn(s, _year_start())),
    "all_time":    ("All Time",     lambda s: _window_fn(s)),
}

DEFAULT_STAT_CONFIGS = ["today", "last_7", "all_time"]

def get_stat_colors():
    """Return stat card value colours using the current theme."""
    return [SUCCESS, WARNING, ACCENT]


# ── Tray icon helpers ─────────────────────────────────────────────────────────

def make_tray_pixmap(color_hex):
    """22×22 filled circle in the given hex color."""
    pm = QPixmap(22, 22)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QBrush(QColor(color_hex)))
    p.setPen(Qt.NoPen)
    p.drawEllipse(3, 3, 16, 16)
    p.end()
    return pm

# ── Jira API ──────────────────────────────────────────────────────────────────

def jira_post_worklog(jira_cfg, ticket_key, started_ts, duration_secs,
                      comment="Logged via TimeTrack"):
    if duration_secs < 60:
        return False, "Session too short (< 60s) to log to Jira."
    base_url = jira_cfg["url"].rstrip("/")
    email, token = jira_cfg["email"], jira_cfg["token"]
    if not base_url or not email or not token:
        return False, "Jira credentials incomplete. Check Jira Settings."
    started_str = datetime.utcfromtimestamp(started_ts).strftime("%Y-%m-%dT%H:%M:%S.000+0000")
    payload = {
        "timeSpentSeconds": int(duration_secs),
        "started": started_str,
        "comment": {"type": "doc", "version": 1,
                    "content": [{"type": "paragraph",
                                 "content": [{"type": "text", "text": comment}]}]}
    }
    try:
        resp = requests.post(f"{base_url}/rest/api/3/issue/{ticket_key}/worklog",
                             json=payload, auth=(email, token),
                             headers={"Accept": "application/json"}, timeout=10)
        if resp.status_code in (200, 201):
            worklog_id = resp.json().get("id")
            return True, None, worklog_id
        try:
            body = resp.json()
            msgs = body.get("errorMessages") or [str(body.get("errors", resp.text))]
            return False, "; ".join(msgs), None
        except Exception:
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}", None
    except requests.exceptions.ConnectionError:
        return False, "Could not connect to Jira. Check your URL and network.", None
    except requests.exceptions.Timeout:
        return False, "Request timed out. Jira may be unreachable.", None
    except Exception as ex:
        return False, str(ex), None


def jira_delete_worklog(jira_cfg, ticket_key, worklog_id):
    """Delete a worklog entry from Jira. Returns (True, None) or (False, err_str)."""
    base_url = jira_cfg["url"].rstrip("/")
    email, token = jira_cfg["email"], jira_cfg["token"]
    if not base_url or not email or not token:
        return False, "Jira credentials incomplete."
    url = f"{base_url}/rest/api/3/issue/{ticket_key}/worklog/{worklog_id}"
    try:
        resp = requests.delete(url, auth=(email, token),
                               headers={"Accept": "application/json"}, timeout=10)
        if resp.status_code == 204:
            return True, None
        try:
            body = resp.json()
            msgs = body.get("errorMessages") or [str(body.get("errors", resp.text))]
            return False, "; ".join(msgs)
        except Exception:
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except requests.exceptions.ConnectionError:
        return False, "Could not connect to Jira."
    except requests.exceptions.Timeout:
        return False, "Request timed out."
    except Exception as ex:
        return False, str(ex)


def jira_get_issue(jira_cfg, ticket_key):
    base_url = jira_cfg["url"].rstrip("/")
    email, token = jira_cfg["email"], jira_cfg["token"]
    if not base_url or not email or not token:
        return None, "Jira credentials not configured."
    url = f"{base_url}/rest/api/3/issue/{ticket_key}?fields=summary,description,status,assignee,priority"
    try:
        resp = requests.get(url, auth=(email, token),
                            headers={"Accept": "application/json"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            fields = data.get("fields", {})
            desc     = _extract_adf_text(fields.get("description"))
            assignee = (fields.get("assignee") or {}).get("displayName", "Unassigned")
            status   = (fields.get("status")   or {}).get("name", "Unknown")
            priority = (fields.get("priority") or {}).get("name", "None")
            return {
                "key": data.get("key", ticket_key),
                "summary": fields.get("summary", "(No summary)"),
                "description": desc or "(No description)",
                "status": status, "assignee": assignee, "priority": priority,
            }, None
        try:
            body = resp.json()
            msgs = body.get("errorMessages") or [str(body.get("errors", resp.text))]
            return None, "; ".join(msgs)
        except Exception:
            return None, f"HTTP {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return None, "Could not connect to Jira."
    except requests.exceptions.Timeout:
        return None, "Request timed out."
    except Exception as ex:
        return None, str(ex)

def _extract_adf_text(node):
    if node is None: return ""
    if isinstance(node, str): return node
    if node.get("type") == "text": return node.get("text", "")
    parts = [_extract_adf_text(c) for c in node.get("content", [])]
    sep = "\n" if node.get("type") in ("paragraph","heading","listItem","bulletList","orderedList") else ""
    return sep.join(p for p in parts if p)

# ── QThread Workers ───────────────────────────────────────────────────────────

class JiraSyncWorker(QThread):
    done = Signal(str, bool, object, float, str, object)  # ticket, ok, err, start_ts, project, worklog_id

    def __init__(self, jira_cfg, session, duration_secs):
        super().__init__()
        self._cfg      = jira_cfg
        self._session  = session
        self._duration = duration_secs

    def run(self):
        ok, err, worklog_id = jira_post_worklog(
            self._cfg, self._session["ticket"],
            self._session["start"], self._duration,
            comment=f"TimeTrack session on {self._session['project']}"
        )
        self.done.emit(self._session["ticket"], ok, err,
                       self._session["start"], self._session["project"], worklog_id)


class JiraFetchWorker(QThread):
    done = Signal(object, object)  # issue or None, err or None

    def __init__(self, jira_cfg, ticket_key):
        super().__init__()
        self._cfg = jira_cfg
        self._key = ticket_key

    def run(self):
        issue, err = jira_get_issue(self._cfg, self._key)
        self.done.emit(issue, err)

class JiraDeleteWorker(QThread):
    done = Signal(bool, str)  # ok, err

    def __init__(self, jira_cfg, ticket_key, worklog_id):
        super().__init__()
        self._cfg        = jira_cfg
        self._ticket     = ticket_key
        self._worklog_id = worklog_id

    def run(self):
        ok, err = jira_delete_worklog(self._cfg, self._ticket, self._worklog_id)
        self.done.emit(ok, err or "")


class JiraAutoArchiveWorker(QThread):
    """
    Checks the Jira status of every project that has a ticket key.
    Emits a list of project names that should be auto-archived because their
    ticket is in a terminal state (Done / Closed / Resolved / Won't Do).
    """
    done = Signal(list, str)   # (projects_to_archive, error_or_empty)

    TERMINAL_STATUSES = {"done", "closed", "resolved", "won't do", "wont do",
                         "complete", "completed", "cancelled", "canceled"}

    def __init__(self, jira_cfg, ticket_map):
        super().__init__()
        self._cfg        = jira_cfg
        self._ticket_map = dict(ticket_map)   # {project: ticket_key}

    def run(self):
        to_archive = []
        errors     = []
        for proj, ticket in self._ticket_map.items():
            if not ticket:
                continue
            issue, err = jira_get_issue(self._cfg, ticket)
            if err:
                errors.append(f"{ticket}: {err}")
                continue
            status = (issue.get("status") or "").strip().lower()
            if status in self.TERMINAL_STATUSES:
                to_archive.append(proj)
        err_msg = "\n".join(errors) if errors else ""
        self.done.emit(to_archive, err_msg)


# ── Spinbox trio helper ───────────────────────────────────────────────────────

def hms_spinboxes(h=0, m=0, s=0):
    """Returns (layout, h_spinbox, m_spinbox, s_spinbox)."""
    row = QHBoxLayout()
    row.setSpacing(0)
    spinboxes = []
    for val, max_val, lbl in [(h, 99, "HRS"), (m, 59, "MIN"), (s, 59, "SEC")]:
        col = QVBoxLayout()
        col.setSpacing(4)
        label = QLabel(lbl)
        label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 8px; font-weight: bold; background: transparent; border: none;")
        label.setAlignment(Qt.AlignCenter)
        sb = QSpinBox()
        sb.setRange(0, max_val)
        sb.setValue(val)
        sb.setFixedWidth(86)
        sb.setAlignment(Qt.AlignCenter)
        sb.setButtonSymbols(QSpinBox.PlusMinus)
        col.addWidget(label)
        col.addWidget(sb)
        spinboxes.append(sb)
        row.addLayout(col)
        if lbl != "SEC":
            sep = QLabel(":")
            sep.setStyleSheet(f"color: {TEXT_DIM}; font-size: 30px; font-weight: bold; background: transparent; border: none;")
            sep.setAlignment(Qt.AlignBottom)
            sep.setContentsMargins(4, 0, 4, 8)
            row.addWidget(sep)
    return row, spinboxes[0], spinboxes[1], spinboxes[2]

# ── Jira Settings Dialog ──────────────────────────────────────────────────────

class JiraTestWorker(QThread):
    """Hits the Jira /myself endpoint to validate credentials."""
    done = Signal(bool, str)  # ok, message

    def __init__(self, cfg):
        super().__init__()
        self._cfg = cfg

    def run(self):
        import requests as _req
        base  = self._cfg["url"].rstrip("/")
        email = self._cfg["email"]
        token = self._cfg["token"]
        try:
            resp = _req.get(
                f"{base}/rest/api/3/myself",
                auth=(email, token),
                headers={"Accept": "application/json"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                name = data.get("displayName") or data.get("emailAddress") or "Unknown"
                self.done.emit(True, f"Connected as {name}")
            elif resp.status_code == 401:
                self.done.emit(False, "Authentication failed — check your email and API token.")
            elif resp.status_code == 403:
                self.done.emit(False, "Access denied — token may lack required permissions.")
            elif resp.status_code == 404:
                self.done.emit(False, "Jira URL not found — check your base URL.")
            else:
                try:
                    msgs = resp.json().get("errorMessages") or [resp.text[:120]]
                except Exception:
                    msgs = [resp.text[:120]]
                self.done.emit(False, f"HTTP {resp.status_code}: {msgs[0]}")
        except _req.exceptions.ConnectionError:
            self.done.emit(False, "Could not connect — check the base URL and your network.")
        except _req.exceptions.Timeout:
            self.done.emit(False, "Connection timed out.")
        except Exception as ex:
            self.done.emit(False, str(ex))


class JiraSettingsDialog(QDialog):
    def __init__(self, parent, jira_cfg):
        super().__init__(parent)
        self.setWindowTitle("Jira Settings")
        self.setFixedWidth(460)
        self.setModal(True)
        self._test_worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Jira Integration")
        title.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        layout.addWidget(dim_label("Connect TimeTrack to your Jira Cloud instance."))

        card = card_frame(SURFACE)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)

        def field(lbl, val, placeholder="", password=False):
            card_layout.addWidget(section_label(lbl))
            e = QLineEdit(val)
            e.setPlaceholderText(placeholder)
            if password:
                e.setEchoMode(QLineEdit.Password)
            card_layout.addWidget(e)
            return e

        self.e_url   = field("JIRA BASE URL", jira_cfg.get("url", ""),
                             "https://yourorg.atlassian.net")
        self.e_email = field("ATLASSIAN EMAIL", jira_cfg.get("email", ""))
        self.e_token = field("API TOKEN", jira_cfg.get("token", ""), password=True)
        layout.addWidget(card)

        layout.addWidget(dim_label(
            "Generate your API token at: id.atlassian.com → Security → API tokens", 9))

        # ── Test connection result label ────────────────────────────────────────────────
        self._test_result_card = card_frame(SURFACE)
        self._test_result_card.setVisible(False)
        trc_lay = QHBoxLayout(self._test_result_card)
        trc_lay.setContentsMargins(14, 10, 14, 10)
        self._test_lbl = QLabel("")
        self._test_lbl.setWordWrap(True)
        self._test_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent; border: none;")
        trc_lay.addWidget(self._test_lbl)
        layout.addWidget(self._test_result_card)

        # ── Button row ────────────────────────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self._test_btn = styled_btn("⚡ Test Connection", CARD, SURFACE, TEXT_DIM, font_size=10)
        self._test_btn.setToolTip("Verify that the credentials can connect to your Jira instance")
        self._test_btn.clicked.connect(self._test_connection)
        btn_row.addWidget(self._test_btn)
        btn_row.addStretch()
        cancel = styled_btn("Cancel", GREY, GREY_H)
        cancel.clicked.connect(self.reject)
        save = styled_btn("Save", JIRA_BLUE, "#0065ff", min_w=90)
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

    def _current_cfg(self):
        return {
            "url":   self.e_url.text().strip(),
            "email": self.e_email.text().strip(),
            "token": self.e_token.text().strip(),
        }

    def _test_connection(self):
        cfg = self._current_cfg()
        if not cfg["url"] or not cfg["email"] or not cfg["token"]:
            self._show_result(False, "Please fill in all three fields before testing.")
            return
        self._test_btn.setEnabled(False)
        self._test_btn.setText("⟳ Testing…")
        self._test_result_card.setVisible(False)
        self._test_worker = JiraTestWorker(cfg)
        self._test_worker.done.connect(self._on_test_done)
        self._test_worker.start()

    def _on_test_done(self, ok, message):
        self._test_btn.setEnabled(True)
        self._test_btn.setText("⚡ Test Connection")
        self._show_result(ok, message)

    def _show_result(self, ok, message):
        color  = SUCCESS if ok else "#e94560"
        prefix = "✔  " if ok else "✖  "
        self._test_lbl.setText(prefix + message)
        self._test_lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; background: transparent; border: none;"
        )
        self._test_result_card.setVisible(True)

    def _save(self):
        self._result = self._current_cfg()
        self.accept()

    def get_result(self):
        return getattr(self, "_result", None)
# ── Project Dialog ────────────────────────────────────────────────────────────

class ProjectDialog(QDialog):
    # Palette of tag background colors (cycles by category index)
    TAG_COLORS = [
        "#6a4fc8", "#0a8f6f", "#b06000", "#0052cc",
        "#c0392b", "#1a6b8a", "#7d3c98", "#1e8449",
    ]

    def __init__(self, parent, name="", ticket="", all_categories=None, assigned_cats=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Project" if name else "New Project")
        self.setFixedWidth(440)
        self.setModal(True)

        self._all_cats      = list(all_categories or [])
        self._assigned_cats = set(assigned_cats or [])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Edit Project" if name else "New Project")
        title.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # ── Name + Ticket card ────────────────────────────────────────────────
        card = card_frame(SURFACE)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.setSpacing(10)

        cl.addWidget(section_label("PROJECT NAME"))
        self.e_name = QLineEdit(name)
        cl.addWidget(self.e_name)

        cl.addWidget(section_label("JIRA TICKET KEY  (optional, e.g. PROJ-42)"))
        self.e_ticket = QLineEdit(ticket)
        self.e_ticket.setPlaceholderText("e.g. PROJ-42")
        cl.addWidget(self.e_ticket)
        layout.addWidget(card)

        # ── Categories card ───────────────────────────────────────────────────
        cat_card = card_frame(SURFACE)
        cat_cl = QVBoxLayout(cat_card)
        cat_cl.setContentsMargins(16, 12, 16, 14)
        cat_cl.setSpacing(8)

        cat_hdr = QHBoxLayout()
        cat_hdr.addWidget(section_label("CATEGORIES"))
        cat_hdr.addStretch()
        cat_hint = QLabel("assign one or more")
        cat_hint.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; background: transparent;")
        cat_hdr.addWidget(cat_hint)
        cat_cl.addLayout(cat_hdr)

        # Scrollable checkbox list for existing categories
        self._cat_scroll = QScrollArea()
        self._cat_scroll.setWidgetResizable(True)
        self._cat_scroll.setFixedHeight(100)
        self._cat_scroll.setStyleSheet(
            f"QScrollArea {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 5px; }}"
            f"QScrollArea > QWidget > QWidget {{ background: transparent; }}"
        )
        self._cat_inner = QWidget()
        self._cat_inner.setStyleSheet("background: transparent;")
        self._cat_vb = QVBoxLayout(self._cat_inner)
        self._cat_vb.setSpacing(4)
        self._cat_vb.setContentsMargins(8, 6, 8, 6)
        self._cat_checks = {}   # cat_name -> QCheckBox
        self._rebuild_cat_list()
        self._cat_scroll.setWidget(self._cat_inner)
        cat_cl.addWidget(self._cat_scroll)

        # Add new category inline
        new_row = QHBoxLayout()
        new_row.setSpacing(6)
        self._new_cat_edit = QLineEdit()
        self._new_cat_edit.setPlaceholderText("New category name…")
        self._new_cat_edit.returnPressed.connect(self._add_new_category)
        new_row.addWidget(self._new_cat_edit, 1)
        add_cat_btn = styled_btn("+ Add", BLUE, BLUE_H, font_size=10)
        add_cat_btn.setFixedWidth(64)
        add_cat_btn.clicked.connect(self._add_new_category)
        new_row.addWidget(add_cat_btn)
        cat_cl.addLayout(new_row)
        layout.addWidget(cat_card)

        layout.addWidget(dim_label(
            "If a ticket is set, time is logged to Jira when the timer stops.", 9))

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = styled_btn("Cancel", GREY, GREY_H)
        cancel.clicked.connect(self.reject)
        save = styled_btn("Save", GREEN, GREEN_H, "#0a0a0a", min_w=90)
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

        self.e_name.setFocus()

    def _rebuild_cat_list(self):
        # Remove existing widgets
        while self._cat_vb.count():
            item = self._cat_vb.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cat_checks.clear()

        if not self._all_cats:
            hint = QLabel("No categories yet — type one above and click + Add")
            hint.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; background: transparent;")
            hint.setWordWrap(True)
            self._cat_vb.addWidget(hint)
            return

        for cat in self._all_cats:
            cb = QCheckBox(cat)
            cb.setChecked(cat in self._assigned_cats)
            self._cat_checks[cat] = cb
            self._cat_vb.addWidget(cb)
        self._cat_vb.addStretch()

    def _add_new_category(self):
        name = self._new_cat_edit.text().strip()
        if not name:
            return
        if name in self._all_cats:
            # Just check it
            if name in self._cat_checks:
                self._cat_checks[name].setChecked(True)
        else:
            self._all_cats.append(name)
            self._assigned_cats.add(name)
            self._rebuild_cat_list()
            # Auto-check the newly added one
            if name in self._cat_checks:
                self._cat_checks[name].setChecked(True)
        self._new_cat_edit.clear()

    def _save(self):
        name = self.e_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Required", "Project name cannot be empty.")
            return
        selected_cats = [cat for cat, cb in self._cat_checks.items() if cb.isChecked()]
        self._result = {
            "name":       name,
            "ticket":     self.e_ticket.text().strip().upper(),
            "categories": selected_cats,
            "all_categories": self._all_cats,  # updated list including any newly added
        }
        self.accept()

    def get_result(self):
        return getattr(self, "_result", None)


# ── Edit Time & Sync Dialog ───────────────────────────────────────────────────

class EditTimeSyncDialog(QDialog):
    def __init__(self, parent, project, ticket, duration_secs):
        super().__init__(parent)
        self.setWindowTitle("Review & Sync Time")
        self.setFixedWidth(420)
        self.setModal(True)
        self._action   = None
        self._duration = duration_secs

        h = int(duration_secs // 3600)
        m = int((duration_secs % 3600) // 60)
        s = int(duration_secs % 60)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Review Time Before Syncing")
        title.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        layout.addWidget(dim_label(f"Tracked on  {project}  →  {ticket}"))

        card = card_frame(SURFACE)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.setSpacing(10)
        cl.addWidget(section_label("TIME TO LOG"))

        hms_row, self.sb_h, self.sb_m, self.sb_s = hms_spinboxes(h, m, s)
        hms_container = QWidget()
        hms_container.setStyleSheet("background: transparent;")
        hms_container.setLayout(hms_row)
        cl.addWidget(hms_container)
        layout.addWidget(card)

        layout.addWidget(dim_label(
            "Jira requires at least 1 minute. Edits here only affect what is sent to Jira — "
            "raw tracked time is always saved locally.", 9))

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        skip = styled_btn("Skip Sync", GREY, GREY_H)
        skip.clicked.connect(self._skip)
        sync = styled_btn("Sync to Jira", JIRA_BLUE, "#0065ff", min_w=120)
        sync.clicked.connect(self._sync)
        btn_row.addWidget(skip)
        btn_row.addWidget(sync)
        layout.addLayout(btn_row)

    def _sync(self):
        secs = parse_hms(self.sb_h.value(), self.sb_m.value(), self.sb_s.value())
        if not secs or secs < 60:
            QMessageBox.warning(self, "Too Short",
                "Jira requires at least 1 minute (00:01:00).\n"
                "Please adjust the time or choose Skip Sync.")
            return
        self._duration = secs
        self._action = "sync"
        self.accept()

    def _skip(self):
        self._action = "skip"
        self.reject()

    def get_action(self):   return self._action
    def get_duration(self): return self._duration

# ── Edit Session Dialog ───────────────────────────────────────────────────────

class EditSessionDialog(QDialog):
    def __init__(self, parent, session):
        super().__init__(parent)
        self.setWindowTitle("Edit Session")
        self.setFixedWidth(420)
        self.setModal(True)

        proj   = session.get("project", "")
        ticket = session.get("ticket", "")
        date   = datetime.fromtimestamp(session["start"]).strftime("%b %d, %Y  %H:%M")
        dur    = session["duration"]
        h = int(dur // 3600); m = int((dur % 3600) // 60); s = int(dur % 60)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Edit Session")
        title.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        layout.addWidget(dim_label(f"{proj}   •   {date}"))

        card = card_frame(SURFACE)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.setSpacing(10)
        cl.addWidget(section_label("DURATION"))

        hms_row, self.sb_h, self.sb_m, self.sb_s = hms_spinboxes(h, m, s)
        hms_container = QWidget()
        hms_container.setStyleSheet("background: transparent;")
        hms_container.setLayout(hms_row)
        cl.addWidget(hms_container)
        layout.addWidget(card)

        # ── Note / Comment ────────────────────────────────────────────────────
        note_card = card_frame(SURFACE)
        nc = QVBoxLayout(note_card)
        nc.setContentsMargins(16, 12, 16, 14)
        nc.setSpacing(8)

        note_hdr = QHBoxLayout()
        note_hdr.setContentsMargins(0, 0, 0, 0)
        note_title = QLabel("Note / Comment")
        note_title.setStyleSheet(f"color: {TEXT}; font-size: 11px; font-weight: bold; background: transparent;")
        note_hdr.addWidget(note_title)
        note_hdr.addStretch()
        if ticket:
            note_hint = QLabel("Also sent as Jira comment when syncing")
            note_hint.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; background: transparent;")
            note_hdr.addWidget(note_hint)
        nc.addLayout(note_hdr)

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Add a note about this session… (optional)")
        self.note_edit.setPlainText(session.get("note", "") or "")
        self.note_edit.setFixedHeight(70)
        nc.addWidget(self.note_edit)
        layout.addWidget(note_card)

        self.resync_cb = QCheckBox(f"Re-sync updated time to Jira  ({ticket})")
        if ticket:
            layout.addWidget(self.resync_cb)

        layout.addWidget(dim_label("Local session record will always be updated.", 9))

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = styled_btn("Cancel", GREY, GREY_H)
        cancel.clicked.connect(self.reject)
        save = styled_btn("Save", GREEN, GREEN_H, "#0a0a0a", min_w=90)
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

    def _save(self):
        secs = parse_hms(self.sb_h.value(), self.sb_m.value(), self.sb_s.value())
        if secs is None:
            QMessageBox.warning(self, "Invalid", "Please enter a valid duration.")
            return
        self._result = {
            "duration": secs,
            "resync":   self.resync_cb.isChecked(),
            "note":     self.note_edit.toPlainText().strip(),
        }
        self.accept()

    def get_result(self): return getattr(self, "_result", None)

# ── Manual Entry Dialog ───────────────────────────────────────────────────────

class ManualEntryDialog(QDialog):
    def __init__(self, parent, project, ticket, jira_configured):
        super().__init__(parent)
        self.setWindowTitle("Add Manual Entry")
        self.setFixedWidth(440)
        self.setModal(True)
        self._project = project
        self._ticket  = ticket
        self._jira_ok = jira_configured and bool(ticket)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Add Manual Time Entry")
        title.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        ticket_suffix = f"   🔗 {ticket}" if ticket else ""
        layout.addWidget(dim_label(f"Project:  {project}{ticket_suffix}"))

        # Date & Start time card
        date_card = card_frame(SURFACE)
        dc = QVBoxLayout(date_card)
        dc.setContentsMargins(16, 16, 16, 16)
        dc.setSpacing(10)
        dc.addWidget(section_label("DATE & START TIME"))

        date_row = QHBoxLayout()
        date_row.setSpacing(16)

        date_col = QVBoxLayout()
        date_col.addWidget(dim_label("DATE", 8))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedWidth(150)
        date_col.addWidget(self.date_edit)
        date_row.addLayout(date_col)

        time_col = QVBoxLayout()
        time_col.addWidget(dim_label("START TIME", 8))
        self.time_edit = QTimeEdit(QTime.currentTime())
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setFixedWidth(110)
        time_col.addWidget(self.time_edit)
        date_row.addLayout(time_col)
        date_row.addStretch()

        dc.addLayout(date_row)
        layout.addWidget(date_card)

        # Duration card
        dur_card = card_frame(SURFACE)
        durc = QVBoxLayout(dur_card)
        durc.setContentsMargins(16, 16, 16, 16)
        durc.setSpacing(10)
        durc.addWidget(section_label("DURATION"))

        hms_row, self.sb_h, self.sb_m, self.sb_s = hms_spinboxes(0, 30, 0)
        hms_container = QWidget()
        hms_container.setStyleSheet("background: transparent;")
        hms_container.setLayout(hms_row)
        durc.addWidget(hms_container)
        layout.addWidget(dur_card)

        # Note field
        note_lbl = section_label("NOTE  (optional)")
        layout.addWidget(note_lbl)
        self.e_note = QLineEdit()
        self.e_note.setPlaceholderText("Add a note about this entry…")
        layout.addWidget(self.e_note)

        # Jira sync checkbox
        self.sync_cb = QCheckBox(f"Sync this entry to Jira  ({ticket})")
        if self._jira_ok:
            layout.addWidget(self.sync_cb)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = styled_btn("Cancel", GREY, GREY_H)
        cancel.clicked.connect(self.reject)
        add = styled_btn("Add Entry", GREEN, GREEN_H, "#0a0a0a", min_w=110)
        add.clicked.connect(self._save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(add)
        layout.addLayout(btn_row)

    def _save(self):
        qdate    = self.date_edit.date()
        qtime    = self.time_edit.time()
        date_str = qdate.toString("yyyy-MM-dd")
        dt_str   = f"{date_str} {qtime.toString('HH:mm')}"
        try:
            start_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except ValueError:
            QMessageBox.warning(self, "Invalid", "Invalid date or time.")
            return

        duration = parse_hms(self.sb_h.value(), self.sb_m.value(), self.sb_s.value())
        if not duration:
            QMessageBox.warning(self, "Invalid Duration",
                                "Please enter a duration greater than zero.")
            return

        start_ts = start_obj.timestamp()
        do_sync  = self.sync_cb.isChecked() if self._jira_ok else False

        session = {
            "project":   self._project,
            "ticket":    self._ticket,
            "start":     start_ts,
            "end":       start_ts + duration,
            "duration":  duration,
            "date":      date_str,
            "jira_sync": "pending" if do_sync else "none",
            "manual":    True,
            "note":      self.e_note.text().strip(),
        }
        self._result = {"session": session, "sync": do_sync}
        self.accept()

    def get_result(self): return getattr(self, "_result", None)

# ── Jira Issue Info Dialog ────────────────────────────────────────────────────

class JiraIssueInfoDialog(QDialog):
    def __init__(self, parent, ticket_key, jira_cfg):
        super().__init__(parent)
        self.setWindowTitle(f"Jira Issue — {ticket_key}")
        self.resize(520, 460)
        self.setModal(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        hdr = QWidget()
        hdr.setStyleSheet(f"background-color: {JIRA_BLUE};")
        hdr.setFixedHeight(52)
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(16, 0, 16, 0)
        key_lbl = QLabel(f"🔗  {ticket_key}")
        key_lbl.setStyleSheet(f"color: white; font-size: 15px; font-weight: bold; background: transparent;")
        hdr_l.addWidget(key_lbl)
        hdr_l.addStretch()
        self.status_lbl = QLabel("Loading…")
        self.status_lbl.setStyleSheet(f"color: #cce0ff; font-size: 11px; background: transparent;")
        hdr_l.addWidget(self.status_lbl)
        layout.addWidget(hdr)

        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 16, 20, 0)
        self.content_layout.setSpacing(12)

        loading = QLabel("Fetching from Jira…")
        loading.setAlignment(Qt.AlignCenter)
        loading.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px; background: transparent;")
        self.content_layout.addWidget(loading)
        self.content_layout.addStretch()
        layout.addWidget(self.content_widget, 1)

        # Footer
        footer = QWidget()
        footer.setStyleSheet(f"background-color: {BG};")
        foot_l = QHBoxLayout(footer)
        foot_l.setContentsMargins(20, 10, 20, 16)
        foot_l.addStretch()
        close_btn = styled_btn("Close", GREY, GREY_H)
        close_btn.clicked.connect(self.accept)
        foot_l.addWidget(close_btn)
        layout.addWidget(footer)

        self._worker = JiraFetchWorker(jira_cfg, ticket_key)
        self._worker.done.connect(self._render)
        self._worker.start()

    def _render(self, issue, err):
        # Clear content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if err:
            self.status_lbl.setText("Error")
            lbl = QLabel(f"⚠  Could not load issue:\n\n{err}")
            lbl.setStyleSheet(f"color: {WARNING}; font-size: 12px; background: transparent;")
            lbl.setWordWrap(True)
            self.content_layout.addWidget(lbl)
            self.content_layout.addStretch()
            return

        self.status_lbl.setText(f"  {issue['status']}  ")

        # Summary
        summary = QLabel(issue["summary"])
        summary.setStyleSheet(f"color: {TEXT}; font-size: 14px; font-weight: bold; background: transparent;")
        summary.setWordWrap(True)
        self.content_layout.addWidget(summary)

        # Meta strip
        meta = card_frame(SURFACE)
        meta_l = QHBoxLayout(meta)
        meta_l.setContentsMargins(14, 10, 14, 10)
        for lbl_text, val in [("Status", issue["status"]),
                               ("Assignee", issue["assignee"]),
                               ("Priority", issue["priority"])]:
            col = QVBoxLayout()
            col.setSpacing(2)
            tl = QLabel(lbl_text)
            tl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 8px; font-weight: bold; background: transparent; border: none;")
            vl = QLabel(val)
            vl.setStyleSheet(f"color: {TEXT}; font-size: 12px; background: transparent; border: none;")
            col.addWidget(tl)
            col.addWidget(vl)
            meta_l.addLayout(col)
            if lbl_text != "Priority":
                meta_l.addStretch()
        self.content_layout.addWidget(meta)

        # Description
        desc_hdr = section_label("DESCRIPTION")
        self.content_layout.addWidget(desc_hdr)

        desc_box = QTextEdit()
        desc_box.setPlainText(issue["description"])
        desc_box.setReadOnly(True)
        desc_box.setStyleSheet(f"background-color: {SURFACE}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 6px; padding: 10px;")
        self.content_layout.addWidget(desc_box)


# ── Export Dialog ─────────────────────────────────────────────────────────────

class ExportDialog(QDialog):
    """Export filtered sessions to CSV or JSON."""

    def __init__(self, parent, data):
        super().__init__(parent)
        self.setWindowTitle("Export Time Data")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setStyleSheet(f"QDialog {{ background-color: {BG}; }}")
        self._data = data

        # date range state
        self._preset    = "last_30"     # currently selected preset key or "custom"
        self._custom_start = None       # date string or None
        self._custom_end   = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(14)

        # ── Title ─────────────────────────────────────────────────────────────
        h1 = QLabel("Export Time Data")
        h1.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {TEXT};")
        lay.addWidget(h1)

        # ── Projects section ──────────────────────────────────────────────────
        lay.addWidget(self._section_label("PROJECTS"))
        proj_card = card_frame(SURFACE)
        pc_lay = QVBoxLayout(proj_card)
        pc_lay.setContentsMargins(12, 10, 12, 10)
        pc_lay.setSpacing(4)

        # Select all / none buttons
        sel_row = QHBoxLayout()
        all_btn  = styled_btn("Select All",  CARD, SURFACE, TEXT_DIM, 9, False)
        none_btn = styled_btn("Select None", CARD, SURFACE, TEXT_DIM, 9, False)
        sel_row.addWidget(all_btn); sel_row.addWidget(none_btn); sel_row.addStretch()
        pc_lay.addLayout(sel_row)

        # Scrollable checkbox list
        proj_scroll = QScrollArea()
        proj_scroll.setWidgetResizable(True)
        proj_scroll.setFixedHeight(130)
        proj_scroll.setStyleSheet(f"QScrollArea {{ background: transparent; border: none; }}")
        proj_inner = QWidget(); proj_inner.setStyleSheet("background: transparent;")
        proj_vb = QVBoxLayout(proj_inner); proj_vb.setSpacing(4); proj_vb.setContentsMargins(4,4,4,4)
        self._proj_checks = []

        active_projects   = data.get("projects", [])
        archived_projects = data.get("archived_projects", [])

        for proj in active_projects:
            cb = QCheckBox(proj)
            cb.setChecked(True)
            cb.stateChanged.connect(self._update_preview)
            proj_vb.addWidget(cb)
            self._proj_checks.append(cb)

        # Archived projects — shown with a dim separator and 📦 prefix label
        if archived_projects:
            # Only show the separator if there are also active projects
            if active_projects:
                sep_lbl = QLabel("── Archived ──────────────")
                sep_lbl.setStyleSheet(
                    f"color: {TEXT_DIM}; font-size: 8px; font-weight: bold; "
                    "background: transparent; margin-top: 4px;"
                )
                proj_vb.addWidget(sep_lbl)

            for proj in archived_projects:
                cb = QCheckBox(f"📦 {proj}")
                cb.setProperty("actual_name", proj)   # store real name for filtering
                cb.setChecked(True)
                cb.setStyleSheet(f"color: {TEXT_DIM};")
                cb.stateChanged.connect(self._update_preview)
                proj_vb.addWidget(cb)
                self._proj_checks.append(cb)

        if not self._proj_checks:
            proj_vb.addWidget(dim_label("No projects yet."))
        proj_vb.addStretch()
        proj_scroll.setWidget(proj_inner)
        pc_lay.addWidget(proj_scroll)
        lay.addWidget(proj_card)

        all_btn.clicked.connect(lambda: [cb.setChecked(True)  for cb in self._proj_checks])
        none_btn.clicked.connect(lambda: [cb.setChecked(False) for cb in self._proj_checks])

        # ── Time frame section ────────────────────────────────────────────────
        lay.addWidget(self._section_label("TIME FRAME"))
        tf_card = card_frame(SURFACE)
        tf_lay = QVBoxLayout(tf_card)
        tf_lay.setContentsMargins(12, 10, 12, 12)
        tf_lay.setSpacing(8)

        # Quick preset buttons (two rows)
        PRESETS_ROW1 = [
            ("Last Day",    "last_1"),
            ("Last 7 Days", "last_7"),
            ("Last 30 Days","last_30"),
            ("Last 6 Months","last_180"),
            ("All Time",    "all_time"),
        ]
        PRESETS_ROW2 = [
            ("Today",       "today"),
            ("This Week",   "this_week"),
            ("This Month",  "this_month"),
            ("This Year",   "this_year"),
            ("Custom",      "custom"),
        ]
        self._preset_btns = {}
        for row_presets in (PRESETS_ROW1, PRESETS_ROW2):
            row = QHBoxLayout(); row.setSpacing(6)
            for label, key in row_presets:
                btn = QPushButton(label)
                btn.setCheckable(True)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setProperty("preset_key", key)
                btn.clicked.connect(self._on_preset_clicked)
                self._preset_btns[key] = btn
                row.addWidget(btn)
            row.addStretch()
            tf_lay.addLayout(row)

        # Custom date range (hidden initially)
        self._custom_widget = QWidget()
        self._custom_widget.setStyleSheet("background: transparent;")
        cw_lay = QHBoxLayout(self._custom_widget)
        cw_lay.setContentsMargins(0, 4, 0, 0); cw_lay.setSpacing(10)
        cw_lay.addWidget(dim_label("From"))
        self._date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self._date_from.setCalendarPopup(True)
        self._date_from.dateChanged.connect(self._update_preview)
        self._date_to   = QDateEdit(QDate.currentDate())
        self._date_to.setCalendarPopup(True)
        self._date_to.dateChanged.connect(self._update_preview)
        cw_lay.addWidget(self._date_from)
        cw_lay.addWidget(dim_label("To"))
        cw_lay.addWidget(self._date_to)
        cw_lay.addStretch()
        self._custom_widget.setVisible(False)
        tf_lay.addWidget(self._custom_widget)
        lay.addWidget(tf_card)

        # style preset buttons now that they exist
        self._style_preset_btns()
        self._preset_btns.get("last_30", list(self._preset_btns.values())[0]).setChecked(True)

        # ── Format ────────────────────────────────────────────────────────────
        lay.addWidget(self._section_label("FORMAT"))
        fmt_row = QHBoxLayout(); fmt_row.setSpacing(10)
        self._fmt_group = QButtonGroup(self)
        for i, (label, val) in enumerate([("CSV  (Excel-friendly)", "csv"), ("JSON", "json")]):
            rb = QCheckBox(label)
            rb.setProperty("fmt_val", val)
            if i == 0: rb.setChecked(True)
            rb.stateChanged.connect(self._on_fmt_changed)
            self._fmt_group.addButton(rb, i)
            fmt_row.addWidget(rb)
        fmt_row.addStretch()
        self._fmt_btns = list(self._fmt_group.buttons())
        lay.addLayout(fmt_row)

        # ── Category totals option ────────────────────────────────────────────
        cat_card = card_frame(SURFACE)
        cc_lay = QVBoxLayout(cat_card)
        cc_lay.setContentsMargins(14, 10, 14, 10)
        cc_lay.setSpacing(6)
        self._cat_totals_cb = QCheckBox("Include category time totals in export")
        self._cat_totals_cb.setToolTip(
            "Appends a summary table showing total hours per category\n"
            "for the selected projects and time range."
        )
        self._cat_totals_cb.stateChanged.connect(self._update_preview)
        cc_lay.addWidget(self._cat_totals_cb)

        # Show which categories exist in the current filter
        self._cat_hint_lbl = QLabel("")
        self._cat_hint_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; background: transparent;")
        self._cat_hint_lbl.setWordWrap(True)
        cc_lay.addWidget(self._cat_hint_lbl)
        lay.addWidget(cat_card)
        self._update_cat_hint()

        # ── Preview count + export button ─────────────────────────────────────
        bot = QHBoxLayout()
        self._preview_lbl = QLabel("")
        self._preview_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        bot.addWidget(self._preview_lbl)
        bot.addStretch()
        cancel_btn = styled_btn("Cancel", GREY, GREY_H)
        export_btn = styled_btn("⬇  Export", GREEN, GREEN_H, "#0a0a0a")
        cancel_btn.clicked.connect(self.reject)
        export_btn.clicked.connect(self._do_export)
        bot.addWidget(cancel_btn); bot.addWidget(export_btn)
        lay.addLayout(bot)

        self._update_preview()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _update_cat_hint(self):
        """Update the small hint label showing categories in the current filter."""
        projs = self._get_selected_projects()
        cat_map = self._data.get("category_map", {})
        cats = set()
        for p in projs:
            cats.update(cat_map.get(p, []))
        if cats:
            self._cat_hint_lbl.setText("Categories in selection: " + ",  ".join(sorted(cats)))
        else:
            self._cat_hint_lbl.setText("No categories assigned to the selected projects.")

    def _get_category_totals(self, sessions):
        """Return {cat_name: total_seconds} for the given sessions."""
        cat_map = self._data.get("category_map", {})
        totals  = {}
        for s in sessions:
            proj = s.get("project", "")
            cats = cat_map.get(proj, [])
            if not cats:
                cats = ["(Uncategorised)"]
            for cat in cats:
                totals[cat] = totals.get(cat, 0) + s["duration"]
        return totals

    def _section_label(self, text):
        l = QLabel(text)
        l.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; font-weight: bold;")
        return l

    def _style_preset_btns(self):
        for key, btn in self._preset_btns.items():
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {CARD}; color: {TEXT_DIM};
                    border: 1px solid {BORDER}; border-radius: 5px;
                    padding: 5px 10px; font-size: 10px; font-weight: bold;
                }}
                QPushButton:checked {{
                    background-color: {ACCENT}; color: #ffffff; border: 1px solid {ACCENT};
                }}
                QPushButton:hover:!checked {{ background-color: {SURFACE}; color: {TEXT}; }}
            """)
            btn.setCursor(Qt.PointingHandCursor)

    def _on_preset_clicked(self):
        btn = self.sender()
        key = btn.property("preset_key")
        # uncheck others
        for k, b in self._preset_btns.items():
            if k != key:
                b.setChecked(False)
        btn.setChecked(True)
        self._preset = key
        self._custom_widget.setVisible(key == "custom")
        self._update_preview()

    def _on_fmt_changed(self):
        # make checkboxes behave as radio buttons
        sender = self.sender()
        if sender.isChecked():
            for b in self._fmt_btns:
                if b is not sender:
                    b.setChecked(False)
        self._update_preview()

    def _get_selected_projects(self):
        selected = set()
        for cb in self._proj_checks:
            if cb.isChecked():
                # archived checkboxes store the real name in actual_name property
                actual = cb.property("actual_name")
                selected.add(actual if actual else cb.text())
        return selected

    def _compute_date_range(self):
        """Returns (start_str, end_str) or (None, None) for all time."""
        now_str   = datetime.now().strftime("%Y-%m-%d")
        if self._preset == "custom":
            return (
                self._date_from.date().toString("yyyy-MM-dd"),
                self._date_to.date().toString("yyyy-MM-dd"),
            )
        PRESET_DAYS = {
            "last_1": 1, "last_7": 7, "last_30": 30,
            "last_180": 180, "all_time": None,
            "today": 0, "yesterday": 1,
        }
        if self._preset in PRESET_DAYS:
            days = PRESET_DAYS[self._preset]
            if days is None:
                return None, None
            if self._preset == "today":
                return now_str, now_str
            if self._preset == "yesterday":
                y = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                return y, y
            start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            return start, now_str
        if self._preset == "this_week":
            start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
            return start, now_str
        if self._preset == "this_month":
            start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            return start, now_str
        if self._preset == "this_year":
            start = datetime.now().replace(month=1, day=1).strftime("%Y-%m-%d")
            return start, now_str
        return None, None

    def _get_filtered_sessions(self):
        projs = self._get_selected_projects()
        start, end = self._compute_date_range()
        out = []
        for s in self._data.get("sessions", []):
            if s.get("project") not in projs:
                continue
            d = s.get("date", "")
            if start and d < start:
                continue
            if end and d > end:
                continue
            out.append(s)
        return out

    def _update_preview(self):
        sessions = self._get_filtered_sessions()
        total = sum(s["duration"] for s in sessions)
        self._preview_lbl.setText(
            f"{len(sessions)} session{'s' if len(sessions) != 1 else ''}  •  {fmt_duration(total)} total"
        )
        self._update_cat_hint()

    def _get_format(self):
        for b in self._fmt_btns:
            if b.isChecked():
                return b.property("fmt_val")
        return "csv"

    def _do_export(self):
        sessions = self._get_filtered_sessions()
        if not sessions:
            QMessageBox.information(self, "Nothing to Export",
                "No sessions match the selected filters.")
            return

        fmt  = self._get_format()
        ext  = "csv" if fmt == "csv" else "json"
        include_cats = self._cat_totals_cb.isChecked()

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Export",
            os.path.expanduser(f"~/timetrack_export.{ext}"),
            f"{'CSV Files (*.csv)' if fmt == 'csv' else 'JSON Files (*.json)'}"
        )
        if not path:
            return

        try:
            sorted_sessions = sorted(sessions, key=lambda x: x["start"])
            cat_map         = self._data.get("category_map", {})

            if fmt == "csv":
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Project", "Categories", "Date", "Start", "End",
                                     "Duration (h:m:s)", "Duration (seconds)",
                                     "Ticket", "Jira Sync", "Manual", "Note"])
                    for s in sorted_sessions:
                        proj      = s.get("project", "")
                        cats_str  = ", ".join(cat_map.get(proj, []))
                        writer.writerow([
                            proj,
                            cats_str,
                            s.get("date", ""),
                            datetime.fromtimestamp(s["start"]).strftime("%H:%M:%S"),
                            datetime.fromtimestamp(s["end"]).strftime("%H:%M:%S"),
                            fmt_duration(s["duration"]),
                            int(s["duration"]),
                            s.get("ticket", ""),
                            s.get("jira_sync", "none"),
                            "Yes" if s.get("manual") else "No",
                            s.get("note", ""),
                        ])

                    if include_cats:
                        cat_totals = self._get_category_totals(sessions)
                        writer.writerow([])   # blank spacer
                        writer.writerow(["── CATEGORY TOTALS ──", "", "", "", "", "", "", "", "", "", ""])
                        writer.writerow(["Category", "Duration (h:m:s)", "Duration (seconds)",
                                         "", "", "", "", "", "", "", ""])
                        for cat, secs in sorted(cat_totals.items()):
                            writer.writerow([cat, fmt_duration(secs), int(secs),
                                             "", "", "", "", "", "", "", ""])

            else:  # JSON
                export_data = {
                    "sessions": [
                        {
                            "project":          s.get("project"),
                            "categories":       cat_map.get(s.get("project", ""), []),
                            "date":             s.get("date"),
                            "start":            datetime.fromtimestamp(s["start"]).isoformat(),
                            "end":              datetime.fromtimestamp(s["end"]).isoformat(),
                            "duration_seconds": int(s["duration"]),
                            "duration_hms":     fmt_duration(s["duration"]),
                            "ticket":           s.get("ticket", ""),
                            "jira_sync":        s.get("jira_sync", "none"),
                            "manual":           bool(s.get("manual")),
                            "note":             s.get("note", ""),
                        }
                        for s in sorted_sessions
                    ]
                }
                if include_cats:
                    cat_totals = self._get_category_totals(sessions)
                    export_data["category_totals"] = {
                        cat: {"duration_seconds": int(secs), "duration_hms": fmt_duration(secs)}
                        for cat, secs in sorted(cat_totals.items())
                    }

                with open(path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2)

            QMessageBox.information(self, "Export Complete",
                f"Exported {len(sessions)} sessions to:\n{path}")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", str(e))

# ── Settings Dialog ───────────────────────────────────────────────────────────

class SettingsDialog(QDialog):
    """App settings: appearance (theme) + Jira credentials."""

    theme_changed = Signal(str)   # emits "dark" or "light"

    def __init__(self, parent, data):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(460)
        self._data = data
        self._pending_theme = data.get("settings", {}).get("theme", "dark")

        self.setStyleSheet(f"QDialog {{ background-color: {BG}; }}")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(18)

        title = QLabel("Settings")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TEXT};")
        lay.addWidget(title)

        # ── Appearance ────────────────────────────────────────────────────────
        lay.addWidget(self._section("APPEARANCE"))
        appear_card = self._card()
        ac_lay = QVBoxLayout(appear_card)
        ac_lay.setContentsMargins(14, 12, 14, 12)
        ac_lay.setSpacing(10)

        theme_row = QHBoxLayout()
        theme_lbl = QLabel("Theme")
        theme_lbl.setStyleSheet(f"color: {TEXT}; font-size: 13px;")
        theme_row.addWidget(theme_lbl)
        theme_row.addStretch()

        self._dark_btn  = self._theme_btn("🌙  Dark",  "dark")
        self._light_btn = self._theme_btn("☀️  Light", "light")
        for b in (self._dark_btn, self._light_btn):
            b.clicked.connect(self._on_theme_btn)
            theme_row.addWidget(b)

        self._refresh_theme_btns()
        ac_lay.addLayout(theme_row)
        lay.addWidget(appear_card)

        # ── Jira ──────────────────────────────────────────────────────────────
        lay.addWidget(self._section("JIRA CLOUD"))
        jira_card = self._card()
        jc_lay = QVBoxLayout(jira_card)
        jc_lay.setContentsMargins(14, 12, 14, 14)
        jc_lay.setSpacing(10)

        jira = data.get("jira", {})
        for label, key, placeholder, pw in [
            ("Site URL",   "url",   "https://yourcompany.atlassian.net", False),
            ("Email",      "email", "you@company.com",                  False),
            ("API Token",  "token", "Your Jira API token",               True),
        ]:
            row = QHBoxLayout(); row.setSpacing(10)
            lbl = QLabel(label)
            lbl.setFixedWidth(80)
            lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px;")
            field = QLineEdit(jira.get(key, ""))
            field.setPlaceholderText(placeholder)
            if pw:
                field.setEchoMode(QLineEdit.Password)
            row.addWidget(lbl); row.addWidget(field)
            setattr(self, f"_jira_{key}", field)
            jc_lay.addLayout(row)

        # Token help link
        help_lbl = QLabel('<a href="https://id.atlassian.com/manage-profile/security/api-tokens" '
                          'style="color:#0052cc;">Generate an API token ↗</a>')
        help_lbl.setOpenExternalLinks(True)
        help_lbl.setStyleSheet("font-size: 11px; background: transparent;")
        jc_lay.addWidget(help_lbl)

        # Test connection row
        test_row = QHBoxLayout()
        self._test_btn = styled_btn("⚡ Test Connection", CARD, SURFACE, TEXT_DIM,
                                    font_size=10, bold=False)
        self._test_btn.setToolTip("Verify credentials can connect to your Jira instance")
        self._test_btn.clicked.connect(self._test_connection)
        self._test_lbl = QLabel("")
        self._test_lbl.setStyleSheet(f"font-size: 11px; background: transparent;")
        self._test_worker = None
        test_row.addWidget(self._test_btn)
        test_row.addSpacing(10)
        test_row.addWidget(self._test_lbl, 1)
        jc_lay.addLayout(test_row)

        lay.addWidget(jira_card)

        # ── Buttons ───────────────────────────────────────────────────────────
        bot = QHBoxLayout()
        bot.addStretch()
        cancel = styled_btn("Cancel", GREY, GREY_H)
        save   = styled_btn("Save",   JIRA_BLUE, "#0065ff")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self._save)
        bot.addWidget(cancel); bot.addWidget(save)
        lay.addLayout(bot)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _section(self, text):
        l = QLabel(text)
        l.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; font-weight: bold;")
        return l

    def _card(self):
        f = QFrame()
        f.setStyleSheet(f"QFrame {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}")
        return f

    def _theme_btn(self, label, key):
        b = QPushButton(label)
        b.setProperty("theme_key", key)
        b.setCheckable(True)
        b.setCursor(Qt.PointingHandCursor)
        b.setFixedWidth(110)
        return b

    def _refresh_theme_btns(self):
        for btn, key in ((self._dark_btn, "dark"), (self._light_btn, "light")):
            active = (self._pending_theme == key)
            btn.setChecked(active)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {"" + ACCENT if active else CARD};
                    color: {"#ffffff" if active else TEXT_DIM};
                    border: 1px solid {"" + ACCENT if active else BORDER};
                    border-radius: 6px; padding: 6px 12px;
                    font-size: 12px; font-weight: bold;
                }}
                QPushButton:hover:!checked {{ background-color: {SURFACE}; color: {TEXT}; }}
            """)

    def _on_theme_btn(self):
        key = self.sender().property("theme_key")
        self._pending_theme = key
        self._refresh_theme_btns()
        # Live preview — emit immediately
        self.theme_changed.emit(key)

    def _current_jira_cfg(self):
        return {
            "url":   self._jira_url.text().strip(),
            "email": self._jira_email.text().strip(),
            "token": self._jira_token.text().strip(),
        }

    def _test_connection(self):
        cfg = self._current_jira_cfg()
        if not cfg["url"] or not cfg["email"] or not cfg["token"]:
            self._show_test_result(False, "Fill in all three Jira fields first.")
            return
        self._test_btn.setEnabled(False)
        self._test_btn.setText("⟳ Testing…")
        self._test_lbl.setText("")
        self._test_worker = JiraTestWorker(cfg)
        self._test_worker.done.connect(self._on_test_done)
        self._test_worker.start()

    def _on_test_done(self, ok, message):
        self._test_btn.setEnabled(True)
        self._test_btn.setText("⚡ Test Connection")
        self._show_test_result(ok, message)

    def _show_test_result(self, ok, message):
        color  = SUCCESS if ok else "#e94560"
        prefix = "✔  " if ok else "✖  "
        self._test_lbl.setText(prefix + message)
        self._test_lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; background: transparent;"
        )

    def _save(self):
        self._data.setdefault("settings", {})["theme"] = self._pending_theme
        self._data["jira"] = {
            "url":   self._jira_url.text().strip(),
            "email": self._jira_email.text().strip(),
            "token": self._jira_token.text().strip(),
        }
        self.accept()


# ── Calendar View ─────────────────────────────────────────────────────────────

class CalendarView(QWidget):
    """
    Calendar view with Day / Week / Month modes.
    Each cell shows which projects were worked on and the per-project time total.
    """

    _PROJ_COLORS = [
        "#e94560", "#6a4fc8", "#0a8f6f", "#b06000",
        "#0052cc", "#7d3c98", "#1e8449", "#1a6b8a",
        "#c0392b", "#2471a3", "#884ea0", "#17a589",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sessions   = []
        self._cur_date   = datetime.now().date()   # anchor date for all modes
        self._view_mode  = "month"                 # "day" | "week" | "month"
        self._proj_color = {}
        self._color_idx  = 0
        self._setup_ui()

    # ── public API ────────────────────────────────────────────────────────────

    def refresh(self, sessions, category_map=None):
        self._sessions = sessions
        self._render()

    # ── UI construction ───────────────────────────────────────────────────────

    def _setup_ui(self):
        import calendar as _cal
        self._cal_module = _cal

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # ── Top bar: nav left | title | nav right | spacer | mode buttons ─────
        top_bar = QHBoxLayout()
        top_bar.setSpacing(6)

        self._prev_btn = QPushButton("‹")
        self._next_btn = QPushButton("›")
        for btn in (self._prev_btn, self._next_btn):
            btn.setFixedSize(30, 30)
            btn.setCursor(Qt.PointingHandCursor)
        self._prev_btn.clicked.connect(self._go_prev)
        self._next_btn.clicked.connect(self._go_next)

        self._title_lbl = QLabel()
        self._title_lbl.setAlignment(Qt.AlignCenter)

        today_btn = QPushButton("Today")
        today_btn.setCursor(Qt.PointingHandCursor)
        today_btn.clicked.connect(self._go_today)

        # Mode toggle buttons
        self._mode_btns = {}
        mode_bar = QHBoxLayout()
        mode_bar.setSpacing(0)
        for i, (label, key) in enumerate(
            [("Day", "day"), ("Week", "week"), ("Month", "month")]
        ):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(key == self._view_mode)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(28)
            btn.setMinimumWidth(54)
            btn.setProperty("mode_key", key)
            btn.clicked.connect(self._on_mode_btn)
            self._mode_btns[key] = btn
            mode_bar.addWidget(btn)

        top_bar.addWidget(self._prev_btn)
        top_bar.addWidget(self._title_lbl, 1)
        top_bar.addWidget(self._next_btn)
        top_bar.addSpacing(10)
        top_bar.addWidget(today_btn)
        top_bar.addSpacing(16)
        top_bar.addLayout(mode_bar)
        root.addLayout(top_bar)

        # ── DOW header (hidden in day mode) ───────────────────────────────────
        self._dow_widget = QWidget()
        self._dow_widget.setStyleSheet("background: transparent;")
        dow_row = QHBoxLayout(self._dow_widget)
        dow_row.setContentsMargins(0, 0, 0, 0)
        dow_row.setSpacing(4)
        for day_name in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
            lbl = QLabel(day_name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedHeight(22)
            is_we = day_name in ("Sat", "Sun")
            lbl.setStyleSheet(
                f"color: {'#e94560' if is_we else TEXT_DIM}; "
                "font-size: 10px; font-weight: bold; background: transparent;"
            )
            dow_row.addWidget(lbl)
        root.addWidget(self._dow_widget)

        # ── Scroll area + content widget ──────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._scroll.setWidget(self._content)
        root.addWidget(self._scroll, 1)

        self._style_nav_buttons()
        self._style_mode_buttons()
        self._render()

    # ── Styling helpers ───────────────────────────────────────────────────────

    def _style_nav_buttons(self):
        for btn in (self._prev_btn, self._next_btn):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {CARD}; color: {TEXT};
                    border: 1px solid {BORDER}; border-radius: 6px;
                    font-size: 18px; font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {ACCENT}; color: white; border-color: {ACCENT}; }}
            """)

    def _style_mode_buttons(self):
        for key, btn in self._mode_btns.items():
            active = (key == self._view_mode)
            if active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {ACCENT}; color: white;
                        border: 1px solid {ACCENT};
                        border-radius: 0px; font-size: 11px; font-weight: bold;
                        padding: 2px 8px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {CARD}; color: {TEXT_DIM};
                        border: 1px solid {BORDER};
                        border-radius: 0px; font-size: 11px;
                        padding: 2px 8px;
                    }}
                    QPushButton:hover {{ background-color: {SURFACE}; color: {TEXT}; }}
                """)
        # Round outer corners of first/last
        keys = list(self._mode_btns.keys())
        first_btn = self._mode_btns[keys[0]]
        last_btn  = self._mode_btns[keys[-1]]
        for btn in (first_btn, last_btn):
            ss = btn.styleSheet()
            radius = "border-top-left-radius: 6px; border-bottom-left-radius: 6px;"                      if btn is first_btn else                      "border-top-right-radius: 6px; border-bottom-right-radius: 6px;"
            btn.setStyleSheet(ss.replace("border-radius: 0px;", radius))

    # ── Navigation ────────────────────────────────────────────────────────────

    def _on_mode_btn(self):
        key = self.sender().property("mode_key")
        self._view_mode = key
        for k, b in self._mode_btns.items():
            b.setChecked(k == key)
        self._style_mode_buttons()
        self._render()

    def _go_prev(self):
        if self._view_mode == "day":
            self._cur_date -= timedelta(days=1)
        elif self._view_mode == "week":
            self._cur_date -= timedelta(weeks=1)
        else:
            # previous month
            if self._cur_date.month == 1:
                self._cur_date = self._cur_date.replace(year=self._cur_date.year - 1, month=12, day=1)
            else:
                self._cur_date = self._cur_date.replace(month=self._cur_date.month - 1, day=1)
        self._render()

    def _go_next(self):
        if self._view_mode == "day":
            self._cur_date += timedelta(days=1)
        elif self._view_mode == "week":
            self._cur_date += timedelta(weeks=1)
        else:
            # next month
            if self._cur_date.month == 12:
                self._cur_date = self._cur_date.replace(year=self._cur_date.year + 1, month=1, day=1)
            else:
                self._cur_date = self._cur_date.replace(month=self._cur_date.month + 1, day=1)
        self._render()

    def _go_today(self):
        self._cur_date = datetime.now().date()
        self._render()

    # ── Data helpers ──────────────────────────────────────────────────────────

    def _proj_bg(self, proj):
        if proj not in self._proj_color:
            self._proj_color[proj] = self._PROJ_COLORS[
                self._color_idx % len(self._PROJ_COLORS)
            ]
            self._color_idx += 1
        return self._proj_color[proj]

    def _sessions_for_date(self, date_str):
        """Return list of sessions for a specific YYYY-MM-DD string."""
        return [s for s in self._sessions if s.get("date", "") == date_str]

    def _proj_totals_for_date(self, date_str):
        """Return {project: total_seconds} for a date string."""
        totals = {}
        for s in self._sessions_for_date(date_str):
            proj = s.get("project", "")
            totals[proj] = totals.get(proj, 0) + s.get("duration", 0)
        return totals

    @staticmethod
    def _fmt_dur(secs):
        h = int(secs // 3600)
        m = int((secs % 3600) // 60)
        return f"{h}h {m:02d}m" if h else f"{m}m"

    # ── Main render dispatcher ────────────────────────────────────────────────

    def _render(self):
        # Clear content
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # clear nested layouts
                pass

        if self._view_mode == "day":
            self._dow_widget.setVisible(False)
            self._render_day()
        elif self._view_mode == "week":
            self._dow_widget.setVisible(True)
            self._render_week()
        else:
            self._dow_widget.setVisible(True)
            self._render_month()

    # ── Month view ────────────────────────────────────────────────────────────

    def _render_month(self):
        import calendar as _cal
        d     = self._cur_date
        year  = d.year
        month = d.month
        self._title_lbl.setStyleSheet(
            f"color: {TEXT}; font-size: 15px; font-weight: bold; background: transparent;"
        )
        self._title_lbl.setText(datetime(year, month, 1).strftime("%B %Y"))

        today_str = datetime.now().strftime("%Y-%m-%d")
        first_weekday, days_in_month = _cal.monthrange(year, month)

        grid = QWidget()
        grid.setStyleSheet("background: transparent;")
        gl = QGridLayout(grid)
        gl.setSpacing(4)
        gl.setContentsMargins(0, 0, 0, 0)
        for col in range(7):
            gl.setColumnStretch(col, 1)

        row = 0
        col = first_weekday

        for day_num in range(1, days_in_month + 1):
            date_str  = f"{year:04d}-{month:02d}-{day_num:02d}"
            is_today  = (date_str == today_str)
            proj_data = self._proj_totals_for_date(date_str)
            cell      = self._make_month_cell(day_num, date_str, is_today, proj_data)
            gl.addWidget(cell, row, col)
            col += 1
            if col == 7:
                col = 0
                row += 1

        while col > 0 and col < 7:
            gl.addWidget(self._make_empty_cell(), row, col)
            col += 1

        for r in range(row + 1):
            gl.setRowStretch(r, 1)

        self._content_layout.addWidget(grid, 1)

    def _make_month_cell(self, day_num, date_str, is_today, proj_data):
        has_data   = bool(proj_data)
        is_weekend = datetime.strptime(date_str, "%Y-%m-%d").weekday() >= 5
        border_c   = ACCENT if is_today else BORDER
        bg_c       = CARD if is_today else (SURFACE if has_data else BG)

        cell = QFrame()
        cell.setMinimumHeight(70)
        cell.setStyleSheet(f"QFrame {{ background: {bg_c}; border: 1px solid {border_c}; border-radius: 6px; }}")

        vl = QVBoxLayout(cell)
        vl.setContentsMargins(5, 4, 5, 4)
        vl.setSpacing(2)

        num_color = ACCENT if is_today else ("#e94560" if is_weekend else TEXT_DIM)
        day_lbl = QLabel(str(day_num))
        day_lbl.setStyleSheet(
            f"color: {num_color}; font-size: 11px; font-weight: {'bold' if is_today else 'normal'}; "
            "background: transparent; border: none;"
        )
        vl.addWidget(day_lbl)

        for proj, secs in sorted(proj_data.items(), key=lambda x: x[1], reverse=True):
            row_lay = QHBoxLayout()
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.setSpacing(3)

            dot = QLabel("●")
            dot.setFixedWidth(10)
            dot.setStyleSheet(f"color: {self._proj_bg(proj)}; font-size: 8px; background: transparent; border: none;")

            name = proj if len(proj) <= 14 else proj[:12] + "…"
            nl = QLabel(name)
            nl.setToolTip(proj)
            nl.setStyleSheet(f"color: {TEXT}; font-size: 9px; background: transparent; border: none;")

            dl = QLabel(self._fmt_dur(secs))
            dl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; background: transparent; border: none;")

            row_lay.addWidget(dot)
            row_lay.addWidget(nl, 1)
            row_lay.addWidget(dl)
            vl.addLayout(row_lay)

        if proj_data:
            total = sum(proj_data.values())
            tl = QLabel(f"Total: {self._fmt_dur(total)}")
            tl.setStyleSheet(f"color: {SUCCESS}; font-size: 8px; font-weight: bold; background: transparent; border: none;")
            tl.setAlignment(Qt.AlignRight)
            vl.addWidget(tl)

        vl.addStretch()
        return cell

    # ── Week view ─────────────────────────────────────────────────────────────

    def _render_week(self):
        # Monday of the week containing _cur_date
        monday    = self._cur_date - timedelta(days=self._cur_date.weekday())
        sunday    = monday + timedelta(days=6)
        mon_str   = monday.strftime("%b %-d") if hasattr(monday, 'strftime') else monday.strftime("%b %d").lstrip("0")
        sun_str   = sunday.strftime("%b %-d") if hasattr(sunday, 'strftime') else sunday.strftime("%b %d").lstrip("0")
        year_str  = monday.strftime("%Y")

        # Cross-platform date formatting without leading zeros
        try:
            mon_str = monday.strftime("%b %-d")
            sun_str = sunday.strftime("%b %-d")
        except ValueError:
            mon_str = monday.strftime("%b %#d")   # Windows
            sun_str = sunday.strftime("%b %#d")

        self._title_lbl.setStyleSheet(
            f"color: {TEXT}; font-size: 14px; font-weight: bold; background: transparent;"
        )
        self._title_lbl.setText(f"{mon_str} – {sun_str}, {year_str}")

        today_str = datetime.now().strftime("%Y-%m-%d")

        grid = QWidget()
        grid.setStyleSheet("background: transparent;")
        gl = QGridLayout(grid)
        gl.setSpacing(4)
        gl.setContentsMargins(0, 0, 0, 0)
        for col in range(7):
            gl.setColumnStretch(col, 1)

        for offset in range(7):
            day      = monday + timedelta(days=offset)
            date_str = day.strftime("%Y-%m-%d")
            is_today = (date_str == today_str)
            proj_data = self._proj_totals_for_date(date_str)
            cell     = self._make_week_cell(day, date_str, is_today, proj_data)
            gl.addWidget(cell, 0, offset)

        gl.setRowStretch(0, 1)
        self._content_layout.addWidget(grid, 1)

    def _make_week_cell(self, day, date_str, is_today, proj_data):
        has_data   = bool(proj_data)
        is_weekend = day.weekday() >= 5
        border_c   = ACCENT if is_today else BORDER
        bg_c       = CARD if is_today else (SURFACE if has_data else BG)

        cell = QFrame()
        cell.setMinimumHeight(160)
        cell.setStyleSheet(f"QFrame {{ background: {bg_c}; border: 1px solid {border_c}; border-radius: 6px; }}")

        vl = QVBoxLayout(cell)
        vl.setContentsMargins(6, 6, 6, 6)
        vl.setSpacing(4)

        # Date header inside cell
        try:
            day_str = day.strftime("%-d")
        except ValueError:
            day_str = day.strftime("%#d")
        num_color = ACCENT if is_today else ("#e94560" if is_weekend else TEXT_DIM)
        hdr = QLabel(day_str)
        hdr.setStyleSheet(
            f"color: {num_color}; font-size: 18px; font-weight: bold; "
            "background: transparent; border: none;"
        )
        vl.addWidget(hdr)

        if not has_data:
            empty_lbl = QLabel("—")
            empty_lbl.setStyleSheet(f"color: {BORDER}; font-size: 12px; background: transparent; border: none;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            vl.addWidget(empty_lbl, 1, Qt.AlignCenter)
        else:
            for proj, secs in sorted(proj_data.items(), key=lambda x: x[1], reverse=True):
                pill = QFrame()
                pill.setStyleSheet(f"""
                    QFrame {{
                        background: {self._proj_bg(proj)}22;
                        border: 1px solid {self._proj_bg(proj)}88;
                        border-radius: 4px;
                    }}
                """)
                pl = QVBoxLayout(pill)
                pl.setContentsMargins(6, 4, 6, 4)
                pl.setSpacing(1)

                name = proj if len(proj) <= 16 else proj[:14] + "…"
                nl = QLabel(name)
                nl.setToolTip(proj)
                nl.setStyleSheet(
                    f"color: {self._proj_bg(proj)}; font-size: 10px; font-weight: bold; "
                    "background: transparent; border: none;"
                )

                dl = QLabel(self._fmt_dur(secs))
                dl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; background: transparent; border: none;")

                pl.addWidget(nl)
                pl.addWidget(dl)
                vl.addWidget(pill)

            total = sum(proj_data.values())
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet(f"color: {BORDER}; background: {BORDER}; border: none; max-height: 1px;")
            vl.addWidget(sep)
            tl = QLabel(f"Total  {self._fmt_dur(total)}")
            tl.setStyleSheet(
                f"color: {SUCCESS}; font-size: 10px; font-weight: bold; "
                "background: transparent; border: none;"
            )
            vl.addWidget(tl)

        vl.addStretch()
        return cell

    # ── Day view ──────────────────────────────────────────────────────────────

    def _render_day(self):
        d        = self._cur_date
        date_str = d.strftime("%Y-%m-%d")
        today    = datetime.now().date()

        try:
            day_fmt = d.strftime("%A, %B %-d %Y")
        except ValueError:
            day_fmt = d.strftime("%A, %B %#d %Y")

        suffix = " — Today" if d == today else (" — Yesterday" if (today - d).days == 1 else "")
        self._title_lbl.setStyleSheet(
            f"color: {TEXT}; font-size: 14px; font-weight: bold; background: transparent;"
        )
        self._title_lbl.setText(day_fmt + suffix)

        sessions = sorted(self._sessions_for_date(date_str), key=lambda s: s.get("start", 0))

        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(8)

        if not sessions:
            # Empty state
            empty = QFrame()
            empty.setStyleSheet(f"QFrame {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}")
            el = QVBoxLayout(empty)
            el.setContentsMargins(24, 32, 24, 32)
            lbl = QLabel("No sessions recorded for this day.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px; background: transparent; border: none;")
            el.addWidget(lbl)
            wl.addWidget(empty)
            wl.addStretch()
            self._content_layout.addWidget(wrapper, 1)
            return

        # Summary bar at top
        proj_totals = self._proj_totals_for_date(date_str)
        day_total   = sum(proj_totals.values())

        summary = QFrame()
        summary.setStyleSheet(f"QFrame {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}")
        sl = QHBoxLayout(summary)
        sl.setContentsMargins(16, 10, 16, 10)
        sl.setSpacing(20)

        total_lbl = QLabel(f"Total: {self._fmt_dur(day_total)}")
        total_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        sl.addWidget(total_lbl)

        for proj, secs in sorted(proj_totals.items(), key=lambda x: x[1], reverse=True):
            dot = QLabel(f"● {proj}  {self._fmt_dur(secs)}")
            dot.setStyleSheet(
                f"color: {self._proj_bg(proj)}; font-size: 11px; font-weight: bold; "
                "background: transparent; border: none;"
            )
            dot.setToolTip(proj)
            sl.addWidget(dot)
        sl.addStretch()
        wl.addWidget(summary)

        # Individual session cards
        for s in sessions:
            proj     = s.get("project", "")
            dur      = s.get("duration", 0)
            note     = s.get("note", "")
            ticket   = s.get("ticket", "")
            manual   = s.get("manual", False)
            sync_st  = s.get("jira_sync", "none")
            start_ts = s.get("start", 0)
            end_ts   = s.get("end", 0)

            start_t = datetime.fromtimestamp(start_ts).strftime("%H:%M") if start_ts else ""
            end_t   = datetime.fromtimestamp(end_ts).strftime("%H:%M")   if end_ts   else ""
            bg_col  = self._proj_bg(proj)

            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {bg_col}18;
                    border: 1px solid {bg_col}55;
                    border-left: 4px solid {bg_col};
                    border-radius: 6px;
                }}
            """)
            cl = QHBoxLayout(card)
            cl.setContentsMargins(12, 10, 12, 10)
            cl.setSpacing(16)

            # Left: time range column
            time_col = QVBoxLayout()
            time_col.setSpacing(2)
            time_lbl = QLabel(f"{start_t}")
            time_lbl.setStyleSheet(f"color: {TEXT}; font-size: 12px; font-weight: bold; background: transparent; border: none;")
            end_lbl  = QLabel(f"{end_t}")
            end_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent; border: none;")
            time_col.addWidget(time_lbl)
            time_col.addWidget(end_lbl)
            cl.addLayout(time_col)

            # Divider
            div = QFrame()
            div.setFrameShape(QFrame.VLine)
            div.setStyleSheet(f"color: {bg_col}55; background: {bg_col}55; border: none; max-width: 1px;")
            cl.addWidget(div)

            # Middle: project + note
            info_col = QVBoxLayout()
            info_col.setSpacing(2)
            proj_lbl = QLabel(proj)
            proj_lbl.setStyleSheet(
                f"color: {bg_col}; font-size: 13px; font-weight: bold; background: transparent; border: none;"
            )
            info_col.addWidget(proj_lbl)
            badges = QHBoxLayout()
            badges.setSpacing(6)
            if ticket:
                t_lbl = QLabel(f"🔗 {ticket}")
                t_lbl.setStyleSheet(f"color: {JIRA_BLUE}; font-size: 10px; background: transparent; border: none;")
                badges.addWidget(t_lbl)
            if manual:
                m_lbl = QLabel("✏ manual")
                m_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; background: transparent; border: none;")
                badges.addWidget(m_lbl)
            if sync_st == "synced":
                j_lbl = QLabel("✔ Jira")
                j_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 10px; background: transparent; border: none;")
                badges.addWidget(j_lbl)
            badges.addStretch()
            info_col.addLayout(badges)
            if note:
                note_lbl = QLabel(note)
                note_lbl.setWordWrap(True)
                note_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent; border: none;")
                info_col.addWidget(note_lbl)
            cl.addLayout(info_col, 1)

            # Right: duration
            dur_lbl = QLabel(self._fmt_dur(dur))
            dur_lbl.setStyleSheet(
                f"color: {TEXT}; font-size: 15px; font-weight: bold; background: transparent; border: none;"
            )
            dur_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            cl.addWidget(dur_lbl)

            wl.addWidget(card)

        wl.addStretch()
        self._content_layout.addWidget(wrapper, 1)

    # ── Shared helpers ────────────────────────────────────────────────────────

    def _make_empty_cell(self):
        f = QFrame()
        f.setStyleSheet("background: transparent; border: none;")
        return f


# ── Main Window ───────────────────────────────────────────────────────────────

class TimeTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TimeTrack")
        self.resize(1040, 740)
        self.setMinimumSize(860, 600)

        self.data           = load_data()
        self.data.setdefault("jira", {"url": "", "email": "", "token": ""})
        self.data.setdefault("ticket_map", {})
        self.data.setdefault("categories", [])
        self.data.setdefault("category_map", {})
        self.data.setdefault("archived_projects", [])
        self._archive_worker = None   # JiraAutoArchiveWorker ref
        self.data.setdefault("stat_configs", list(DEFAULT_STAT_CONFIGS))
        self.data.setdefault("settings", {"theme": "dark"})
        while len(self.data["stat_configs"]) < 3:
            self.data["stat_configs"].append(DEFAULT_STAT_CONFIGS[-1])

        # Apply saved theme before building UI
        _theme = self.data["settings"].get("theme", "dark")
        set_theme(_theme)

        self._active_project  = ""
        self._timer_running   = False
        self._start_time      = None
        self._elapsed         = 0
        self._expanded_projs  = set()
        self._workers         = []   # keep QThread refs alive

        self._build_ui()
        self.refresh_projects()
        self.refresh_log()
        self._setup_tray()

        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._tick)
        self._tick_timer.start(500)

        # Run Jira auto-archive check 3 seconds after startup (non-blocking)
        QTimer.singleShot(3000, self._run_jira_auto_archive)

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(20, 16, 20, 16)
        body_layout.setSpacing(0)

        # Splitter — lets user drag the divider between left and right panels
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {BORDER};
                border-radius: 3px;
                margin: 4px 0px;
            }}
            QSplitter::handle:hover {{
                background-color: {ACCENT};
            }}
        """)

        left = QWidget()
        left.setMinimumWidth(220)
        left.setMaximumWidth(560)
        left.setStyleSheet("background: transparent;")
        self._build_left(left)

        right = QWidget()
        right.setStyleSheet("background: transparent;")
        self._build_right(right)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([320, 680])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        self._splitter = splitter   # keep ref for theme rebuild

        body_layout.addWidget(splitter)
        root.addWidget(body, 1)

    def _build_header(self):
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background-color: {SURFACE};")
        self._header_widget = header   # keep ref for theme repaints

        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 0, 16, 0)
        hl.setSpacing(12)

        logo = QLabel("⏱  TimeTrack")
        logo.setStyleSheet(f"color: {ACCENT}; font-size: 22px; font-weight: bold; background: transparent;")
        hl.addWidget(logo)

        tagline = QLabel("Stay focused, stay productive.")
        tagline.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
        hl.addWidget(tagline)

        hl.addStretch()

        self.jira_status_lbl = QLabel("")
        self.jira_status_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; background: transparent;")
        hl.addWidget(self.jira_status_lbl)

        export_btn = styled_btn("⬇  Export", GREEN, GREEN_H, "#0a0a0a", font_size=10)
        export_btn.clicked.connect(self.open_export)
        hl.addWidget(export_btn)

        settings_btn = styled_btn("⚙  Settings", CARD, SURFACE, TEXT_DIM, font_size=10)
        settings_btn.clicked.connect(self.open_settings)
        hl.addWidget(settings_btn)

        self._update_jira_status_label()
        return header

    def _build_left(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # ── Timer card ────────────────────────────────────────────────────────
        timer_card = card_frame(CARD)
        tc = QVBoxLayout(timer_card)
        tc.setContentsMargins(16, 14, 16, 16)
        tc.setSpacing(4)

        tc.addWidget(section_label("CURRENT SESSION"))

        self.timer_lbl = QLabel("00:00:00")
        font = QFont()
        font.setPointSize(40)
        font.setWeight(QFont.Bold)
        font.setFamilies(["SF Mono", "Courier New", "Monospace"])
        self.timer_lbl.setFont(font)
        self.timer_lbl.setAlignment(Qt.AlignCenter)
        self.timer_lbl.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        tc.addWidget(self.timer_lbl)

        self.project_lbl = QLabel("No project selected")
        self.project_lbl.setAlignment(Qt.AlignCenter)
        self.project_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent; border: none;")
        tc.addWidget(self.project_lbl)

        self.ticket_lbl = QLabel("")
        self.ticket_lbl.setAlignment(Qt.AlignCenter)
        self.ticket_lbl.setStyleSheet(f"color: {JIRA_BLUE}; font-size: 10px; background: transparent; border: none;")
        tc.addWidget(self.ticket_lbl)

        tc.addSpacing(8)
        self.start_btn = styled_btn("▶   Start", GREEN, GREEN_H, "#0a0a0a", font_size=13)
        self.start_btn.setMinimumHeight(44)
        self.start_btn.clicked.connect(self.toggle_timer)
        tc.addWidget(self.start_btn)

        layout.addWidget(timer_card)

        # ── Projects header with tab bar ──────────────────────────────────────
        ph = QHBoxLayout()
        ph.setContentsMargins(0, 0, 0, 0)
        ph.setSpacing(0)

        # Active / Archived toggle tabs
        self._proj_tab_active   = QPushButton("Active")
        self._proj_tab_archived = QPushButton("Archived")
        for btn in (self._proj_tab_active, self._proj_tab_archived):
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(26)
            btn.setMinimumWidth(60)
        self._proj_tab_active.setChecked(True)
        self._proj_tab_active.clicked.connect(lambda: self._switch_proj_tab("active"))
        self._proj_tab_archived.clicked.connect(lambda: self._switch_proj_tab("archived"))
        self._proj_tab = "active"
        self._style_proj_tabs()

        ph.addWidget(self._proj_tab_active)
        ph.addWidget(self._proj_tab_archived)
        ph.addStretch()

        # Right side: add button (hidden in archived tab) + Jira check button
        self._add_proj_btn = styled_btn("+ Add", BLUE, BLUE_H, font_size=10)
        self._add_proj_btn.clicked.connect(self.add_project)

        self._jira_check_btn = styled_btn("⟳ Jira", CARD, SURFACE, TEXT_DIM, font_size=9)
        self._jira_check_btn.setToolTip(
            "Check Jira ticket statuses and auto-archive any projects\n"
            "whose ticket is Done, Closed, or Resolved."
        )
        self._jira_check_btn.clicked.connect(self._run_jira_auto_archive)

        ph.addWidget(self._add_proj_btn)
        ph.addSpacing(4)
        ph.addWidget(self._jira_check_btn)
        layout.addLayout(ph)

        # ── Stacked scroll areas (active / archived) ──────────────────────────
        self._proj_stack = QStackedWidget()
        self._proj_stack.setStyleSheet("background: transparent;")

        # Page 0: active projects
        def _make_scroll_page():
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setStyleSheet(f"""
                QScrollArea {{ background-color: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}
                QScrollArea > QWidget > QWidget {{ background-color: {SURFACE}; }}
            """)
            container = QWidget()
            container.setStyleSheet(f"background-color: {SURFACE};")
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(6, 6, 6, 6)
            vbox.setSpacing(4)
            vbox.addStretch()
            scroll.setWidget(container)
            return scroll, vbox

        active_scroll, self.proj_layout = _make_scroll_page()
        archived_scroll, self.archived_proj_layout = _make_scroll_page()

        self._proj_stack.addWidget(active_scroll)
        self._proj_stack.addWidget(archived_scroll)
        layout.addWidget(self._proj_stack, 1)

    def _style_proj_tabs(self):
        for btn, key in (
            (self._proj_tab_active,   "active"),
            (self._proj_tab_archived, "archived"),
        ):
            active = (key == self._proj_tab)
            if active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {SURFACE}; color: {TEXT};
                        border: 1px solid {BORDER}; border-bottom: 2px solid {ACCENT};
                        border-radius: 0px; font-size: 10px; font-weight: bold; padding: 0 10px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent; color: {TEXT_DIM};
                        border: none; border-bottom: 2px solid transparent;
                        border-radius: 0px; font-size: 10px; padding: 0 10px;
                    }}
                    QPushButton:hover {{ color: {TEXT}; border-bottom: 2px solid {BORDER}; }}
                """)

    def _switch_proj_tab(self, tab):
        self._proj_tab = tab
        self._proj_tab_active.setChecked(tab == "active")
        self._proj_tab_archived.setChecked(tab == "archived")
        self._proj_stack.setCurrentIndex(0 if tab == "active" else 1)
        self._add_proj_btn.setVisible(tab == "active")
        self._style_proj_tabs()

    def _build_right(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # ── Stat cards (customizable) ─────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.stat_title_labels = []
        self.stat_value_labels = []
        self.stat_cards        = []
        for slot_idx, color in enumerate(get_stat_colors()):
            card = card_frame(SURFACE)
            card.setProperty("slot_idx", slot_idx)
            card.setCursor(Qt.PointingHandCursor)
            card.installEventFilter(self)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(14, 8, 14, 10)
            cl.setSpacing(1)
            tr = QHBoxLayout(); tr.setContentsMargins(0,0,0,0); tr.setSpacing(4)
            tl = QLabel()
            tl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; font-weight: bold; background: transparent; border: none;")
            hint_lbl = QLabel("▾")
            hint_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; background: transparent; border: none;")
            tr.addWidget(tl); tr.addWidget(hint_lbl); tr.addStretch()
            vl = QLabel("00:00:00")
            vl.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold; background: transparent; border: none;")
            cl.addLayout(tr)
            cl.addWidget(vl)
            self.stat_title_labels.append(tl)
            self.stat_value_labels.append(vl)
            self.stat_cards.append(card)
            stats_row.addWidget(card)
        layout.addLayout(stats_row)

        # ── View toggle header ────────────────────────────────────────────────
        view_hdr = QHBoxLayout()
        view_hdr.setContentsMargins(0, 0, 0, 0)
        view_hdr.setSpacing(0)

        self._log_tab_btn = QPushButton("  Session Log  ")
        self._cal_tab_btn = QPushButton("  Calendar  ")
        for btn in (self._log_tab_btn, self._cal_tab_btn):
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(30)
        self._log_tab_btn.setChecked(True)
        self._log_tab_btn.clicked.connect(lambda: self._switch_view(0))
        self._cal_tab_btn.clicked.connect(lambda: self._switch_view(1))
        self._style_view_tabs()

        view_hdr.addWidget(self._log_tab_btn)
        view_hdr.addWidget(self._cal_tab_btn)
        view_hdr.addStretch()

        # Log-specific controls (hidden when calendar is active)
        self._log_controls = QWidget()
        self._log_controls.setStyleSheet("background: transparent;")
        lc_lay = QHBoxLayout(self._log_controls)
        lc_lay.setContentsMargins(0, 0, 0, 0)
        lc_lay.setSpacing(4)
        hint = dim_label("Double-click to edit  •  Right-click to delete", 9)
        lc_lay.addWidget(hint)
        expand_btn   = styled_btn("Expand All",   CARD, BORDER, TEXT_DIM, 9, False)
        collapse_btn = styled_btn("Collapse All", CARD, BORDER, TEXT_DIM, 9, False)
        clear_btn    = styled_btn("Clear All",    GREY, GREY_H, "#ffffff", 9)
        expand_btn.clicked.connect(self.expand_all)
        collapse_btn.clicked.connect(self.collapse_all)
        clear_btn.clicked.connect(self.clear_log)
        for b in (expand_btn, collapse_btn, clear_btn):
            lc_lay.addWidget(b)
        view_hdr.addWidget(self._log_controls)
        layout.addLayout(view_hdr)

        # ── Stacked widget: page 0 = log, page 1 = calendar ──────────────────
        self._view_stack = QStackedWidget()
        self._view_stack.setStyleSheet("background: transparent;")

        # Page 0: session log tree
        log_page = QWidget()
        log_page.setStyleSheet("background: transparent;")
        log_lay = QVBoxLayout(log_page)
        log_lay.setContentsMargins(0, 0, 0, 0)

        tree_frame = QFrame()
        tree_frame.setStyleSheet(f"QFrame {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}")
        tf_layout = QVBoxLayout(tree_frame)
        tf_layout.setContentsMargins(0, 0, 0, 0)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(7)
        self.tree.setHeaderLabels(["Project / Date", "Ticket", "Start", "End", "Duration", "Jira Sync", "Notes"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setIndentation(18)
        self.tree.setAnimated(True)
        self.tree.setUniformRowHeights(False)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tree.header().setSectionResizeMode(3, QHeaderView.Fixed)
        self.tree.header().setSectionResizeMode(4, QHeaderView.Fixed)
        self.tree.header().setSectionResizeMode(5, QHeaderView.Fixed)
        self.tree.header().setSectionResizeMode(6, QHeaderView.Stretch)
        self.tree.setColumnWidth(0, 200)
        self.tree.setColumnWidth(1, 90)
        self.tree.setColumnWidth(2, 65)
        self.tree.setColumnWidth(3, 65)
        self.tree.setColumnWidth(4, 90)
        self.tree.setColumnWidth(5, 95)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemCollapsed.connect(self._on_item_collapsed)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_tree_context_menu)

        tf_layout.addWidget(self.tree)
        log_lay.addWidget(tree_frame, 1)
        self._view_stack.addWidget(log_page)

        # Page 1: calendar
        self._calendar = CalendarView()
        self._view_stack.addWidget(self._calendar)

        layout.addWidget(self._view_stack, 1)

    def _style_view_tabs(self):
        """Style the Log / Calendar toggle buttons to reflect which is active."""
        for btn, is_active in (
            (self._log_tab_btn, self._view_stack.currentIndex() == 0 if hasattr(self, '_view_stack') else True),
            (self._cal_tab_btn, self._view_stack.currentIndex() == 1 if hasattr(self, '_view_stack') else False),
        ):
            if is_active and btn.isChecked():
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {SURFACE}; color: {TEXT};
                        border: 1px solid {BORDER}; border-bottom: 2px solid {ACCENT};
                        border-radius: 0px; font-size: 11px; font-weight: bold;
                        padding: 0 12px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent; color: {TEXT_DIM};
                        border: none; border-bottom: 2px solid transparent;
                        border-radius: 0px; font-size: 11px;
                        padding: 0 12px;
                    }}
                    QPushButton:hover {{ color: {TEXT}; border-bottom: 2px solid {BORDER}; }}
                """)

    def _switch_view(self, index):
        """Switch between log (0) and calendar (1)."""
        self._view_stack.setCurrentIndex(index)
        self._log_tab_btn.setChecked(index == 0)
        self._cal_tab_btn.setChecked(index == 1)
        self._log_controls.setVisible(index == 0)
        self._style_view_tabs()
        if index == 1:
            self.refresh_calendar()

    # ── Jira ──────────────────────────────────────────────────────────────────

    def _update_jira_status_label(self):
        j = self.data.get("jira", {})
        if j.get("url") and j.get("email") and j.get("token"):
            domain = j["url"].replace("https://","").replace("http://","").split("/")[0]
            self.jira_status_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 10px; background: transparent;")
            self.jira_status_lbl.setText(f"● {domain}")
        else:
            self.jira_status_lbl.setStyleSheet(f"color: {WARNING}; font-size: 10px; background: transparent;")
            self.jira_status_lbl.setText("● Not configured")

    def open_settings(self):
        dlg = SettingsDialog(self, self.data)
        dlg.theme_changed.connect(self.apply_theme)   # live preview
        prev_theme = self.data.get("settings", {}).get("theme", "dark")
        if dlg.exec() == QDialog.Accepted:
            save_data(self.data)
            self._update_jira_status_label()
            self.apply_theme(self.data["settings"].get("theme", "dark"))
        else:
            # Revert live preview if cancelled
            self.apply_theme(prev_theme)

    def apply_theme(self, theme_name):
        """Switch colour theme and fully rebuild the UI so every widget gets the new colours."""
        set_theme(theme_name)
        QApplication.instance().setStyleSheet(build_stylesheet())

        # Save splitter sizes and active view so they survive the rebuild
        splitter_sizes  = self._splitter.sizes() if hasattr(self, '_splitter') else None
        active_view_idx = self._view_stack.currentIndex() if hasattr(self, '_view_stack') else 0
        active_proj_tab = getattr(self, '_proj_tab', 'active')

        # Tear down and rebuild the entire central widget
        old = self.centralWidget()
        if old:
            old.deleteLater()

        self._build_ui()
        self.refresh_projects()
        self.refresh_log()
        self._update_jira_status_label()
        self._update_tray()

        # Restore splitter position
        if splitter_sizes and hasattr(self, '_splitter'):
            self._splitter.setSizes(splitter_sizes)

        # Restore active view (log vs calendar)
        if active_view_idx == 1:
            self._switch_view(1)

        # Restore project tab (active vs archived)
        if active_proj_tab == "archived":
            self._switch_proj_tab("archived")

        # Restore timer display state
        if self._timer_running:
            self.timer_lbl.setStyleSheet(f"color: {SUCCESS}; background: transparent; border: none;")
            self.start_btn.setText("⏹   Stop")
            self.start_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {RED}; color: white;
                    border: none; border-radius: 5px;
                    padding: 6px 14px; font-size: 13px; font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {RED_H}; }}
            """)
            self.project_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 12px; background: transparent; border: none;")


    def open_jira_settings(self):
        """Legacy shim — opens the new settings dialog."""
        self.open_settings()

    # ── Projects ──────────────────────────────────────────────────────────────

    def refresh_projects(self):
        # ── Active tab ────────────────────────────────────────────────────────
        while self.proj_layout.count() > 1:
            item = self.proj_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.data["projects"]:
            empty = QLabel("No projects yet.\nClick + Add to create one.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent;")
            self.proj_layout.insertWidget(0, empty)
        else:
            for i, proj in enumerate(self.data["projects"]):
                total     = total_seconds_for_project(self.data["sessions"], proj)
                is_active = (proj == self._active_project and self._timer_running)
                ticket    = self.data["ticket_map"].get(proj, "")
                bg        = ACCENT2 if is_active else CARD
                border_c  = ACCENT if is_active else BORDER

                row = QFrame()
                row.setStyleSheet(f"""
                    QFrame {{
                        background-color: {bg};
                        border: 1px solid {border_c};
                        border-radius: 7px;
                    }}
                """)
                rl = QHBoxLayout(row)
                rl.setContentsMargins(10, 8, 8, 8)
                rl.setSpacing(8)

                info = QVBoxLayout()
                info.setSpacing(2)
                dot = "🟢 " if is_active else "⚪ "
                name_lbl = QLabel(dot + proj)
                name_lbl.setStyleSheet(f"color: {TEXT}; font-size: 12px; font-weight: bold; background: transparent; border: none;")
                info.addWidget(name_lbl)

                sub_row = QHBoxLayout()
                sub_row.setSpacing(8)
                time_lbl = QLabel(fmt_duration(total))
                time_lbl.setStyleSheet(f"color: {SUCCESS if is_active else TEXT_DIM}; font-size: 10px; background: transparent; border: none;")
                sub_row.addWidget(time_lbl)
                if ticket:
                    tick_lbl = QLabel(f"🔗 {ticket}")
                    tick_lbl.setStyleSheet(f"color: {JIRA_BLUE}; font-size: 9px; background: transparent; border: none;")
                    sub_row.addWidget(tick_lbl)
                sub_row.addStretch()
                info.addLayout(sub_row)

                cats = self.data["category_map"].get(proj, [])
                if cats:
                    tags_row = QHBoxLayout()
                    tags_row.setSpacing(4)
                    tags_row.setContentsMargins(0, 0, 0, 0)
                    tag_palette = ProjectDialog.TAG_COLORS
                    all_cats    = self.data.get("categories", [])
                    for cat in cats:
                        idx      = all_cats.index(cat) if cat in all_cats else 0
                        bg_color = tag_palette[idx % len(tag_palette)]
                        tag = QLabel(cat)
                        tag.setStyleSheet(
                            f"background-color: {bg_color}; color: #ffffff; "
                            f"font-size: 8px; font-weight: bold; padding: 1px 6px; "
                            f"border-radius: 3px; border: none;"
                        )
                        tags_row.addWidget(tag)
                    tags_row.addStretch()
                    info.addLayout(tags_row)
                rl.addLayout(info, 1)

                btns = QHBoxLayout()
                btns.setSpacing(3)

                def _small_btn(text, color, hover, tc="#ffffff"):
                    b = QPushButton(text)
                    b.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {color}; color: {tc};
                            border: none; border-radius: 4px;
                            padding: 3px 7px; font-size: 11px; font-weight: bold;
                        }}
                        QPushButton:hover {{ background-color: {hover}; }}
                    """)
                    b.setCursor(Qt.PointingHandCursor)
                    b.setFixedHeight(26)
                    return b

                sel = _small_btn("▶", GREEN, GREEN_H, "#0a0a0a")
                sel.clicked.connect(lambda checked=False, p=proj: self.select_project(p))
                btns.addWidget(sel)

                add_e = _small_btn("⊕", PURPLE, PURPLE_H)
                add_e.clicked.connect(lambda checked=False, p=proj: self.add_manual_entry(p))
                btns.addWidget(add_e)

                if ticket:
                    info_b = _small_btn("ℹ", BLUE, BLUE_H)
                    info_b.clicked.connect(lambda checked=False, p=proj, t=ticket: self.open_jira_info(p, t))
                    btns.addWidget(info_b)

                edit_b = _small_btn("✎", JIRA_BLUE, "#0065ff")
                edit_b.clicked.connect(lambda checked=False, p=proj: self.edit_project(p))
                btns.addWidget(edit_b)

                arc_b = _small_btn("⊟", WARNING, "#c8a000", "#0a0a0a")
                arc_b.setToolTip("Archive this project")
                arc_b.clicked.connect(lambda checked=False, p=proj: self.archive_project(p))
                btns.addWidget(arc_b)

                del_b = _small_btn("✕", RED, RED_H)
                del_b.clicked.connect(lambda checked=False, p=proj: self.delete_project(p))
                btns.addWidget(del_b)

                rl.addLayout(btns)
                self.proj_layout.insertWidget(i, row)

        # ── Archived tab ──────────────────────────────────────────────────────
        self._refresh_archived()

        # Keep tab button counts up to date
        n_arch = len(self.data.get("archived_projects", []))
        arch_label = f"Archived ({n_arch})" if n_arch else "Archived"
        self._proj_tab_archived.setText(arch_label)

    def _refresh_archived(self):
        """Rebuild the archived projects list."""
        while self.archived_proj_layout.count() > 1:
            item = self.archived_proj_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        archived = self.data.get("archived_projects", [])
        if not archived:
            empty = QLabel("No archived projects.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent;")
            self.archived_proj_layout.insertWidget(0, empty)
            return

        for i, proj in enumerate(archived):
            total  = total_seconds_for_project(self.data["sessions"], proj)
            ticket = self.data["ticket_map"].get(proj, "")

            row = QFrame()
            row.setStyleSheet(f"""
                QFrame {{
                    background-color: {BG};
                    border: 1px solid {BORDER};
                    border-radius: 7px;
                    opacity: 0.8;
                }}
            """)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(10, 8, 8, 8)
            rl.setSpacing(8)

            info = QVBoxLayout()
            info.setSpacing(2)

            name_lbl = QLabel("📦 " + proj)
            name_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; font-weight: bold; background: transparent; border: none;")
            info.addWidget(name_lbl)

            sub_row = QHBoxLayout()
            sub_row.setSpacing(8)
            time_lbl = QLabel(fmt_duration(total))
            time_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; background: transparent; border: none;")
            sub_row.addWidget(time_lbl)
            if ticket:
                tick_lbl = QLabel(f"🔗 {ticket}")
                tick_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9px; background: transparent; border: none;")
                sub_row.addWidget(tick_lbl)
            sub_row.addStretch()
            info.addLayout(sub_row)

            cats = self.data["category_map"].get(proj, [])
            if cats:
                tags_row = QHBoxLayout()
                tags_row.setSpacing(4)
                tags_row.setContentsMargins(0, 0, 0, 0)
                tag_palette = ProjectDialog.TAG_COLORS
                all_cats    = self.data.get("categories", [])
                for cat in cats:
                    idx      = all_cats.index(cat) if cat in all_cats else 0
                    bg_color = tag_palette[idx % len(tag_palette)]
                    tag = QLabel(cat)
                    tag.setStyleSheet(
                        f"background-color: {bg_color}55; color: {TEXT_DIM}; "
                        f"font-size: 8px; font-weight: bold; padding: 1px 6px; "
                        f"border-radius: 3px; border: none;"
                    )
                    tags_row.addWidget(tag)
                tags_row.addStretch()
                info.addLayout(tags_row)
            rl.addLayout(info, 1)

            btns = QHBoxLayout()
            btns.setSpacing(3)

            def _small_btn(text, color, hover, tc="#ffffff"):
                b = QPushButton(text)
                b.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color}; color: {tc};
                        border: none; border-radius: 4px;
                        padding: 3px 7px; font-size: 11px; font-weight: bold;
                    }}
                    QPushButton:hover {{ background-color: {hover}; }}
                """)
                b.setCursor(Qt.PointingHandCursor)
                b.setFixedHeight(26)
                return b

            restore_b = _small_btn("↩ Restore", GREEN, GREEN_H, "#0a0a0a")
            restore_b.setToolTip("Move back to active projects")
            restore_b.clicked.connect(lambda checked=False, p=proj: self.restore_project(p))
            btns.addWidget(restore_b)

            del_b = _small_btn("✕", RED, RED_H)
            del_b.setToolTip("Permanently delete this project and all its sessions")
            del_b.clicked.connect(lambda checked=False, p=proj: self.delete_project(p, archived=True))
            btns.addWidget(del_b)

            rl.addLayout(btns)
            self.archived_proj_layout.insertWidget(i, row)

    def add_project(self):
        dlg = ProjectDialog(self,
                            all_categories=self.data["categories"])
        if dlg.exec() != QDialog.Accepted:
            return
        r = dlg.get_result()
        if not r:
            return
        name, ticket = r["name"], r["ticket"]
        if name in self.data["projects"]:
            QMessageBox.warning(self, "Duplicate", f'"{name}" already exists.')
            return
        self.data["projects"].append(name)
        if ticket:
            self.data["ticket_map"][name] = ticket
        # Persist any newly-created categories and this project's assignment
        self.data["categories"] = r["all_categories"]
        if r["categories"]:
            self.data["category_map"][name] = r["categories"]
        save_data(self.data)
        self.refresh_projects()

    def edit_project(self, name):
        ticket        = self.data["ticket_map"].get(name, "")
        assigned_cats = self.data["category_map"].get(name, [])
        dlg = ProjectDialog(self, name, ticket,
                            all_categories=self.data["categories"],
                            assigned_cats=assigned_cats)
        if dlg.exec() != QDialog.Accepted:
            return
        r = dlg.get_result()
        if not r:
            return
        new_name, new_ticket = r["name"], r["ticket"]

        if new_name != name:
            if new_name in self.data["projects"]:
                QMessageBox.warning(self, "Duplicate", f'"{new_name}" already exists.')
                return
            idx = self.data["projects"].index(name)
            self.data["projects"][idx] = new_name
            for s in self.data["sessions"]:
                if s["project"] == name:
                    s["project"] = new_name
            if name in self.data["ticket_map"]:
                self.data["ticket_map"][new_name] = self.data["ticket_map"].pop(name)
            if name in self.data["category_map"]:
                self.data["category_map"][new_name] = self.data["category_map"].pop(name)
            if self._active_project == name:
                self._active_project = new_name
                self.project_lbl.setText(new_name)

        if new_ticket:
            self.data["ticket_map"][new_name] = new_ticket
        else:
            self.data["ticket_map"].pop(new_name, None)

        # Update global category list and this project's assignment
        self.data["categories"] = r["all_categories"]
        if r["categories"]:
            self.data["category_map"][new_name] = r["categories"]
        else:
            self.data["category_map"].pop(new_name, None)

        save_data(self.data)
        self.refresh_projects()
        self.refresh_log()
        self._update_ticket_label()

    def archive_project(self, name):
        """Move a project from active to the archive."""
        if self._timer_running and self._active_project == name:
            QMessageBox.warning(self, "Active", "Stop the timer before archiving.")
            return
        self.data["projects"].remove(name)
        self.data.setdefault("archived_projects", [])
        if name not in self.data["archived_projects"]:
            self.data["archived_projects"].append(name)
        save_data(self.data)
        if self._active_project == name:
            self._active_project = ""
            self.project_lbl.setText("No project selected")
            self.ticket_lbl.setText("")
        self.refresh_projects()
        self.refresh_log()

    def restore_project(self, name):
        """Move a project from the archive back to active."""
        archived = self.data.get("archived_projects", [])
        if name in archived:
            archived.remove(name)
        if name not in self.data["projects"]:
            self.data["projects"].append(name)
        save_data(self.data)
        self.refresh_projects()
        self.refresh_log()

    def delete_project(self, name, archived=False):
        if not archived and self._timer_running and self._active_project == name:
            QMessageBox.warning(self, "Active", "Stop the timer before deleting.")
            return
        if QMessageBox.question(self, "Delete",
                f'Permanently delete "{name}" and all its sessions?\n'
                f'This cannot be undone.',
                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        if archived:
            self.data.get("archived_projects", []).remove(name) if name in self.data.get("archived_projects", []) else None
        else:
            if name in self.data["projects"]:
                self.data["projects"].remove(name)
        self.data["sessions"]    = [s for s in self.data["sessions"] if s["project"] != name]
        self.data["ticket_map"].pop(name, None)
        self.data["category_map"].pop(name, None)
        save_data(self.data)
        if self._active_project == name:
            self._active_project = ""
            self.project_lbl.setText("No project selected")
            self.ticket_lbl.setText("")
        self.refresh_projects()
        self.refresh_log()
        self.refresh_stats()

    def _run_jira_auto_archive(self):
        """Start a background Jira status check; auto-archives done/closed projects."""
        j = self.data.get("jira", {})
        if not (j.get("url") and j.get("email") and j.get("token")):
            return  # Jira not configured — silent skip

        # Only check projects that have tickets and are not already archived
        ticket_map = {
            p: self.data["ticket_map"][p]
            for p in self.data["projects"]
            if self.data["ticket_map"].get(p)
        }
        if not ticket_map:
            return

        # Disable button while running
        if hasattr(self, "_jira_check_btn"):
            self._jira_check_btn.setEnabled(False)
            self._jira_check_btn.setText("⟳ Checking…")

        self._archive_worker = JiraAutoArchiveWorker(j, ticket_map)
        self._archive_worker.done.connect(self._on_auto_archive_done)
        self._archive_worker.start()

    def _on_auto_archive_done(self, to_archive, error_msg):
        """Called when the Jira status check finishes."""
        if hasattr(self, "_jira_check_btn"):
            self._jira_check_btn.setEnabled(True)
            self._jira_check_btn.setText("⟳ Jira")

        if to_archive:
            names = "\n".join(f"  • {p}" for p in to_archive)
            reply = QMessageBox.question(
                self, "Auto-Archive Projects",
                f"The following projects have a completed Jira ticket\n"
                f"(Done / Closed / Resolved) and can be archived:\n\n"
                f"{names}\n\n"
                f"Archive them now?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                for name in to_archive:
                    if name in self.data["projects"]:
                        self.data["projects"].remove(name)
                        self.data.setdefault("archived_projects", [])
                        if name not in self.data["archived_projects"]:
                            self.data["archived_projects"].append(name)
                save_data(self.data)
                self.refresh_projects()
                self.refresh_log()
                # Switch to the archived tab so user sees the result
                self._switch_proj_tab("archived")

        if error_msg:
            # Non-blocking: just update the Jira status label
            existing = self.jira_status_lbl.text()
            self.jira_status_lbl.setToolTip(f"Errors during status check:\n{error_msg}")

    def select_project(self, name):
        if self._timer_running:
            if QMessageBox.question(self, "Switch Project",
                    f"Stop current timer and switch to {name}?",
                    QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                return
            self._stop_timer(save=True)
        self._active_project = name
        self.project_lbl.setText(name)
        self._update_ticket_label()
        self.refresh_projects()
        self._update_tray()

    def add_manual_entry(self, project):
        ticket = self.data["ticket_map"].get(project, "")
        j = self.data.get("jira", {})
        jira_ok = bool(j.get("url") and j.get("email") and j.get("token"))

        dlg = ManualEntryDialog(self, project, ticket, jira_ok)
        if dlg.exec() != QDialog.Accepted:
            return
        r = dlg.get_result()
        if not r:
            return

        session  = r["session"]
        do_sync  = r["sync"]
        self.data["sessions"].append(session)
        save_data(self.data)
        self.refresh_log()
        self.refresh_stats()
        self.refresh_projects()

        # Auto-expand the project row in the tree
        self._expanded_projs.add(project)
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            pname = item.data(0, Qt.UserRole)
            if pname == project:
                item.setExpanded(True)
                break

        if do_sync:
            self._jira_sync_async(session, session["duration"])

    def open_jira_info(self, project, ticket):
        j = self.data.get("jira", {})
        if not j.get("url") or not j.get("email") or not j.get("token"):
            QMessageBox.warning(self, "Not Configured",
                "Please configure your Jira credentials first (⚙ Jira Settings).")
            return
        dlg = JiraIssueInfoDialog(self, ticket, j)
        dlg.show()

    def _update_ticket_label(self):
        ticket = self.data["ticket_map"].get(self._active_project, "")
        if ticket:
            self.ticket_lbl.setText(f"🔗 Jira: {ticket}")
        else:
            self.ticket_lbl.setText("No Jira ticket linked  —  click ✎ to add one")

    # ── Timer ─────────────────────────────────────────────────────────────────

    def toggle_timer(self):
        if not self._active_project:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return
        if self._timer_running:
            self._stop_timer(save=True)
        else:
            self._start_timer()

    def _start_timer(self):
        self._timer_running = True
        self._start_time    = time.time()
        self._elapsed       = 0
        self.start_btn.setText("⏹   Stop")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {RED}; color: white;
                border: none; border-radius: 5px;
                padding: 6px 14px; font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {RED_H}; }}
        """)
        self.project_lbl.setStyleSheet(f"color: {SUCCESS}; font-size: 12px; background: transparent; border: none;")
        self._update_ticket_label()
        self.refresh_projects()
        self._update_tray()

    def _stop_timer(self, save=True):
        if not self._timer_running:
            return
        duration   = time.time() - self._start_time
        start_snap = self._start_time
        proj       = self._active_project

        self._timer_running = False
        self.start_btn.setText("▶   Start")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GREEN}; color: #0a0a0a;
                border: none; border-radius: 5px;
                padding: 6px 14px; font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {GREEN_H}; }}
        """)
        self.project_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent; border: none;")
        self.timer_lbl.setText("00:00:00")
        self.timer_lbl.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")

        if not save or duration < 1:
            return

        ticket     = self.data["ticket_map"].get(proj, "")
        sync_dur   = duration
        do_sync    = False

        if ticket:
            dlg = EditTimeSyncDialog(self, proj, ticket, duration)
            if dlg.exec() == QDialog.Accepted and dlg.get_action() == "sync":
                sync_dur = dlg.get_duration()
                do_sync  = True

        jira_sync_status = "pending" if do_sync else ("none" if not ticket else "skipped")
        session = {
            "project":   proj,
            "ticket":    ticket,
            "start":     start_snap,
            "end":       time.time(),
            "duration":  duration,
            "date":      datetime.now().strftime("%Y-%m-%d"),
            "jira_sync": jira_sync_status,
        }
        self.data["sessions"].append(session)
        save_data(self.data)
        self.refresh_log()
        self.refresh_stats()
        self.refresh_projects()
        self._update_tray()

        if do_sync:
            self._jira_sync_async(session, sync_dur)

    def _jira_sync_async(self, session, duration_secs):
        worker = JiraSyncWorker(self.data["jira"], session, duration_secs)
        self._workers.append(worker)
        worker.done.connect(self._on_jira_sync_done)
        worker.start()
        self.jira_status_lbl.setText("⟳ Syncing…")
        self.jira_status_lbl.setStyleSheet(f"color: {WARNING}; font-size: 10px; background: transparent;")

    def _on_jira_sync_done(self, ticket, ok, err, start_ts, proj_name, worklog_id=None):
        for s in self.data["sessions"]:
            if s["start"] == start_ts and s["project"] == proj_name:
                s["jira_sync"] = "synced" if ok else f"failed: {err}"
                if ok and worklog_id:
                    s["jira_worklog_id"] = worklog_id
                break
        save_data(self.data)

        # Clean up worker
        self._workers = [w for w in self._workers if w.isRunning()]

        self._update_jira_status_label()
        self.refresh_log()

        if ok:
            QMessageBox.information(self, "Jira Sync",
                f"Worklog posted to {ticket} successfully.")
        else:
            QMessageBox.warning(self, "Jira Sync Failed",
                f"Could not post worklog to {ticket}:\n\n{err}\n\n"
                "Check your Jira settings and try again.")

    def _tick(self):
        if self._timer_running and self._start_time:
            self._elapsed = time.time() - self._start_time
            self.timer_lbl.setText(fmt_duration(self._elapsed))
            self.timer_lbl.setStyleSheet(f"color: {SUCCESS}; background: transparent; border: none;")

    # ── Tree / Log ────────────────────────────────────────────────────────────

    def _on_item_expanded(self, item):
        name = item.data(0, Qt.UserRole)
        if name:
            self._expanded_projs.add(name)

    def _on_item_collapsed(self, item):
        name = item.data(0, Qt.UserRole)
        if name:
            self._expanded_projs.discard(name)

    def _on_item_double_clicked(self, item, column):
        # Session child items have a session dict stored
        session = item.data(0, Qt.UserRole + 1)
        if not session:
            # It's a project row — toggle expand/collapse
            item.setExpanded(not item.isExpanded())
            return
        dlg = EditSessionDialog(self, session)
        if dlg.exec() != QDialog.Accepted:
            return
        r = dlg.get_result()
        if not r:
            return
        new_dur  = r["duration"]
        resync   = r["resync"]
        new_note = r.get("note", "")
        for s in self.data["sessions"]:
            if s["start"] == session["start"] and s["project"] == session["project"]:
                s["duration"]  = new_dur
                s["end"]       = s["start"] + new_dur
                s["note"]      = new_note
                if resync and s.get("ticket"):
                    s["jira_sync"] = "pending"
                break
        save_data(self.data)
        self.refresh_log()
        self.refresh_stats()
        self.refresh_projects()
        if resync and session.get("ticket"):
            updated = next(
                (s for s in self.data["sessions"]
                 if s["start"] == session["start"] and s["project"] == session["project"]),
                None)
            if updated:
                self._jira_sync_async(updated, new_dur)

    # ── Context menu & delete ─────────────────────────────────────────────────

    def _on_tree_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        session = item.data(0, Qt.UserRole + 1)
        if not session:
            return  # project row — no context menu

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {SURFACE}; color: {TEXT};
                border: 1px solid {BORDER}; border-radius: 6px;
                padding: 4px; font-size: 13px;
            }}
            QMenu::item {{ padding: 8px 24px 8px 16px; border-radius: 4px; }}
            QMenu::item:selected {{ background-color: {ACCENT2}; }}
            QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 8px; }}
        """)

        edit_act = QAction("✎  Edit Entry", self)
        edit_act.triggered.connect(lambda: self._edit_session_item(item))
        menu.addAction(edit_act)

        menu.addSeparator()

        del_act = QAction("✕  Delete Entry", self)
        del_act.triggered.connect(lambda: self._delete_session(session))
        menu.addAction(del_act)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _edit_session_item(self, item):
        """Trigger edit for a session item (same as double-click)."""
        self._on_item_double_clicked(item, 0)

    def _delete_session(self, session):
        proj    = session.get("project", "")
        ticket  = session.get("ticket", "")
        wid     = session.get("jira_worklog_id")
        date    = datetime.fromtimestamp(session["start"]).strftime("%b %d, %Y  %H:%M")
        dur     = fmt_duration(session["duration"])
        synced  = session.get("jira_sync") == "synced" and ticket and wid

        # Build confirmation message
        msg = f"Delete this time entry?\n\n  {proj}  \u2022  {date}  \u2022  {dur}"
        also_jira = False
        if synced:
            j = self.data.get("jira", {})
            jira_ok = bool(j.get("url") and j.get("email") and j.get("token"))
            if jira_ok:
                msg += f"\n\nThis entry was synced to Jira ({ticket}).\nDelete the worklog from Jira as well?"
                reply = QMessageBox.question(
                    self, "Delete Entry", msg,
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Cancel
                )
                if reply == QMessageBox.Cancel:
                    return
                also_jira = (reply == QMessageBox.Yes)
            else:
                # Jira not configured — just confirm local delete
                reply = QMessageBox.question(self, "Delete Entry", msg,
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
        else:
            reply = QMessageBox.question(self, "Delete Entry", msg,
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return

        # Remove from local data
        self.data["sessions"] = [
            s for s in self.data["sessions"]
            if not (s["start"] == session["start"] and s["project"] == session["project"])
        ]
        save_data(self.data)
        self.refresh_log()
        self.refresh_stats()
        self.refresh_projects()

        # Delete from Jira asynchronously
        if also_jira:
            worker = JiraDeleteWorker(self.data["jira"], ticket, wid)
            self._workers.append(worker)
            worker.done.connect(lambda ok, err: self._on_jira_delete_done(ticket, ok, err))
            worker.start()
            self.jira_status_lbl.setText("⟳ Deleting…")
            self.jira_status_lbl.setStyleSheet(f"color: {WARNING}; font-size: 10px; background: transparent;")

    def _on_jira_delete_done(self, ticket, ok, err):
        self._workers = [w for w in self._workers if w.isRunning()]
        self._update_jira_status_label()
        if ok:
            QMessageBox.information(self, "Jira", f"Worklog deleted from {ticket}.")
        else:
            QMessageBox.warning(self, "Jira Delete Failed",
                f"Could not delete worklog from {ticket}:\n\n{err}")

    def expand_all(self):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setExpanded(True)
            self._expanded_projs.add(item.data(0, Qt.UserRole))

    def collapse_all(self):
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setExpanded(False)
        self._expanded_projs.clear()

    def refresh_log(self):
        self.tree.clear()

        # Group sessions by project
        proj_sessions = {}
        for proj in self.data["projects"]:
            proj_sessions[proj] = sorted(
                [s for s in self.data["sessions"] if s["project"] == proj],
                key=lambda s: s["start"], reverse=True)
        # Orphaned sessions
        known = set(self.data["projects"])
        for s in self.data["sessions"]:
            p = s["project"]
            if p not in known:
                proj_sessions.setdefault(p, []).append(s)

        for proj, sessions in proj_sessions.items():
            total   = sum(s["duration"] for s in sessions)
            ticket  = self.data["ticket_map"].get(proj, "")
            is_act  = (proj == self._active_project and self._timer_running)
            dot     = "🟢 " if is_act else "⚪ "
            n       = len(sessions)
            count_s = f"{n} session{'s' if n != 1 else ''}"

            parent = QTreeWidgetItem(self.tree)
            parent.setText(0, f"{dot}{proj}")
            parent.setText(1, ticket or "—")
            parent.setText(2, "")
            parent.setText(3, "")
            parent.setText(4, fmt_duration(total))
            parent.setText(5, count_s)
            parent.setText(6, "")
            parent.setData(0, Qt.UserRole, proj)          # project name
            parent.setData(0, Qt.UserRole + 1, None)      # not a session

            proj_font_bold   = QFont()
            proj_font_bold.setPointSize(12)
            proj_font_bold.setBold(True)
            proj_font_normal = QFont()
            proj_font_normal.setPointSize(12)

            bg = QColor(ACCENT2) if is_act else QColor(CARD)
            for col in range(7):
                parent.setBackground(col, bg)
                parent.setForeground(col, QColor(TEXT))
                parent.setFont(col, proj_font_bold if col == 0 else proj_font_normal)
            parent.setForeground(1, QColor(JIRA_BLUE if ticket else TEXT_DIM))
            parent.setForeground(5, QColor(TEXT_DIM))
            parent.setForeground(6, QColor(TEXT_DIM))
            parent.setSizeHint(0, QSize(0, 40))

            parent.setExpanded(proj in self._expanded_projs)

            sess_font = QFont()
            sess_font.setPointSize(11)

            for i, s in enumerate(sessions):
                date = datetime.fromtimestamp(s["start"]).strftime("%b %d, %Y")
                st   = datetime.fromtimestamp(s["start"]).strftime("%H:%M")
                en   = datetime.fromtimestamp(s["end"]).strftime("%H:%M")
                dur  = fmt_duration(s["duration"])
                sync = s.get("jira_sync", "none")

                if sync == "synced":
                    sync_lbl, sync_col = "✅ Synced",  SUCCESS
                elif sync == "skipped":
                    sync_lbl, sync_col = "⏭ Skipped", TEXT_DIM
                elif not s.get("ticket") or sync == "none":
                    sync_lbl, sync_col = "—",          TEXT_DIM
                elif sync == "pending":
                    sync_lbl, sync_col = "⟳ Pending",  WARNING
                else:
                    sync_lbl, sync_col = "⚠ Failed",   WARNING

                manual_badge = "  ✏" if s.get("manual") else ""
                child = QTreeWidgetItem(parent)
                note_text = s.get("note", "") or ""
                child.setText(0, f"  {date}{manual_badge}")
                child.setText(1, "")
                child.setText(2, st)
                child.setText(3, en)
                child.setText(4, dur)
                child.setText(5, sync_lbl)
                child.setText(6, note_text)
                child.setData(0, Qt.UserRole, None)
                child.setData(0, Qt.UserRole + 1, s)
                child.setSizeHint(0, QSize(0, 34))

                row_bg = QColor(SURFACE) if i % 2 == 0 else QColor(ALT_ROW)
                for col in range(7):
                    child.setBackground(col, row_bg)
                    child.setFont(col, sess_font)
                    child.setForeground(col, QColor(TEXT_DIM))
                child.setForeground(5, QColor(sync_col))
                child.setForeground(6, QColor(TEXT_DIM))

        self.refresh_stats()
        self.refresh_calendar()

    def refresh_stats(self):
        sessions = self.data["sessions"]
        for i, window_key in enumerate(self.data["stat_configs"][:3]):
            info = STAT_WINDOWS.get(window_key, STAT_WINDOWS["all_time"])
            label, fn = info
            self.stat_title_labels[i].setText(label.upper())
            self.stat_value_labels[i].setText(fmt_duration(fn(sessions)))


    def refresh_calendar(self):
        if hasattr(self, "_calendar"):
            self._calendar.refresh(
                self.data.get("sessions", []),
                self.data.get("category_map", {}),
            )
    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.MouseButtonPress and obj in self.stat_cards:
            slot_idx = obj.property("slot_idx")
            self._show_stat_menu(slot_idx, obj)
            return True
        return super().eventFilter(obj, event)

    def _show_stat_menu(self, slot_idx, card_widget):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {SURFACE}; color: {TEXT};
                border: 1px solid {BORDER}; border-radius: 6px;
                padding: 4px; font-size: 12px;
            }}
            QMenu::item {{ padding: 7px 24px 7px 14px; border-radius: 4px; }}
            QMenu::item:selected {{ background-color: {ACCENT2}; }}
            QMenu::item:checked {{ color: {SUCCESS}; }}
            QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 8px; }}
        """)
        current = self.data["stat_configs"][slot_idx] if slot_idx < len(self.data["stat_configs"]) else "all_time"
        for key, (label, _) in STAT_WINDOWS.items():
            act = QAction(label, self)
            act.setCheckable(True)
            act.setChecked(key == current)
            act.setProperty("window_key", key)
            act.triggered.connect(lambda checked, k=key, idx=slot_idx: self._set_stat_window(idx, k))
            menu.addAction(act)
        # show below card
        pos = card_widget.mapToGlobal(card_widget.rect().bottomLeft())
        menu.exec(pos)

    def _set_stat_window(self, slot_idx, window_key):
        while len(self.data["stat_configs"]) <= slot_idx:
            self.data["stat_configs"].append("all_time")
        self.data["stat_configs"][slot_idx] = window_key
        save_data(self.data)
        self.refresh_stats()

    def open_export(self):
        dlg = ExportDialog(self, self.data)
        dlg.exec()

    # ── Tray ──────────────────────────────────────────────────────────────────

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._tray = None
            return
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(QIcon(make_tray_pixmap(GREEN)))
        self._tray.setToolTip("TimeTrack  •  Idle")
        self._tray_menu = QMenu()
        self._tray_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {SURFACE}; color: {TEXT};
                border: 1px solid {BORDER}; border-radius: 6px;
                padding: 4px; font-size: 13px;
            }}
            QMenu::item {{ padding: 8px 24px 8px 16px; border-radius: 4px; }}
            QMenu::item:selected {{ background-color: {ACCENT2}; }}
            QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 8px; }}
        """)
        self._tray.setContextMenu(self._tray_menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()
        self._update_tray()

    def _update_tray(self):
        if not hasattr(self, "_tray") or not self._tray:
            return
        color = RED if self._timer_running else GREEN
        self._tray.setIcon(QIcon(make_tray_pixmap(color)))
        if self._timer_running and self._active_project:
            self._tray.setToolTip(f"TimeTrack  •  ⏱ {self._active_project}")
        else:
            self._tray.setToolTip("TimeTrack  •  Idle")

        menu = self._tray_menu
        menu.clear()

        # Status label
        status_act = QAction("⏱ " + (self._active_project or "Idle"), self)
        status_act.setEnabled(False)
        menu.addAction(status_act)
        menu.addSeparator()

        # Start / Stop
        if self._timer_running:
            stop_act = QAction("⏹  Stop Timer", self)
            stop_act.triggered.connect(lambda: self._stop_timer(save=True))
            menu.addAction(stop_act)
        else:
            if self._active_project:
                start_act = QAction(f"▶  Start  ({self._active_project})", self)
                start_act.triggered.connect(self._start_timer)
                menu.addAction(start_act)

        menu.addSeparator()

        # Project quick-select
        for proj in self.data.get("projects", []):
            act = QAction(("🟢 " if proj == self._active_project else "⚪ ") + proj, self)
            act.triggered.connect(lambda checked=False, p=proj: self._tray_select_project(p))
            menu.addAction(act)

        menu.addSeparator()

        show_act = QAction("Show Window", self)
        show_act.triggered.connect(self.show)
        show_act.triggered.connect(self.activateWindow)
        menu.addAction(show_act)

        quit_act = QAction("Quit TimeTrack", self)
        quit_act.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_act)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def _tray_select_project(self, name):
        self.show(); self.activateWindow()
        self.select_project(name)

    def clear_log(self):
        if not self.data["sessions"]:
            return
        if QMessageBox.question(self, "Clear Log",
                "Delete all session history?",
                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        self.data["sessions"] = []
        save_data(self.data)
        self.refresh_log()
        self.refresh_projects()

    def closeEvent(self, event):
        if self._timer_running:
            self._stop_timer(save=True)
        self._tick_timer.stop()
        for w in self._workers:
            w.wait(2000)
        event.accept()

# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("TimeTrack")
    app.setOrganizationName("TimeTrack")
    app.setStyleSheet(build_stylesheet())
    window = TimeTrackerApp()
    window.show()
    sys.exit(app.exec())
