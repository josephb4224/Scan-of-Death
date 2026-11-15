#!/usr/bin/env python3
"""
Scan of Death - Nmap GUI Frontend
Death's Head Software
"""

# --- TOC of recent changes/tests ----
# ------------------------------------
# - Lines 290-300:  Splash screen
# - Lines 521-529: Command: text box
# ------------------------------------

from __future__ import annotations

import ctypes
import json
import os
import re
import shlex
import tempfile
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QAction, QColor, QFont, QIcon, QPixmap, QTextCursor, QPainter,
)
from PyQt6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox,
    QFileDialog, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar,
    QPushButton, QRadioButton, QScrollArea, QSpinBox, QSplashScreen,
    QSplitter, QStatusBar, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

# ---------------------------------------------------------------------------
# App constants
# ---------------------------------------------------------------------------
APP_NAME    = "Scan of Death"
ORG_NAME    = "Death's Head Software"
APP_VERSION = "1.0.0"


def _startup_log_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "scan_of_death_startup.log"
    return Path(tempfile.gettempdir()) / "scan_of_death_startup.log"

def _log_startup(message: str) -> None:
    try:
        with _startup_log_path().open("a", encoding="utf-8") as fh:
            fh.write(message + "\n")
    except Exception:
        pass


def resource_path(relative: str) -> str:
    base = getattr(sys, "_MEIPASS", Path(__file__).parent)
    return str(Path(base) / relative)


# Load the Nmap_Cheatsheet.md file
def _load_cheatsheet_text() -> str:
    candidates = [
        Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / ".Nmap_Cheatsheet.md",
        Path(__file__).resolve().parent.parent / ".Nmap_Cheatsheet.md",
    ]
    for cheatsheet_path in candidates:
        if cheatsheet_path.exists():
            try:
                return cheatsheet_path.read_text(encoding="utf-8")
            except Exception:
                pass
    return (
        "# Cheatsheet not found\n"
        "Your .Nmap_Cheatsheet.md file was not found in the app root.\n\n"
        "Place .Nmap_Cheatsheet.md next to the Source folder or bundle it with your exe.\n"
        "If you want this tab to always show content, include the file in the PyInstaller bundle."
    )


def _report_cheatsheet_error(exc: Exception) -> None:
    _log_startup(f"Cheatsheet initialization failed: {exc!r}")
    print("[Scan of Death] Cheatsheet initialization failed:", file=sys.stderr)
    traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)


# Convert Markdown to HTML using the markdown library
def _markdown_to_html(md_text: str) -> str:
    """Convert markdown to styled HTML using the markdown library."""
    try:
        import markdown
        # Use 'extra' for tables, fenced code blocks, etc.
        # Use 'smarty' for typographically correct punctuation.
        return markdown.markdown(md_text, extensions=["extra", "smarty"])
    except ImportError:
        # Fallback to a very basic converter if markdown is not installed
        _log_startup("Markdown library not found. Falling back to basic conversion.")
        html = md_text.replace("\n", "<br>")
        return f"<pre>{html}</pre>"


def _set_cheatsheet_content(widget: QTextEdit) -> None:
    """Set cheatsheet content with markdown formatting."""
    try:
        cheatsheet_text = _load_cheatsheet_text()
    except Exception as exc:
        _report_cheatsheet_error(exc)
        widget.setHtml(
            "<h3 style='color:#cc0000;'>Cheatsheet failed to load</h3>"
            f"<p>{exc}</p>"
            "<p>Check the console build output for the full traceback.</p>"
        )
        return

    # Convert markdown to HTML
    html_content = _markdown_to_html(cheatsheet_text)
    
    # CSS for the markdown content
    md_css = """
    <style>
        body { font-family: 'Courier New', Courier, monospace; font-size: 12px; color: #00cc00; line-height: 1.5; }
        h1, h2, h3, h4, h5, h6 { color: #cc0000; margin-top: 15px; margin-bottom: 5px; font-weight: bold; }
        h1 { font-size: 20px; border-bottom: 2px solid #cc0000; padding-bottom: 5px; }
        h2 { font-size: 17px; border-bottom: 1px solid #444; padding-bottom: 4px; }
        h3 { font-size: 15px; border-bottom: 1px solid #333; padding-bottom: 3px; }
        h4 { font-size: 14px; }
        table { border-collapse: collapse; width: 100%; margin: 10px 0; background-color: #0d0d0d; }
        th { border: 1px solid #444; padding: 6px 8px; background-color: #1a1a1a; color: #cc0000; text-align: left; }
        td { border: 1px solid #333; padding: 4px 8px; color: #00cc00; }
        code { background-color: #1a1a1a; color: #00ff00; padding: 2px 4px; border-radius: 3px; font-family: Consolas, 'Courier New', monospace; }
        pre { background-color: #080808; border: 1px solid #333; padding: 10px; border-radius: 5px; margin: 10px 0; overflow-x: auto; }
        pre code { background-color: transparent; padding: 0; }
        a { color: #cc0000; text-decoration: underline; }
        ul, ol { margin: 10px 0; padding-left: 25px; }
        li { margin-bottom: 4px; }
        hr { border: none; border-top: 1px solid #333; margin: 15px 0; }
        blockquote { border-left: 3px solid #cc0000; padding-left: 10px; color: #888; margin: 10px 0; }
    </style>
    """
    
    # Wrap in a styled div
    styled_html = f"""
    <html>
    <head>{md_css}</head>
    <body>
        <div style="padding: 10px;">
            {html_content}
        </div>
    </body>
    </html>
    """
    
    widget.setHtml(styled_html)


# ---------------------------------------------------------------------------
# Dark stylesheet - Death's Head red-on-black palette
# ---------------------------------------------------------------------------
DARK_STYLE = """
QWidget {
    background-color: #141414;
    color: #e0e0e0;
    font-family: Courier, monospace;
    font-size: 12px;
}
QMainWindow { background-color: #141414; }

QTabWidget::pane { border: 1px solid #333; background-color: #1a1a1a; }
QTabBar::tab {
    background-color: #1a1a1a; color: #888;
    padding: 6px 14px; border: 1px solid #333;
    border-bottom: none; margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #2a2a2a; color: #fff;
    border-bottom: 2px solid #cc0000;
}
QTabBar::tab:hover { background-color: #252525; color: #ccc; }

QGroupBox {
    border: 1px solid #333; border-radius: 6px;
    margin-top: 12px; padding-top: 10px;
    color: #cc0000; font-weight: bold;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }

QLineEdit {
    background-color: #0d0d0d; border: 1px solid #333;
    border-radius: 4px; padding: 5px 8px; color: #00cc00;
    selection-background-color: #cc0000;
}
QLineEdit:focus { border: 1px solid #cc0000; background-color: #1a1a1a; }

QPlainTextEdit, QTextEdit {
    background-color: #080808; border: 1px solid #222;
    color: #00cc00; font-family: 'Courier New', monospace; font-size: 12px;
    selection-background-color: #cc0000;
}

QComboBox {
    background-color: #1a1a1a; border: 1px solid #333;
    border-radius: 4px; padding: 4px 8px; color: #e0e0e0;
}
QComboBox:focus { border-color: #cc0000; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background-color: #1a1a1a; border: 1px solid #333;
    selection-background-color: #cc0000; color: #e0e0e0;
}

QCheckBox { spacing: 8px; color: #e0e0e0; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #444; border-radius: 3px; background-color: #141414;
}
QCheckBox::indicator:checked { background-color: #cc0000; border-color: #cc0000; }

QRadioButton { spacing: 8px; color: #e0e0e0; }
QRadioButton::indicator {
    width: 16px; height: 16px;
    border: 1px solid #444; border-radius: 9px; background-color: #141414;
}
QRadioButton::indicator:checked { background-color: #cc0000; border-color: #cc0000; }

QSpinBox, QDoubleSpinBox {
    background-color: #1a1a1a; border: 1px solid #333;
    border-radius: 4px; padding: 4px 8px; color: #e0e0e0;
}
QSpinBox:focus, QDoubleSpinBox:focus { border-color: #cc0000; }

QPushButton {
    background-color: #1e1e1e; border: 1px solid #444;
    border-radius: 4px; padding: 6px 16px; color: #d0d0d0; font-weight: bold;
}
QPushButton:hover { background-color: #2a2a2a; border-color: #cc0000; color: #fff; }
QPushButton:pressed { background-color: #8b0000; border-color: #cc0000; }

QPushButton#scanBtn {
    background-color: #8b0000; border: 1px solid #cc0000;
    color: #fff; font-size: 14px; padding: 8px 28px;
}
QPushButton#scanBtn:hover { background-color: #cc0000; }
QPushButton#scanBtn:disabled { background-color: #3a0000; color: #666; border-color: #500; }

QPushButton#stopBtn {
    background-color: #1a1a1a; border: 1px solid #444;
    color: #666; font-size: 14px; padding: 8px 28px;
}
QPushButton#stopBtn:enabled { border-color: #cc6600; color: #cc6600; }
QPushButton#stopBtn:hover:enabled { background-color: #cc6600; color: #fff; }

QLabel { color: #e0e0e0; }
QLabel#privWarn {
    color: #ff9900;
    font-family: Courier, monospace;
    font-size: 11px;
    font-weight: bold;
    background-color: #1a0f00;
    border: 1px solid #cc6600;
    padding: 3px 8px;
    border-radius: 3px;
}
QLabel#privOk {
    color: #00aa00;
    font-family: Courier, monospace;
    font-size: 11px;
    background-color: #001a00;
    border: 1px solid #006600;
    padding: 3px 8px;
    border-radius: 3px;
}
QLabel#cmdLabel {
    color: #00aa00; font-family: Courier, monospace; font-size: 11px;
    background-color: #0d0d0d; border: 1px solid #333;
    padding: 4px 6px; border-radius: 3px;
}

QScrollBar:vertical {
    background-color: #1a1a1a; width: 10px; border: none;
}
QScrollBar::handle:vertical {
    background-color: #444; border-radius: 4px; min-height: 20px;
}
QScrollBar::handle:vertical:hover { background-color: #cc0000; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background-color: #1a1a1a; height: 10px; border: none;
}
QScrollBar::handle:horizontal {
    background-color: #444; border-radius: 4px; min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background-color: #cc0000; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QScrollArea { border: none; }
QSplitter::handle { background-color: #333; }

QProgressBar {
    background-color: #1a1a1a;
    border: 1px solid #333;
    border-radius: 3px;
    height: 14px;
    text-align: center;
    color: #e0e0e0;
    font-size: 11px;
}
QProgressBar::chunk {
    background-color: #cc0000;
    border-radius: 2px;
}

QStatusBar {
    background-color: #0d0d0d; color: #666; border-top: 1px solid #333;
}
QMenuBar { background-color: #141414; color: #e0e0e0; border-bottom: 1px solid #333; }
QMenuBar::item:selected { background-color: #cc0000; }
QMenu { background-color: #1e1e1e; border: 1px solid #444; color: #e0e0e0; }
QMenu::item:selected { background-color: #cc0000; }
"""


# ---------------------------------------------------------------------------
# Splash screen
# ---------------------------------------------------------------------------
def create_splash() -> QSplashScreen | None:
    """Create and return a styled splash screen."""
    try:
        splash_path = Path(resource_path("splash.png"))
        if splash_path.exists():
            pixmap = QPixmap(str(splash_path))
            if pixmap.isNull():
                pixmap = QPixmap(800, 600)
                pixmap.fill(QColor(20, 20, 20))
            if pixmap.width() != 800 or pixmap.height() != 600:
                pixmap = pixmap.scaled(
                    800, 600,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
        else:
            pixmap = QPixmap(800, 600)
            pixmap.fill(QColor(20, 20, 20))

        # Create a painter to draw on the pixmap
        painter = QPainter(pixmap)
        
        # Add a subtle dark overlay to the bottom for better message visibility
        overlay_height = 120
        painter.fillRect(
            0, pixmap.height() - overlay_height, 
            pixmap.width(), overlay_height, 
            QColor(0, 0, 0, 160)
        )

        # Draw App Name (Red/White combo)
        painter.setPen(QColor(204, 0, 0)) # Death's Head Red
        painter.setFont(QFont("Courier New", 42, QFont.Weight.Bold))
        tr = pixmap.rect()
        tr.setTop(60)
        tr.setBottom(140)
        painter.drawText(tr, Qt.AlignmentFlag.AlignCenter, APP_NAME)

        # Draw Org Name at the bottom
        painter.setPen(QColor(180, 180, 180))
        painter.setFont(QFont("Courier New", 12, QFont.Weight.Normal))
        fr = pixmap.rect()
        fr.setTop(pixmap.height() - 40)
        fr.setBottom(pixmap.height() - 10)
        painter.drawText(fr, Qt.AlignmentFlag.AlignCenter, f"© {ORG_NAME}")

        painter.end()

        splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        return splash
    except Exception as e:
        _log_startup(f"Splash error: {e!r}")
        print("Splash error:", e)
        return None


# ---------------------------------------------------------------------------
# Nmap runner thread
# ---------------------------------------------------------------------------
class NmapThread(QThread):
    output_ready  = pyqtSignal(str)
    scan_finished = pyqtSignal(int)

    def __init__(self, cmd: list[str]) -> None:
        super().__init__()
        self.cmd = cmd
        self._proc: subprocess.Popen | None = None

    def run(self) -> None:
        try:
            kwargs = {}
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            self._proc = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
                bufsize=1,
                **kwargs,
            )
            for line in self._proc.stdout:
                self.output_ready.emit(line.rstrip())
            self._proc.wait()
            self.scan_finished.emit(self._proc.returncode)
        except FileNotFoundError:
            self.output_ready.emit(
                "[ERROR] nmap not found. Please install nmap and ensure it is in PATH."
            )
            self.scan_finished.emit(-1)
        except Exception as exc:
            self.output_ready.emit(f"[ERROR] {exc}")
            self.scan_finished.emit(-1)

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()


# ---------------------------------------------------------------------------
# Helper: wrap a widget in a scroll area
# ---------------------------------------------------------------------------
def _scroll(widget: QWidget) -> QScrollArea:
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setWidget(widget)
    return sa


def _real_home() -> Path:
    """
    Return the actual user's home directory even when running under sudo.
    Under sudo, HOME and Path.home() both resolve to /root.
    SUDO_USER contains the original username, so we use that instead.
    """
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        try:
            import pwd
            return Path(pwd.getpwnam(sudo_user).pw_dir)
        except Exception:
            pass
    for env_var in ("HOME", "XDG_CONFIG_HOME"):
        val = os.environ.get(env_var)
        if val and not val.startswith("/root"):
            p = Path(val)
            if env_var == "XDG_CONFIG_HOME":
                p = p.parent   # XDG_CONFIG_HOME is typically ~/.config
            if p.exists():
                return p
    return Path.home()


def _real_desktop() -> Path:
    """Return the actual user's Desktop folder, falling back to home."""
    home = _real_home()
    # Try XDG user dirs config
    xdg_config = home / ".config" / "user-dirs.dirs"
    if xdg_config.exists():
        try:
            for line in xdg_config.read_text().splitlines():
                if line.startswith("XDG_DESKTOP_DIR"):
                    val = line.split("=", 1)[1].strip().strip('"')
                    # $HOME is literal in the file
                    val = val.replace("$HOME", str(home))
                    p = Path(val)
                    if p.exists():
                        return p
        except Exception:
            pass
    # Common fallback
    desktop = home / "Desktop"
    return desktop if desktop.exists() else home


def _is_admin() -> bool:
    """Return True if the process has Administrator / root privileges."""
    try:
        if sys.platform == "win32":
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def _npcap_available() -> bool:
    """Return True if Npcap (or WinPcap) is installed on Windows."""
    if sys.platform != "win32":
        return True   # irrelevant on Linux/mac
    # Check the Npcap service
    try:
        r = subprocess.run(
            ["sc", "query", "npcap"],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if r.returncode == 0:
            return True
    except Exception:
        pass
    # Fallback: look for the DLL
    for p in [
        r"C:\Windows\System32\Npcap\wpcap.dll",
        r"C:\Windows\SysWOW64\Npcap\wpcap.dll",
        r"C:\Windows\System32\wpcap.dll",     # legacy WinPcap
    ]:
        if Path(p).exists():
            return True
    return False


# ===========================================================================
# Main window
# ===========================================================================
class ScanOfDeath(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self._ready = False
        self._thread: NmapThread | None = None
        self._npcap = True
        _log_startup("ScanOfDeath.__init__: base init complete")
        self.setWindowTitle(f"{APP_NAME} - {ORG_NAME}")
        self.setMinimumSize(640, 480)
        self.resize(1120, 820)
        self._command_edited = False
        _log_startup("ScanOfDeath.__init__: before setup_icon")
        self._setup_icon()
        _log_startup("ScanOfDeath.__init__: before build_ui")
        self._build_ui()
        _log_startup("ScanOfDeath.__init__: build_ui complete")
        self._npcap = _npcap_available()
        _log_startup(f"ScanOfDeath.__init__: npcap={self._npcap}")
        if sys.platform == "win32" and not self._npcap:
            self._apply_no_npcap_restrictions()
            _log_startup("ScanOfDeath.__init__: applied no-npcap restrictions")
        self._ready = True
        _log_startup("ScanOfDeath.__init__: before update_command")
        self._update_command()
        _log_startup("ScanOfDeath.__init__: complete")

    # ------------------------------------------------------------------
    # ICON
    # ------------------------------------------------------------------
    def _setup_icon(self) -> None:
        ico = resource_path("icon.ico")
        if Path(ico).exists():
            self.setWindowIcon(QIcon(ico))
        if sys.platform == "win32":
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    "DeathsHeadSoftware.ScanOfDeath.1"
                )
            except Exception:
                pass

    # ==================================================================
    # UI layout
    # ==================================================================
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ---- Target + Command Preview --------------------------------
        top = QWidget()
        tl = QVBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(4)

        # "Target:" text box
        tr = QHBoxLayout()
        tr.addWidget(QLabel("Target:"))
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText(
            "hostname / IP / CIDR / range - e.g. 192.168.1.0/24  scanme.nmap.org"
        )
        self.target_edit.textChanged.connect(self._reset_command_auto_update)
        self.target_edit.textChanged.connect(self._update_command)
        tr.addWidget(self.target_edit, 1)
        self.target_file_btn = QPushButton("From File (-iL)")
        self.target_file_btn.clicked.connect(self._browse_target_file)
        tr.addWidget(self.target_file_btn)
        tl.addLayout(tr)

        # "Command:" text box: ('cmd_edit' used next on line 1877)
        cr = QHBoxLayout()
        cr.addWidget(QLabel("Command:"))
        self.cmd_edit = QLineEdit()
        self.cmd_edit.setPlaceholderText("Generated command - edit to customize, then press Apply")
        self.cmd_edit.setReadOnly(False)
        self.cmd_edit.textChanged.connect(self._on_command_edited)
        cr.addWidget(self.cmd_edit, 1)
        self.apply_cmd_btn = QPushButton("Apply")
        self.apply_cmd_btn.setToolTip("Parse the command above and update all UI controls to match")
        self.apply_cmd_btn.clicked.connect(self._parse_command_to_ui)
        cr.addWidget(self.apply_cmd_btn)
        tl.addLayout(cr)

        # ---- Profile / Presets --------------------------------------
        # --------------------------------------------------------------
        pr2 = QHBoxLayout()
        pr2.addWidget(QLabel("Profile:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Select preset...",
            "Quick scan",
            "Stealth scan",
            "Vulnerability scan",
            "Discovery only",
        ])
        self.preset_combo.setMaximumWidth(220)
        pr2.addWidget(self.preset_combo)
        self.apply_preset_btn = QPushButton("Apply Preset")
        self.apply_preset_btn.clicked.connect(self._apply_selected_preset)
        pr2.addWidget(self.apply_preset_btn)
        self.save_profile_btn = QPushButton("Save Profile")
        self.save_profile_btn.clicked.connect(self._save_profile)
        pr2.addWidget(self.save_profile_btn)
        self.load_profile_btn = QPushButton("Load Profile")
        self.load_profile_btn.clicked.connect(self._load_profile)
        pr2.addWidget(self.load_profile_btn)
        pr2.addStretch()
        tl.addLayout(pr2)

        # ---- Privilege Bar -------------------------------------------
        # --------------------------------------------------------------
        pr = QHBoxLayout()
        self.priv_label = QLabel("WARNING: This scan requires elevated privileges")
        self.priv_label.setObjectName("privWarn")
        self.priv_label.setVisible(False)
        pr.addWidget(self.priv_label, 1)

        if sys.platform == "win32":
            self.elev_btn = QPushButton("Relaunch as Administrator")
            self.elev_btn.setVisible(False)
            self.elev_btn.clicked.connect(self._relaunch_admin)
            pr.addWidget(self.elev_btn)

        tl.addLayout(pr)

        root.addWidget(top)

        # ---- Splitter: Tabs | Output ---------------------------------
        # --------------------------------------------------------------
        splitter = QSplitter(Qt.Orientation.Vertical)

        self.tabs = QTabWidget()
        self._tab_scan_type()
        self._tab_host_discovery()
        self._tab_ports()
        self._tab_service_version()
        self._tab_scripts()
        self._tab_os_detection()
        self._tab_timing()
        self._tab_evasion()
        self._tab_output()
        self._tab_misc()
        self._tab_cheatsheet()      # New cheatsheet tab
        splitter.addWidget(self.tabs)

        # Output panel
        out_frame = QWidget()
        ol = QVBoxLayout(out_frame)
        ol.setContentsMargins(0, 0, 0, 0)
        ol.setSpacing(4)

        oh = QHBoxLayout()
        oh.addWidget(QLabel("[ SCAN OUTPUT ]"))
        oh.addStretch()
        clr = QPushButton("Clear")
        clr.clicked.connect(lambda: (self.output.clear(),
                                     self.progress.setValue(0),
                                     self.progress.setRange(0, 100),
                                     self.progress.setFormat("Idle")))
        oh.addWidget(clr)
        sav = QPushButton("Save Output")
        sav.clicked.connect(self._save_output)
        oh.addWidget(sav)
        ol.addLayout(oh)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("Idle")
        self.progress.setFixedHeight(16)
        ol.addWidget(self.progress)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Courier", 11))
        ol.addWidget(self.output)

        splitter.addWidget(out_frame)
        splitter.setSizes([500, 260])
        root.addWidget(splitter, 1)

        # ---- Scan / Stop Buttons -------------------------------------
        # --------------------------------------------------------------
        br = QHBoxLayout()
        br.addStretch()
        self.scan_btn = QPushButton("SCAN")
        self.scan_btn.setObjectName("scanBtn")
        self.scan_btn.clicked.connect(self._run_scan)
        br.addWidget(self.scan_btn)
        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_scan)
        br.addWidget(self.stop_btn)
        br.addStretch()
        root.addLayout(br)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready.")

        self._build_menu()

    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        mb = self.menuBar()
        fm = mb.addMenu("File")
        a = QAction("Save Output", self); a.triggered.connect(self._save_output); fm.addAction(a)
        fm.addSeparator()
        a = QAction("Exit", self); a.triggered.connect(self.close); fm.addAction(a)
        hm = mb.addMenu("Help")
        a = QAction("About", self); a.triggered.connect(self._about); hm.addAction(a)

    def closeEvent(self, event) -> None:
        if self._thread is not None and self._thread.isRunning():
            self._thread.stop()
            self._thread.wait(2000)
        event.accept()

    # ------------------------------------------------------------------

    def _apply_no_npcap_restrictions(self) -> None:
        """Grey out raw-socket options and default to -sT when Npcap is absent."""
        self._disable_raw_options("Requires Npcap - reinstall nmap from nmap.org")
        self.status.showMessage(
            "WARNING: Npcap not detected - raw-socket scans disabled. "
            "Reinstall nmap from nmap.org to unlock all scan types."
        )
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(600, self._warn_no_npcap)

    def _warn_no_npcap(self) -> None:
        QMessageBox.warning(
            self,
            "Npcap Not Found",
            "<b>Npcap is not installed.</b><br><br>"
            "Npcap is the packet-capture driver that nmap requires for raw-socket "
            "scans (SYN, UDP, OS detection, ICMP probes, etc.).<br><br>"
            "The easiest fix: <b>reinstall nmap using the official Windows installer</b> "
            "from <a href='https://nmap.org/download.html'>nmap.org</a> - "
            "it bundles and installs Npcap automatically.<br><br>"
            "Until then, only <b>TCP Connect (-sT)</b> is available."
        )

    # ------------------------------------------------------------------
    # Raw-socket option enable / disable helpers
    # ------------------------------------------------------------------
    _RAW_SCAN_FLAGS = {"-sS","-sA","-sW","-sM","-sU","-sN","-sF","-sX","-sY","-sZ","-sO"}

    def _disable_raw_options(self, reason: str) -> None:
        """Grey out every scan option that needs raw sockets."""
        for flag, rb in self._scan_radios.items():
            if flag in self._RAW_SCAN_FLAGS:
                rb.setEnabled(False)
                rb.setToolTip(reason)
        self._scan_radios["-sT"].setChecked(True)
        self._os_chk.setEnabled(False);  self._os_chk.setToolTip(reason)
        self._aggr_chk.setEnabled(False); self._aggr_chk.setToolTip(reason)
        for flag in ("-PE", "-PP", "-PM"):
            if flag in self._probe_chks:
                self._probe_chks[flag].setEnabled(False)
                self._probe_chks[flag].setToolTip(reason)

    def _restore_raw_options(self) -> None:
        """Re-enable raw-socket options (call only when both Npcap present
        and --unprivileged is not checked)."""
        if not self._npcap:
            return   # Npcap still absent - leave them disabled
        if self._unpriv_chk.isChecked():
            return   # --unprivileged still active - leave them disabled
        for flag, rb in self._scan_radios.items():
            rb.setEnabled(True)
            rb.setToolTip("")
        self._os_chk.setEnabled(True);  self._os_chk.setToolTip("")
        self._aggr_chk.setEnabled(True); self._aggr_chk.setToolTip("")
        for flag in ("-PE", "-PP", "-PM"):
            if flag in self._probe_chks:
                self._probe_chks[flag].setEnabled(True)
                self._probe_chks[flag].setToolTip("")

    def _on_spoof_ip_toggled(self, checked: bool) -> None:
        if checked:
            self._spoof_pn_chk.setEnabled(True)
            # Auto-check -Pn the first time -S is enabled, but don't
            # force it - the user can uncheck it manually afterwards.
            if not self._spoof_pn_chk.isChecked():
                self._spoof_pn_chk.setChecked(True)
        else:
            self._spoof_pn_chk.setEnabled(False)
            self._spoof_pn_chk.setChecked(False)
        self._update_command()

    def _on_unprivileged_toggled(self, checked: bool) -> None:
        if checked:
            # Mutually exclusive with --privileged
            self._priv_chk.blockSignals(True)
            self._priv_chk.setChecked(False)
            self._priv_chk.blockSignals(False)
            self._disable_raw_options(
                "--unprivileged is active: nmap will refuse raw-socket scans"
            )
            self.status.showMessage(
                "WARNING: --unprivileged active - raw-socket scans disabled. "
                "Uncheck it to restore them."
            )
        else:
            self._restore_raw_options()
            self.status.showMessage("Ready.")
        self._update_command()

    def _on_privileged_toggled(self, checked: bool) -> None:
        if checked:
            # Mutually exclusive with --unprivileged
            self._unpriv_chk.blockSignals(True)
            self._unpriv_chk.setChecked(False)
            self._unpriv_chk.blockSignals(False)
            self._restore_raw_options()
            if sys.platform == "win32" and not _is_admin():
                self.status.showMessage(
                    "WARNING: --privileged selected, but app is not elevated. "
                    "Use 'Relaunch as Administrator' for raw-socket scans."
                )
            else:
                self.status.showMessage("Ready.")
        else:
            if self._unpriv_chk.isChecked():
                self._disable_raw_options(
                    "--unprivileged is active: nmap will refuse raw-socket scans"
                )
                self.status.showMessage(
                    "WARNING: --unprivileged active - raw-socket scans disabled. "
                    "Uncheck it to restore them."
                )
            else:
                self._restore_raw_options()
                self.status.showMessage("Ready.")
        self._update_command()

    def _on_command_edited(self) -> None:
        """Called when user manually edits the command text box."""
        self._command_edited = True

    def _reset_command_auto_update(self) -> None:
        """Reset to automatic command generation mode.
        Called when any UI control changes, indicating user wants
        the command to be auto-generated again."""
        self._command_edited = False

    def _get_command_from_edit(self) -> list[str]:
        """Parse the command text box into a token list using shlex.
        Falls back to _build_command() if parsing fails."""
        text = self.cmd_edit.text().strip()
        if not text:
            return self._build_command()
        try:
            tokens = shlex.split(text)
            if not tokens:
                return self._build_command()
            # If user omitted 'nmap' at the start, prepend it
            if tokens[0] != "nmap":
                tokens = ["nmap"] + tokens
            return tokens
        except ValueError:
            return self._build_command()

    def _parse_command_to_ui(self) -> None:
        """Parse the command in the Command text box and update all
        UI controls to match.  This is the reverse of _build_command."""
        text = self.cmd_edit.text().strip()
        if not text:
            QMessageBox.information(self, "Apply Command", "Command box is empty.")
            return
        try:
            tokens = shlex.split(text)
        except ValueError as exc:
            QMessageBox.warning(self, "Parse Error", f"Could not parse command:\n{exc}")
            return

        if not tokens:
            QMessageBox.information(self, "Apply Command", "No tokens found.")
            return

        # Ensure 'nmap' prefix
        if tokens[0] != "nmap":
            tokens = ["nmap"] + tokens

        # ------------------------------------------------------------------
        # Reset everything to defaults first
        # ------------------------------------------------------------------
        self._ready = False   # suppress auto-update while we churn
        self.target_edit.setText("")
        self._scan_radios[""].setChecked(True)
        self._idle_chk.setChecked(False); self._idle_edit.setText("")
        self._ftp_chk.setChecked(False); self._ftp_edit.setText("")
        for chk in self._hd.values(): chk.setChecked(False)
        for chk in self._probe_chks.values(): chk.setChecked(False)
        for ed in self._probe_edits.values(): ed.setText("")
        self._dns_edit.setText("")
        self._ports_edit.setText("")
        self._excl_ports_edit.setText("")
        for chk in self._port_flags.values(): chk.setChecked(False)
        self._top_chk.setChecked(False); self._top_spin.setValue(100)
        self._ratio_chk.setChecked(False); self._ratio_spin.setValue(0.5)
        self._sv_chk.setChecked(False)
        self._sv_light_chk.setChecked(False)
        self._sv_all_chk.setChecked(False)
        self._sv_trace_chk.setChecked(False)
        self._sv_int_chk.setChecked(False); self._sv_int_spin.setValue(7)
        self._sc_chk.setChecked(False)
        self._script_edit.setText("")
        self._sargs_edit.setText("")
        self._sargs_file_edit.setText("")
        self._strace_chk.setChecked(False)
        self._supdatedb_chk.setChecked(False)
        self._stimeout_chk.setChecked(False); self._stimeout_edit.setText("")
        self._aggr_chk.setChecked(False)
        self._os_chk.setChecked(False)
        self._os_limit_chk.setChecked(False)
        self._os_guess_chk.setChecked(False)
        self._timing_radios[""].setChecked(True)
        for chk in self._t_chks.values(): chk.setChecked(False)
        for ed in self._t_edits.values(): ed.setText("")
        self._frag_chk.setChecked(False)
        self._frag2_chk.setChecked(False)
        self._mtu_chk.setChecked(False); self._mtu_spin.setValue(24)
        self._decoy_chk.setChecked(False); self._decoy_edit.setText("")
        self._spoof_ip_chk.setChecked(False); self._spoof_ip_edit.setText("")
        self._spoof_pn_chk.setChecked(False)
        self._iface_chk.setChecked(False); self._iface_edit.setText("")
        self._sp_chk.setChecked(False); self._sp_spin.setValue(53)
        self._prox_chk.setChecked(False); self._prox_edit.setText("")
        self._dl_chk.setChecked(False); self._dl_spin.setValue(25)
        self._ipo_chk.setChecked(False); self._ipo_edit.setText("")
        self._ttl_chk.setChecked(False); self._ttl_spin.setValue(64)
        self._smac_chk.setChecked(False); self._smac_edit.setText("")
        self._badsum_chk.setChecked(False)
        for chk in self._out_chks.values(): chk.setChecked(False)
        for ed in self._out_edits.values(): ed.setText("")
        self._oA_chk.setChecked(False); self._oA_edit.setText("")
        for chk in self._verb.values(): chk.setChecked(False)
        for chk in self._misc.values(): chk.setChecked(False)
        self._priv_chk.setChecked(False)
        self._unpriv_chk.setChecked(False)
        self._excl_hosts_edit.setText("")
        self._excl_file_edit.setText("")
        self._iL_edit.setText("")
        self._iR_chk.setChecked(False); self._iR_spin.setValue(100)

        # ------------------------------------------------------------------
        # Walk tokens and set UI state
        # ------------------------------------------------------------------
        i = 1  # skip 'nmap'
        targets: list[str] = []
        while i < len(tokens):
            tok = tokens[i]
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None

            # --- Scan type ---
            if tok in self._scan_radios:
                self._scan_radios[tok].setChecked(True)
            elif tok == "-sI" and nxt:
                self._idle_chk.setChecked(True); self._idle_edit.setText(nxt); i += 1
            elif tok == "-b" and nxt:
                self._ftp_chk.setChecked(True); self._ftp_edit.setText(nxt); i += 1

            # --- Host discovery ---
            elif tok in self._hd:
                self._hd[tok].setChecked(True)
            elif tok.startswith("-PS"):
                self._probe_chks["-PS"].setChecked(True)
                if len(tok) > 3: self._probe_edits["-PS"].setText(tok[3:])
            elif tok.startswith("-PA"):
                self._probe_chks["-PA"].setChecked(True)
                if len(tok) > 3: self._probe_edits["-PA"].setText(tok[3:])
            elif tok.startswith("-PU"):
                self._probe_chks["-PU"].setChecked(True)
                if len(tok) > 3: self._probe_edits["-PU"].setText(tok[3:])
            elif tok.startswith("-PY"):
                self._probe_chks["-PY"].setChecked(True)
                if len(tok) > 3: self._probe_edits["-PY"].setText(tok[3:])
            elif tok.startswith("-PO"):
                self._probe_chks["-PO"].setChecked(True)
                if len(tok) > 3: self._probe_edits["-PO"].setText(tok[3:])
            elif tok == "-PE": self._probe_chks["-PE"].setChecked(True)
            elif tok == "-PP": self._probe_chks["-PP"].setChecked(True)
            elif tok == "-PM": self._probe_chks["-PM"].setChecked(True)
            elif tok == "--dns-servers" and nxt:
                self._dns_edit.setText(nxt); i += 1

            # --- Ports ---
            elif tok == "-p" and nxt:
                self._ports_edit.setText(nxt); i += 1
            elif tok == "--exclude-ports" and nxt:
                self._excl_ports_edit.setText(nxt); i += 1
            elif tok in self._port_flags:
                self._port_flags[tok].setChecked(True)
            elif tok == "--top-ports" and nxt:
                self._top_chk.setChecked(True)
                try: self._top_spin.setValue(int(nxt))
                except ValueError: pass
                i += 1
            elif tok == "--port-ratio" and nxt:
                self._ratio_chk.setChecked(True)
                try: self._ratio_spin.setValue(float(nxt))
                except ValueError: pass
                i += 1

            # --- Service / Version ---
            elif tok == "-sV": self._sv_chk.setChecked(True)
            elif tok == "--version-light": self._sv_light_chk.setChecked(True)
            elif tok == "--version-all": self._sv_all_chk.setChecked(True)
            elif tok == "--version-trace": self._sv_trace_chk.setChecked(True)
            elif tok == "--version-intensity" and nxt:
                self._sv_int_chk.setChecked(True)
                try: self._sv_int_spin.setValue(int(nxt))
                except ValueError: pass
                i += 1

            # --- Scripts ---
            elif tok == "-sC": self._sc_chk.setChecked(True)
            elif tok == "--script" and nxt:
                self._script_edit.setText(nxt); i += 1
            elif tok == "--script-args" and nxt:
                self._sargs_edit.setText(nxt); i += 1
            elif tok == "--script-args-file" and nxt:
                self._sargs_file_edit.setText(nxt); i += 1
            elif tok == "--script-trace": self._strace_chk.setChecked(True)
            elif tok == "--script-updatedb": self._supdatedb_chk.setChecked(True)
            elif tok == "--script-timeout" and nxt:
                self._stimeout_chk.setChecked(True)
                self._stimeout_edit.setText(nxt); i += 1

            # --- OS / Aggressive ---
            elif tok == "-A": self._aggr_chk.setChecked(True)
            elif tok == "-O": self._os_chk.setChecked(True)
            elif tok == "--osscan-limit": self._os_limit_chk.setChecked(True)
            elif tok == "--osscan-guess": self._os_guess_chk.setChecked(True)

            # --- Timing ---
            elif tok in self._timing_radios:
                self._timing_radios[tok].setChecked(True)
            elif tok in self._t_chks and nxt:
                self._t_chks[tok].setChecked(True)
                self._t_edits[tok].setText(nxt); i += 1

            # --- Evasion ---
            elif tok == "-f": self._frag_chk.setChecked(True)
            elif tok == "-ff": self._frag2_chk.setChecked(True)
            elif tok == "--mtu" and nxt:
                self._mtu_chk.setChecked(True)
                try: self._mtu_spin.setValue(int(nxt))
                except ValueError: pass
                i += 1
            elif tok == "-D" and nxt:
                self._decoy_chk.setChecked(True)
                self._decoy_edit.setText(nxt); i += 1
            elif tok == "-S" and nxt:
                self._spoof_ip_chk.setChecked(True)
                self._spoof_ip_edit.setText(nxt); i += 1
            elif tok == "-Pn":
                self._spoof_pn_chk.setChecked(True)
                if "-Pn" not in self._hd:
                    pass  # -Pn is also a host-discovery flag, but we handle it below
                self._hd["-Pn"].setChecked(True)
            elif tok == "-e" and nxt:
                self._iface_chk.setChecked(True)
                self._iface_edit.setText(nxt); i += 1
            elif tok in ("-g", "--source-port") and nxt:
                self._sp_chk.setChecked(True)
                try: self._sp_spin.setValue(int(nxt))
                except ValueError: pass
                i += 1
            elif tok == "--proxies" and nxt:
                self._prox_chk.setChecked(True)
                self._prox_edit.setText(nxt); i += 1
            elif tok == "--data-length" and nxt:
                self._dl_chk.setChecked(True)
                try: self._dl_spin.setValue(int(nxt))
                except ValueError: pass
                i += 1
            elif tok == "--ip-options" and nxt:
                self._ipo_chk.setChecked(True)
                self._ipo_edit.setText(nxt); i += 1
            elif tok == "--ttl" and nxt:
                self._ttl_chk.setChecked(True)
                try: self._ttl_spin.setValue(int(nxt))
                except ValueError: pass
                i += 1
            elif tok == "--spoof-mac" and nxt:
                self._smac_chk.setChecked(True)
                self._smac_edit.setText(nxt); i += 1
            elif tok == "--badsum": self._badsum_chk.setChecked(True)

            # --- Output ---
            elif tok in self._out_chks and nxt:
                self._out_chks[tok].setChecked(True)
                self._out_edits[tok].setText(nxt); i += 1
            elif tok == "-oA" and nxt:
                self._oA_chk.setChecked(True)
                self._oA_edit.setText(nxt); i += 1
            elif tok in self._verb:
                self._verb[tok].setChecked(True)

            # --- Misc ---
            elif tok in self._misc:
                self._misc[tok].setChecked(True)
            elif tok == "--privileged": self._priv_chk.setChecked(True)
            elif tok == "--unprivileged": self._unpriv_chk.setChecked(True)
            elif tok == "--exclude" and nxt:
                self._excl_hosts_edit.setText(nxt); i += 1
            elif tok == "--excludefile" and nxt:
                self._excl_file_edit.setText(nxt); i += 1
            elif tok == "-iL" and nxt:
                self._iL_edit.setText(nxt); i += 1
            elif tok == "--iR" and nxt:
                self._iR_chk.setChecked(True)
                try: self._iR_spin.setValue(int(nxt))
                except ValueError: pass
                i += 1

            # --- Target (anything not starting with '-') ---
            elif not tok.startswith("-"):
                targets.append(tok)

            i += 1

        if targets:
            self.target_edit.setText(" ".join(targets))

        self._command_edited = False
        self._ready = True
        self._update_command()
        self.status.showMessage("Command applied to UI controls.")

    # ==================================================================
    # Tabs
    # ==================================================================

    # ---- Scan Type ---------------------------------------------------
    def _tab_scan_type(self) -> None:
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignmentFlag.AlignTop)

        grp = QGroupBox("Scan Technique (-s*)")
        g = QGridLayout(grp)
        self._scan_bg = QButtonGroup(self)
        entries = [
            ("-sS", "SYN Stealth (-sS)"),
            ("-sT", "TCP Connect (-sT)"),
            ("-sA", "ACK Scan (-sA)"),
            ("-sW", "Window Scan (-sW)"),
            ("-sM", "Maimon Scan (-sM)"),
            ("-sU", "UDP Scan (-sU)"),
            ("-sN", "TCP Null (-sN)"),
            ("-sF", "FIN Scan (-sF)"),
            ("-sX", "Xmas Scan (-sX)"),
            ("-sY", "SCTP INIT (-sY)"),
            ("-sZ", "COOKIE-ECHO (-sZ)"),
            ("-sO", "IP Protocol (-sO)"),
            ("",    "No technique (default)"),
        ]
        self._scan_radios: dict[str, QRadioButton] = {}
        for i, (flag, label) in enumerate(entries):
            rb = QRadioButton(label)
            rb.setProperty("flag", flag)
            rb.toggled.connect(self._reset_command_auto_update)
            rb.toggled.connect(self._update_command)
            self._scan_bg.addButton(rb)
            self._scan_radios[flag] = rb
            g.addWidget(rb, i // 2, i % 2)
        self._scan_radios[""].setChecked(True)
        l.addWidget(grp)

        # idle scan
        ig = QGroupBox("Idle Scan (-sI)"); il = QHBoxLayout(ig)
        self._idle_chk = QCheckBox("Enable"); self._idle_chk.toggled.connect(self._update_command)
        self._idle_edit = QLineEdit(); self._idle_edit.setPlaceholderText("zombie_host[:probe_port]")
        self._idle_edit.textChanged.connect(self._update_command)
        self._idle_edit.setEnabled(False); self._idle_chk.toggled.connect(self._idle_edit.setEnabled)
        il.addWidget(self._idle_chk); il.addWidget(self._idle_edit, 1); l.addWidget(ig)

        # ftp bounce
        fg = QGroupBox("FTP Bounce Scan (-b)"); fl = QHBoxLayout(fg)
        self._ftp_chk = QCheckBox("Enable"); self._ftp_chk.toggled.connect(self._update_command)
        self._ftp_edit = QLineEdit(); self._ftp_edit.setPlaceholderText("ftp_relay_host")
        self._ftp_edit.textChanged.connect(self._update_command)
        self._ftp_edit.setEnabled(False); self._ftp_chk.toggled.connect(self._ftp_edit.setEnabled)
        fl.addWidget(self._ftp_chk); fl.addWidget(self._ftp_edit, 1); l.addWidget(fg)

        l.addStretch()
        self.tabs.addTab(_scroll(w), "Scan Type")


    # ---- Host Discovery ----------------------------------------------
    def _tab_host_discovery(self) -> None:
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignmentFlag.AlignTop)

        g1 = QGroupBox("Discovery Flags"); grid = QGridLayout(g1)
        self._hd: dict[str, QCheckBox] = {}
        hd_flags = [
            ("-sL",  "List Scan - enumerate only (-sL)"),
            ("-sn",  "Ping Scan - no port scan (-sn)"),
            ("-Pn",  "Skip discovery - treat all as online (-Pn)"),
            ("-n",   "No DNS resolution (-n)"),
            ("-R",   "Always resolve DNS (-R)"),
            ("--traceroute", "Traceroute (--traceroute)"),
            ("--system-dns","Use system DNS resolver (--system-dns)"),
        ]
        for i, (flag, lbl) in enumerate(hd_flags):
            c = QCheckBox(lbl)
            c.toggled.connect(self._reset_command_auto_update)
            c.toggled.connect(self._update_command)
            self._hd[flag] = c; grid.addWidget(c, i // 2, i % 2)
        l.addWidget(g1)

        g2 = QGroupBox("Probe Techniques"); pg = QGridLayout(g2)
        self._probe_chks:  dict[str, QCheckBox] = {}
        self._probe_edits: dict[str, QLineEdit]  = {}
        probes = [
            ("-PS", "TCP SYN ping (-PS)",   "port(s) e.g. 22,80"),
            ("-PA", "TCP ACK ping (-PA)",   "port(s)"),
            ("-PU", "UDP ping (-PU)",       "port(s)"),
            ("-PY", "SCTP ping (-PY)",      "port(s)"),
            ("-PE", "ICMP echo (-PE)",      None),
            ("-PP", "ICMP timestamp (-PP)", None),
            ("-PM", "ICMP netmask (-PM)",   None),
            ("-PO", "IP proto ping (-PO)",  "protocols"),
        ]
        for i, item in enumerate(probes):
            flag, lbl = item[0], item[1]
            hint = item[2] if len(item) > 2 else None
            c = QCheckBox(lbl)
            c.toggled.connect(self._reset_command_auto_update)
            c.toggled.connect(self._update_command)
            self._probe_chks[flag] = c; pg.addWidget(c, i, 0)
            if hint:
                ed = QLineEdit(); ed.setPlaceholderText(hint)
                ed.setMaximumWidth(200)
                ed.textChanged.connect(self._reset_command_auto_update)
                ed.textChanged.connect(self._update_command)
                ed.setEnabled(False); c.toggled.connect(ed.setEnabled)
                self._probe_edits[flag] = ed; pg.addWidget(ed, i, 1)
        l.addWidget(g2)

        g3 = QGroupBox("DNS"); df = QFormLayout(g3)
        self._dns_edit = QLineEdit(); self._dns_edit.setPlaceholderText("server1,server2,...")
        self._dns_edit.textChanged.connect(self._reset_command_auto_update)
        self._dns_edit.textChanged.connect(self._update_command)
        df.addRow("--dns-servers:", self._dns_edit)
        l.addWidget(g3)

        l.addStretch()
        self.tabs.addTab(_scroll(w), "Host Discovery")


    # ---- Ports -------------------------------------------------------
    def _tab_ports(self) -> None:
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignmentFlag.AlignTop)

        g1 = QGroupBox("Port Specification"); f1 = QFormLayout(g1)
        self._ports_edit = QLineEdit()
        self._ports_edit.setPlaceholderText("22,80,443  /  1-1024  /  U:53,T:21-25,80")
        self._ports_edit.textChanged.connect(self._reset_command_auto_update)
        self._ports_edit.textChanged.connect(self._update_command)
        f1.addRow("-p (ports):", self._ports_edit)
        self._excl_ports_edit = QLineEdit()
        self._excl_ports_edit.setPlaceholderText("80,443")
        self._excl_ports_edit.textChanged.connect(self._reset_command_auto_update)
        self._excl_ports_edit.textChanged.connect(self._update_command)
        f1.addRow("--exclude-ports:", self._excl_ports_edit)
        l.addWidget(g1)

        g2 = QGroupBox("Port Flags"); g2g = QGridLayout(g2)
        self._port_flags: dict[str, QCheckBox] = {}
        for i, (flag, lbl) in enumerate([("-F", "Fast - top 100 ports (-F)"),
                                          ("-r", "Sequential port order (-r)")]):
            c = QCheckBox(lbl)
            c.toggled.connect(self._reset_command_auto_update)
            c.toggled.connect(self._update_command)
            self._port_flags[flag] = c; g2g.addWidget(c, 0, i)
        l.addWidget(g2)

        g3 = QGroupBox("Top Ports / Port Ratio"); f3 = QFormLayout(g3)

        self._top_chk  = QCheckBox("--top-ports")
        self._top_spin = QSpinBox(); self._top_spin.setRange(1, 65535); self._top_spin.setValue(100)
        self._top_spin.setEnabled(False)
        self._top_chk.toggled.connect(self._top_spin.setEnabled)
        self._top_chk.toggled.connect(self._reset_command_auto_update)
        self._top_chk.toggled.connect(self._update_command)
        self._top_spin.valueChanged.connect(self._reset_command_auto_update)
        self._top_spin.valueChanged.connect(self._update_command)
        r1 = QHBoxLayout(); r1.addWidget(self._top_chk); r1.addWidget(self._top_spin); r1.addStretch()
        f3.addRow("", r1)

        self._ratio_chk  = QCheckBox("--port-ratio")
        self._ratio_spin = QDoubleSpinBox()
        self._ratio_spin.setRange(0.0, 1.0); self._ratio_spin.setSingleStep(0.05)
        self._ratio_spin.setValue(0.5); self._ratio_spin.setEnabled(False)
        self._ratio_chk.toggled.connect(self._ratio_spin.setEnabled)
        self._ratio_chk.toggled.connect(self._reset_command_auto_update)
        self._ratio_chk.toggled.connect(self._update_command)
        self._ratio_spin.valueChanged.connect(self._reset_command_auto_update)
        self._ratio_spin.valueChanged.connect(self._update_command)
        r2 = QHBoxLayout(); r2.addWidget(self._ratio_chk); r2.addWidget(self._ratio_spin); r2.addStretch()
        f3.addRow("", r2)

        l.addWidget(g3)
        l.addStretch()
        self.tabs.addTab(_scroll(w), "Ports")


    # ---- Service / Version -------------------------------------------
    def _tab_service_version(self) -> None:
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignmentFlag.AlignTop)

        g = QGroupBox("Version Detection"); gg = QGridLayout(g)

        self._sv_chk       = QCheckBox("Enable Version Detection (-sV)")
        self._sv_light_chk = QCheckBox("--version-light  (intensity 2)")
        self._sv_all_chk   = QCheckBox("--version-all    (intensity 9)")
        self._sv_trace_chk = QCheckBox("--version-trace")
        for c in (self._sv_chk, self._sv_light_chk, self._sv_all_chk, self._sv_trace_chk):
            c.toggled.connect(self._reset_command_auto_update)
            c.toggled.connect(self._update_command)
        gg.addWidget(self._sv_chk,        0, 0, 1, 2)
        gg.addWidget(self._sv_light_chk,  1, 0)
        gg.addWidget(self._sv_all_chk,    1, 1)
        gg.addWidget(self._sv_trace_chk,  2, 0)

        self._sv_int_chk  = QCheckBox("--version-intensity")
        self._sv_int_spin = QSpinBox(); self._sv_int_spin.setRange(0, 9); self._sv_int_spin.setValue(7)
        self._sv_int_spin.setEnabled(False)
        self._sv_int_chk.toggled.connect(self._sv_int_spin.setEnabled)
        self._sv_int_chk.toggled.connect(self._reset_command_auto_update)
        self._sv_int_chk.toggled.connect(self._update_command)
        self._sv_int_spin.valueChanged.connect(self._reset_command_auto_update)
        self._sv_int_spin.valueChanged.connect(self._update_command)
        ir = QHBoxLayout(); ir.addWidget(self._sv_int_chk); ir.addWidget(self._sv_int_spin); ir.addStretch()
        gg.addLayout(ir, 3, 0, 1, 2)

        l.addWidget(g)
        l.addStretch()
        self.tabs.addTab(_scroll(w), "Service/Version")


    # ---- Scripts (NSE) -----------------------------------------------
    def _tab_scripts(self) -> None:
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignmentFlag.AlignTop)

        g = QGroupBox("Nmap Scripting Engine (NSE)"); f = QFormLayout(g)

        self._sc_chk = QCheckBox("Default scripts (-sC / --script=default)")
        self._sc_chk.toggled.connect(self._reset_command_auto_update)
        self._sc_chk.toggled.connect(self._update_command)
        f.addRow("", self._sc_chk)

        self._script_edit = QLineEdit()
        self._script_edit.setPlaceholderText("vuln,auth  /  http-title,ssl-cert")
        self._script_edit.textChanged.connect(self._reset_command_auto_update)
        self._script_edit.textChanged.connect(self._update_command)
        f.addRow("--script:", self._script_edit)

        self._sargs_edit = QLineEdit()
        self._sargs_edit.setPlaceholderText("user=foo,pass=bar")
        self._sargs_edit.textChanged.connect(self._reset_command_auto_update)
        self._sargs_edit.textChanged.connect(self._update_command)
        f.addRow("--script-args:", self._sargs_edit)

        self._sargs_file_edit = QLineEdit()
        self._sargs_file_edit.textChanged.connect(self._reset_command_auto_update)
        self._sargs_file_edit.textChanged.connect(self._update_command)
        sfr = QHBoxLayout()
        sfr.addWidget(self._sargs_file_edit)
        sb = QPushButton("Browse"); sb.clicked.connect(lambda: self._browse_to(self._sargs_file_edit))
        sfr.addWidget(sb)
        f.addRow("--script-args-file:", sfr)

        self._strace_chk    = QCheckBox("--script-trace")
        self._supdatedb_chk = QCheckBox("--script-updatedb")
        for c in (self._strace_chk, self._supdatedb_chk):
            c.toggled.connect(self._reset_command_auto_update)
            c.toggled.connect(self._update_command)
        f.addRow("", self._strace_chk)
        f.addRow("", self._supdatedb_chk)

        # Script timeout - critical for heavy categories like 'vuln'
        self._stimeout_chk  = QCheckBox("--script-timeout")
        self._stimeout_edit = QLineEdit()
        self._stimeout_edit.setPlaceholderText("e.g. 60s  /  5m  (recommended for 'vuln')")
        self._stimeout_edit.setEnabled(False)
        self._stimeout_chk.toggled.connect(self._stimeout_edit.setEnabled)
        self._stimeout_chk.toggled.connect(self._reset_command_auto_update)
        self._stimeout_chk.toggled.connect(self._update_command)
        self._stimeout_edit.textChanged.connect(self._reset_command_auto_update)
        self._stimeout_edit.textChanged.connect(self._update_command)
        str_ = QHBoxLayout()
        str_.addWidget(self._stimeout_chk)
        str_.addWidget(self._stimeout_edit, 1)
        f.addRow("", str_)

        tip = QLabel(
            "WARNING: Heavy script categories (vuln, auth) can hang indefinitely on hosts\n"
            "   that return non-standard error codes (e.g. Akamai, Cloudflare CDNs).\n"
            "   Always set --script-timeout and --host-timeout (Timing tab) for these."
        )
        tip.setStyleSheet("color: #cc6600; font-size: 11px;")
        f.addRow("", tip)

        l.addWidget(g)
        l.addStretch()
        self.tabs.addTab(_scroll(w), "Scripts (NSE)")


    # ---- OS Detection ------------------------------------------------
    def _tab_os_detection(self) -> None:
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignmentFlag.AlignTop)

        g = QGroupBox("OS Detection"); gg = QGridLayout(g)
        self._os_chk       = QCheckBox("Enable OS Detection (-O)")
        self._os_limit_chk = QCheckBox("--osscan-limit  (skip uncertain hosts)")
        self._os_guess_chk = QCheckBox("--osscan-guess  (aggressive guess)")
        for i, c in enumerate((self._os_chk, self._os_limit_chk, self._os_guess_chk)):
            c.toggled.connect(self._reset_command_auto_update)
            c.toggled.connect(self._update_command); gg.addWidget(c, i, 0)
        l.addWidget(g)

        ag = QGroupBox("Aggressive Mode"); al = QHBoxLayout(ag)
        self._aggr_chk = QCheckBox("-A  (OS + version + scripts + traceroute)")
        self._aggr_chk.toggled.connect(self._reset_command_auto_update)
        self._aggr_chk.toggled.connect(self._update_command)
        al.addWidget(self._aggr_chk); l.addWidget(ag)

        l.addStretch()
        self.tabs.addTab(_scroll(w), "OS Detection")


    # ---- Timing ------------------------------------------------------
    def _tab_timing(self) -> None:
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignmentFlag.AlignTop)

        tg = QGroupBox("Timing Template"); th = QHBoxLayout(tg)
        self._timing_bg = QButtonGroup(self)
        self._timing_radios: dict[str, QRadioButton] = {}
        for flag, lbl in [("-T0","T0\nParanoid"),("-T1","T1\nSneaky"),("-T2","T2\nPolite"),
                           ("-T3","T3\nNormal"),("-T4","T4\nAggressive"),("-T5","T5\nInsane"),
                           ("","None")]:
            rb = QRadioButton(lbl); rb.setProperty("flag", flag)
            rb.toggled.connect(self._reset_command_auto_update)
            rb.toggled.connect(self._update_command)
            self._timing_bg.addButton(rb); self._timing_radios[flag] = rb; th.addWidget(rb)
        self._timing_radios[""].setChecked(True)
        l.addWidget(tg)

        fg = QGroupBox("Fine-Grained Timing"); ff = QFormLayout(fg)
        self._t_chks:  dict[str, QCheckBox] = {}
        self._t_edits: dict[str, QLineEdit]  = {}
        fine = [
            ("--min-hostgroup",      "size"),
            ("--max-hostgroup",      "size"),
            ("--min-parallelism",    "probes"),
            ("--max-parallelism",    "probes"),
            ("--min-rtt-timeout",    "ms  e.g. 100ms"),
            ("--max-rtt-timeout",    "ms  e.g. 3000ms"),
            ("--initial-rtt-timeout","ms"),
            ("--max-retries",        "count"),
            ("--host-timeout",       "e.g. 5m  30s"),
            ("--scan-delay",         "e.g. 100ms"),
            ("--max-scan-delay",     "e.g. 1000ms"),
            ("--min-rate",           "packets/sec"),
            ("--max-rate",           "packets/sec"),
        ]
        for opt, ph in fine:
            c = QCheckBox(opt)
            c.toggled.connect(self._reset_command_auto_update)
            c.toggled.connect(self._update_command)
            ed = QLineEdit(); ed.setPlaceholderText(ph); ed.setMaximumWidth(180)
            ed.textChanged.connect(self._reset_command_auto_update)
            ed.textChanged.connect(self._update_command); ed.setEnabled(False)
            c.toggled.connect(ed.setEnabled)
            self._t_chks[opt] = c; self._t_edits[opt] = ed
            r = QHBoxLayout(); r.addWidget(c); r.addWidget(ed); r.addStretch()
            ff.addRow("", r)
        l.addWidget(fg)
        l.addStretch()
        self.tabs.addTab(_scroll(w), "Timing")


    # ---- Evasion / Spoofing ------------------------------------------
    def _tab_evasion(self) -> None:
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignmentFlag.AlignTop)

        g = QGroupBox("Firewall / IDS Evasion & Spoofing"); f = QFormLayout(g)

        # Fragmentation
        fr = QHBoxLayout()
        self._frag_chk  = QCheckBox("-f  (fragment packets)")
        self._frag2_chk = QCheckBox("-ff  (8-byte fragments)")
        for c in (self._frag_chk, self._frag2_chk):
            c.toggled.connect(self._reset_command_auto_update)
            c.toggled.connect(self._update_command)
        fr.addWidget(self._frag_chk); fr.addWidget(self._frag2_chk); fr.addStretch()
        f.addRow("Fragmentation:", fr)

        # MTU
        self._mtu_chk  = QCheckBox("--mtu")
        self._mtu_spin = QSpinBox(); self._mtu_spin.setRange(8, 1500)
        self._mtu_spin.setSingleStep(8); self._mtu_spin.setValue(24); self._mtu_spin.setEnabled(False)
        self._mtu_chk.toggled.connect(self._mtu_spin.setEnabled)
        self._mtu_chk.toggled.connect(self._reset_command_auto_update)
        self._mtu_chk.toggled.connect(self._update_command)
        self._mtu_spin.valueChanged.connect(self._reset_command_auto_update)
        self._mtu_spin.valueChanged.connect(self._update_command)
        mr = QHBoxLayout(); mr.addWidget(self._mtu_chk); mr.addWidget(self._mtu_spin); mr.addStretch()
        f.addRow("MTU:", mr)

        # Decoys
        self._decoy_chk  = QCheckBox("-D  (use decoys)")
        self._decoy_edit = QLineEdit(); self._decoy_edit.setPlaceholderText("decoy1,decoy2,ME,...")
        self._decoy_edit.setEnabled(False)
        self._decoy_chk.toggled.connect(self._decoy_edit.setEnabled)
        self._decoy_chk.toggled.connect(self._reset_command_auto_update)
        self._decoy_chk.toggled.connect(self._update_command)
        self._decoy_edit.textChanged.connect(self._reset_command_auto_update)
        self._decoy_edit.textChanged.connect(self._update_command)
        dr = QHBoxLayout(); dr.addWidget(self._decoy_chk); dr.addWidget(self._decoy_edit, 1)
        f.addRow("Decoys:", dr)

        # Spoof source IP
        self._spoof_ip_chk  = QCheckBox("-S  (spoof source IP)")
        self._spoof_ip_edit = QLineEdit(); self._spoof_ip_edit.setPlaceholderText("spoofed_IP")
        self._spoof_ip_edit.setEnabled(False)
        self._spoof_ip_chk.toggled.connect(self._spoof_ip_edit.setEnabled)
        self._spoof_ip_chk.toggled.connect(self._on_spoof_ip_toggled)
        self._spoof_ip_edit.textChanged.connect(self._reset_command_auto_update)
        self._spoof_ip_edit.textChanged.connect(self._update_command)
        # -Pn shortcut - essential when spoofing
        self._spoof_pn_chk = QCheckBox("-Pn  (required for spoofing)")
        self._spoof_pn_chk.setToolTip(
            "Skips host discovery so nmap doesn't send a ping from your real IP\n"
            "before the spoofed packets. Always enable this when using -S."
        )
        self._spoof_pn_chk.toggled.connect(self._reset_command_auto_update)
        self._spoof_pn_chk.toggled.connect(self._update_command)
        self._spoof_pn_chk.setEnabled(False)
        # Note: setEnabled for _spoof_pn_chk is handled inside _on_spoof_ip_toggled,
        # NOT via a signal connection - avoids state conflict during click processing.
        sr = QHBoxLayout()
        sr.addWidget(self._spoof_ip_chk)
        sr.addWidget(self._spoof_ip_edit, 1)
        sr.addWidget(self._spoof_pn_chk)
        f.addRow("Spoof Source IP:", sr)

        # Interface
        self._iface_chk  = QCheckBox("-e  (interface)")
        self._iface_edit = QLineEdit(); self._iface_edit.setPlaceholderText("eth0")
        self._iface_edit.setEnabled(False)
        self._iface_chk.toggled.connect(self._iface_edit.setEnabled)
        self._iface_chk.toggled.connect(self._reset_command_auto_update)
        self._iface_chk.toggled.connect(self._update_command)
        self._iface_edit.textChanged.connect(self._reset_command_auto_update)
        self._iface_edit.textChanged.connect(self._update_command)
        ir = QHBoxLayout(); ir.addWidget(self._iface_chk); ir.addWidget(self._iface_edit, 1)
        f.addRow("Interface:", ir)

        # Source port
        self._sp_chk  = QCheckBox("-g / --source-port")
        self._sp_spin = QSpinBox(); self._sp_spin.setRange(1, 65535); self._sp_spin.setValue(53)
        self._sp_spin.setEnabled(False)
        self._sp_chk.toggled.connect(self._sp_spin.setEnabled)
        self._sp_chk.toggled.connect(self._reset_command_auto_update)
        self._sp_chk.toggled.connect(self._update_command)
        self._sp_spin.valueChanged.connect(self._reset_command_auto_update)
        self._sp_spin.valueChanged.connect(self._update_command)
        spr = QHBoxLayout(); spr.addWidget(self._sp_chk); spr.addWidget(self._sp_spin); spr.addStretch()
        f.addRow("Source Port:", spr)

        # Proxies
        self._prox_chk  = QCheckBox("--proxies")
        self._prox_edit = QLineEdit(); self._prox_edit.setPlaceholderText("http://server:port,...")
        self._prox_edit.setEnabled(False)
        self._prox_chk.toggled.connect(self._prox_edit.setEnabled)
        self._prox_chk.toggled.connect(self._reset_command_auto_update)
        self._prox_chk.toggled.connect(self._update_command)
        self._prox_edit.textChanged.connect(self._reset_command_auto_update)
        self._prox_edit.textChanged.connect(self._update_command)
        pr = QHBoxLayout(); pr.addWidget(self._prox_chk); pr.addWidget(self._prox_edit, 1)
        f.addRow("Proxies:", pr)

        # Data length
        self._dl_chk  = QCheckBox("--data-length")
        self._dl_spin = QSpinBox(); self._dl_spin.setRange(1, 1400); self._dl_spin.setValue(25)
        self._dl_spin.setEnabled(False)
        self._dl_chk.toggled.connect(self._dl_spin.setEnabled)
        self._dl_chk.toggled.connect(self._reset_command_auto_update)
        self._dl_chk.toggled.connect(self._update_command)
        self._dl_spin.valueChanged.connect(self._reset_command_auto_update)
        self._dl_spin.valueChanged.connect(self._update_command)
        dlr = QHBoxLayout(); dlr.addWidget(self._dl_chk); dlr.addWidget(self._dl_spin); dlr.addStretch()
        f.addRow("Data Length:", dlr)

        # IP options
        self._ipo_chk  = QCheckBox("--ip-options")
        self._ipo_edit = QLineEdit(); self._ipo_edit.setPlaceholderText("options string e.g. R")
        self._ipo_edit.setEnabled(False)
        self._ipo_chk.toggled.connect(self._ipo_edit.setEnabled)
        self._ipo_chk.toggled.connect(self._reset_command_auto_update)
        self._ipo_chk.toggled.connect(self._update_command)
        self._ipo_edit.textChanged.connect(self._reset_command_auto_update)
        self._ipo_edit.textChanged.connect(self._update_command)
        ior = QHBoxLayout(); ior.addWidget(self._ipo_chk); ior.addWidget(self._ipo_edit, 1)
        f.addRow("IP Options:", ior)

        # TTL
        self._ttl_chk  = QCheckBox("--ttl")
        self._ttl_spin = QSpinBox(); self._ttl_spin.setRange(1, 255); self._ttl_spin.setValue(64)
        self._ttl_spin.setEnabled(False)
        self._ttl_chk.toggled.connect(self._ttl_spin.setEnabled)
        self._ttl_chk.toggled.connect(self._reset_command_auto_update)
        self._ttl_chk.toggled.connect(self._update_command)
        self._ttl_spin.valueChanged.connect(self._reset_command_auto_update)
        self._ttl_spin.valueChanged.connect(self._update_command)
        tr = QHBoxLayout(); tr.addWidget(self._ttl_chk); tr.addWidget(self._ttl_spin); tr.addStretch()
        f.addRow("TTL:", tr)

        # Spoof MAC
        self._smac_chk  = QCheckBox("--spoof-mac")
        self._smac_edit = QLineEdit(); self._smac_edit.setPlaceholderText("MAC / vendor / 0 (random)")
        self._smac_edit.setEnabled(False)
        self._smac_chk.toggled.connect(self._smac_edit.setEnabled)
        self._smac_chk.toggled.connect(self._reset_command_auto_update)
        self._smac_chk.toggled.connect(self._update_command)
        self._smac_edit.textChanged.connect(self._reset_command_auto_update)
        self._smac_edit.textChanged.connect(self._update_command)
        smr = QHBoxLayout(); smr.addWidget(self._smac_chk); smr.addWidget(self._smac_edit, 1)
        f.addRow("Spoof MAC:", smr)

        # Badsum
        self._badsum_chk = QCheckBox("--badsum  (send packets with bad checksums)")
        self._badsum_chk.toggled.connect(self._reset_command_auto_update)
        self._badsum_chk.toggled.connect(self._update_command)
        f.addRow("", self._badsum_chk)

        l.addWidget(g)
        l.addStretch()
        self.tabs.addTab(_scroll(w), "Evasion/Spoof")


    # ---- Output ------------------------------------------------------
    def _tab_output(self) -> None:
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignmentFlag.AlignTop)

        g1 = QGroupBox("Output Files"); f1 = QFormLayout(g1)
        self._out_chks:  dict[str, QCheckBox] = {}
        self._out_edits: dict[str, QLineEdit]  = {}

        # Show where relative paths will actually land
        self._out_dir_label = QLabel(f"Relative paths save to: {_real_desktop()}")
        self._out_dir_label.setStyleSheet("color: #00aa00; font-size: 11px;")
        f1.addRow("", self._out_dir_label)

        fmts = [
            ("-oN", "Normal (-oN)",        "output.txt"),
            ("-oX", "XML (-oX)",           "output.xml"),
            ("-oS", "Script-kiddie (-oS)", "output.txt"),
            ("-oG", "Greppable (-oG)",     "output.gnmap"),
        ]
        for flag, lbl, ph in fmts:
            c = QCheckBox(lbl)
            c.toggled.connect(self._reset_command_auto_update)
            c.toggled.connect(self._update_command)
            ed = QLineEdit(); ed.setPlaceholderText(ph)
            ed.textChanged.connect(self._reset_command_auto_update)
            ed.textChanged.connect(self._update_command); ed.setEnabled(False)
            c.toggled.connect(ed.setEnabled)
            btn = QPushButton("..."); btn.setMaximumWidth(30)
            btn.clicked.connect(lambda _, e=ed: self._save_file_to(e))
            r = QHBoxLayout(); r.addWidget(c); r.addWidget(ed, 1); r.addWidget(btn)
            self._out_chks[flag] = c; self._out_edits[flag] = ed; f1.addRow("", r)

        self._oA_chk  = QCheckBox("-oA  (all formats - give basename)")
        self._oA_edit = QLineEdit(); self._oA_edit.setPlaceholderText("scan_output")
        self._oA_edit.setEnabled(False)
        self._oA_chk.toggled.connect(self._oA_edit.setEnabled)
        self._oA_chk.toggled.connect(self._reset_command_auto_update)
        self._oA_chk.toggled.connect(self._update_command)
        self._oA_edit.textChanged.connect(self._reset_command_auto_update)
        self._oA_edit.textChanged.connect(self._update_command)
        ar = QHBoxLayout(); ar.addWidget(self._oA_chk); ar.addWidget(self._oA_edit, 1)
        f1.addRow("", ar)
        l.addWidget(g1)

        g2 = QGroupBox("Verbosity & Misc Output"); g2g = QGridLayout(g2)
        self._verb: dict[str, QCheckBox] = {}
        vopts = [
            ("-v",              "Verbose (-v)"),
            ("-vv",             "Very verbose (-vv)"),
            ("-d",              "Debug (-d)"),
            ("-dd",             "More debug (-dd)"),
            ("--reason",        "Show reason (--reason)"),
            ("--open",          "Open ports only (--open)"),
            ("--packet-trace",  "Packet trace (--packet-trace)"),
            ("--iflist",        "Print host interfaces (--iflist)"),
            ("--append-output", "Append to output files (--append-output)"),
            ("--webxml",        "Web-friendly XML (--webxml)"),
            ("--no-stylesheet", "No XML stylesheet (--no-stylesheet)"),
        ]
        for i, (flag, lbl) in enumerate(vopts):
            c = QCheckBox(lbl)
            c.toggled.connect(self._reset_command_auto_update)
            c.toggled.connect(self._update_command)
            self._verb[flag] = c; g2g.addWidget(c, i // 2, i % 2)
        l.addWidget(g2)

        l.addStretch()
        self.tabs.addTab(_scroll(w), "Output")


    # ---- Misc --------------------------------------------------------
    def _tab_misc(self) -> None:
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignmentFlag.AlignTop)

        g1 = QGroupBox("Miscellaneous Flags"); g1g = QGridLayout(g1)
        self._misc: dict[str, QCheckBox] = {}
        mopts = [
            ("-6",         "IPv6 scanning (-6)"),
            ("--send-eth", "Raw Ethernet layer (--send-eth)"),
            ("--send-ip",  "Raw IP layer (--send-ip)"),
        ]
        for i, (flag, lbl) in enumerate(mopts):
            c = QCheckBox(lbl)
            c.toggled.connect(self._reset_command_auto_update)
            c.toggled.connect(self._update_command)
            self._misc[flag] = c; g1g.addWidget(c, i // 2, i % 2)

        # --privileged / --unprivileged - mutually exclusive, with side-effects
        self._priv_chk   = QCheckBox("--privileged  (force assume root)")
        self._unpriv_chk = QCheckBox("--unprivileged  (force assume non-root)")
        self._priv_chk.setToolTip(
            "Tell nmap to act as if it has root/admin rights regardless of reality."
        )
        self._unpriv_chk.setToolTip(
            "Tell nmap to act as if it has NO root/admin rights.\n"
            "Incompatible with raw-socket scan types (-sS, -sU, -O, etc.)."
        )
        self._priv_chk.toggled.connect(self._on_privileged_toggled)
        self._unpriv_chk.toggled.connect(self._on_unprivileged_toggled)
        g1g.addWidget(self._priv_chk,   2, 0)
        g1g.addWidget(self._unpriv_chk, 2, 1)
        l.addWidget(g1)

        g2 = QGroupBox("Exclude Hosts"); f2 = QFormLayout(g2)
        self._excl_hosts_edit = QLineEdit()
        self._excl_hosts_edit.setPlaceholderText("host1,host2,network/mask,...")
        self._excl_hosts_edit.textChanged.connect(self._reset_command_auto_update)
        self._excl_hosts_edit.textChanged.connect(self._update_command)
        f2.addRow("--exclude:", self._excl_hosts_edit)

        self._excl_file_edit = QLineEdit()
        self._excl_file_edit.textChanged.connect(self._reset_command_auto_update)
        self._excl_file_edit.textChanged.connect(self._update_command)
        efb = QPushButton("Browse"); efb.clicked.connect(lambda: self._browse_to(self._excl_file_edit))
        efr = QHBoxLayout(); efr.addWidget(self._excl_file_edit); efr.addWidget(efb)
        f2.addRow("--excludefile:", efr)
        l.addWidget(g2)

        g3 = QGroupBox("Input / Random Targets"); f3 = QFormLayout(g3)
        self._iL_edit = QLineEdit()
        self._iL_edit.textChanged.connect(self._reset_command_auto_update)
        self._iL_edit.textChanged.connect(self._update_command)
        iLb = QPushButton("Browse"); iLb.clicked.connect(lambda: self._browse_to(self._iL_edit))
        iLr = QHBoxLayout(); iLr.addWidget(self._iL_edit); iLr.addWidget(iLb)
        f3.addRow("-iL (hosts file):", iLr)

        self._iR_chk  = QCheckBox("--iR  (choose random targets)")
        self._iR_spin = QSpinBox(); self._iR_spin.setRange(0, 1000000); self._iR_spin.setValue(100)
        self._iR_spin.setEnabled(False)
        self._iR_chk.toggled.connect(self._iR_spin.setEnabled)
        self._iR_chk.toggled.connect(self._reset_command_auto_update)
        self._iR_chk.toggled.connect(self._update_command)
        self._iR_spin.valueChanged.connect(self._reset_command_auto_update)
        self._iR_spin.valueChanged.connect(self._update_command)
        iRr = QHBoxLayout(); iRr.addWidget(self._iR_chk); iRr.addWidget(self._iR_spin); iRr.addStretch()
        f3.addRow("Random targets:", iRr)
        l.addWidget(g3)

        l.addStretch()
        self.tabs.addTab(_scroll(w), "Misc")


    # ---- Cheatsheet (NEW) --------------------------------------------------------
    def _tab_cheatsheet(self) -> None:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Button bar
        btn_bar = QHBoxLayout()
        self._cs_edit_btn = QPushButton("Edit")
        self._cs_edit_btn.setToolTip("Toggle edit mode for the cheatsheet")
        self._cs_edit_btn.clicked.connect(self._toggle_cheatsheet_edit)
        btn_bar.addWidget(self._cs_edit_btn)

        self._cs_reload_btn = QPushButton("Reload")
        self._cs_reload_btn.setToolTip("Reload cheatsheet from disk")
        self._cs_reload_btn.clicked.connect(self._reload_cheatsheet)
        btn_bar.addWidget(self._cs_reload_btn)

        self._cs_status_lbl = QLabel("View mode")
        self._cs_status_lbl.setStyleSheet("color: #888; font-size: 11px;")
        btn_bar.addWidget(self._cs_status_lbl)
        btn_bar.addStretch()
        l.addLayout(btn_bar)

        # View widget (rich HTML)
        self._cs_view = QTextEdit()
        self._cs_view.setReadOnly(True)
        _set_cheatsheet_content(self._cs_view)
        l.addWidget(self._cs_view)

        # Edit widget (plain markdown)
        self._cs_edit = QPlainTextEdit()
        self._cs_edit.setFont(QFont("Courier", 11))
        self._cs_edit.setPlainText(_load_cheatsheet_text())
        self._cs_edit.setVisible(False)
        l.addWidget(self._cs_edit)

        self._cs_edit_mode = False
        self.tabs.addTab(_scroll(w), "Cheatsheet")

    def _toggle_cheatsheet_edit(self) -> None:
        """Toggle between view and edit mode for the cheatsheet."""
        if not self._cs_edit_mode:
            # Switch to edit mode
            self._cs_edit_mode = True
            self._cs_edit_btn.setText("Save")
            self._cs_status_lbl.setText("Edit mode — changes will save to .Nmap_Cheatsheet.md")
            self._cs_status_lbl.setStyleSheet("color: #cc6600; font-size: 11px;")
            self._cs_view.setVisible(False)
            self._cs_edit.setVisible(True)
            self._cs_edit.setPlainText(_load_cheatsheet_text())
        else:
            # Save and switch back to view mode
            new_text = self._cs_edit.toPlainText()
            # Find the cheatsheet file path
            cs_path = None
            for candidate in [
                Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / ".Nmap_Cheatsheet.md",
                Path(__file__).resolve().parent.parent / ".Nmap_Cheatsheet.md",
            ]:
                if candidate.exists():
                    cs_path = candidate
                    break
            if cs_path is None:
                # Try to create next to the script
                cs_path = Path(__file__).resolve().parent.parent / ".Nmap_Cheatsheet.md"
            try:
                cs_path.write_text(new_text, encoding="utf-8")
                self.status.showMessage(f"Cheatsheet saved -> {cs_path}")
            except Exception as exc:
                QMessageBox.warning(self, "Save Cheatsheet", f"Could not save cheatsheet:\n{exc}")
                return

            self._cs_edit_mode = False
            self._cs_edit_btn.setText("Edit")
            self._cs_status_lbl.setText("View mode")
            self._cs_status_lbl.setStyleSheet("color: #888; font-size: 11px;")
            self._cs_edit.setVisible(False)
            self._cs_view.setVisible(True)
            _set_cheatsheet_content(self._cs_view)

    def _reload_cheatsheet(self) -> None:
        """Reload cheatsheet content from disk."""
        text = _load_cheatsheet_text()
        self._cs_view.setHtml("")
        _set_cheatsheet_content(self._cs_view)
        self._cs_edit.setPlainText(text)
        self.status.showMessage("Cheatsheet reloaded from disk.")

    # ---- PresetS --------------------------------------------------------
    # --------------------------------------------------------------------
    def _apply_selected_preset(self) -> None:
        name = self.preset_combo.currentText()
        if name == "Select preset...":
            QMessageBox.information(self, "Preset", "Please choose a preset before applying it.")
            return
        profile = self._preset_profiles().get(name)
        if not profile:
            QMessageBox.warning(self, "Preset", f"Unknown preset: {name}")
            return
        self._apply_profile_data(profile)
        self.status.showMessage(f"Applied preset: {name}")

    def _preset_profiles(self) -> dict[str, dict[str, Any]]:
        return {
            "Quick scan": {
                "scan_flag": "-sT",
                "top_chk": True,
                "top_spin": 100,
                "timing_flag": "-T4",
                "sv_chk": False,
                "os_chk": False,
                "aggr_chk": False,
                "sc_chk": False,
                "script": "",
                "sargs": "",
                "sargs_file": "",
                "excl_hosts": "",
                "excl_file": "",
                "iL": "",
                "iR": False,
                "iR_value": 100,
                "ports": "",
                "excl_ports": "",
            },
            "Stealth scan": {
                "scan_flag": "-sS",
                "timing_flag": "-T3",
                "top_chk": False,
                "sv_chk": False,
                "os_chk": False,
                "aggr_chk": False,
                "sc_chk": False,
                "script": "",
                "sargs": "",
                "sargs_file": "",
                "excl_hosts": "",
                "excl_file": "",
                "iL": "",
                "iR": False,
                "iR_value": 100,
                "ports": "",
                "excl_ports": "",
            },
            "Vulnerability scan": {
                "scan_flag": "-sT",
                "timing_flag": "-T4",
                "sv_chk": True,
                "sv_light_chk": False,
                "sv_all_chk": False,
                "sv_trace_chk": False,
                "sc_chk": True,
                "script": "vuln",
                "sargs": "",
                "sargs_file": "",
                "aitimeout_chk": False,
                "os_chk": False,
                "aggr_chk": False,
                "top_chk": False,
                "excl_hosts": "",
                "excl_file": "",
                "iL": "",
                "iR": False,
                "iR_value": 100,
                "ports": "",
                "excl_ports": "",
            },
            "Discovery only": {
                "scan_flag": "",
                "top_chk": False,
                "timing_flag": "-T4",
                "sv_chk": False,
                "os_chk": False,
                "aggr_chk": False,
                "sc_chk": False,
                "script": "",
                "sargs": "",
                "sargs_file": "",
                "excl_hosts": "",
                "excl_file": "",
                "iL": "",
                "iR": False,
                "iR_value": 100,
                "ports": "",
                "excl_ports": "",
                "hd": {
                    "-sn": True,
                    "-Pn": False,
                    "-n": False,
                    "-R": False,
                    "--traceroute": False,
                    "--system-dns": False,
                },
            },
        }

    def _select_scan_flag(self, flag: str) -> None:
        if flag == "-sS" and sys.platform == "win32" and not getattr(self, "_npcap", True):
            flag = "-sT"
        if flag in self._scan_radios:
            self._scan_radios[flag].setChecked(True)

    def _select_timing_flag(self, flag: str) -> None:
        if flag in self._timing_radios:
            self._timing_radios[flag].setChecked(True)

    def _collect_profile(self) -> dict[str, Any]:
        return {
            "target": self.target_edit.text(),
            "scan_flag": next((rb.property("flag") for rb in self._scan_bg.buttons() if rb.isChecked()), ""),
            "idle": self._idle_chk.isChecked(),
            "idle_edit": self._idle_edit.text(),
            "ftp": self._ftp_chk.isChecked(),
            "ftp_edit": self._ftp_edit.text(),
            "hd": {flag: chk.isChecked() for flag, chk in self._hd.items()},
            "probes": {
                flag: {
                    "checked": chk.isChecked(),
                    "value": self._probe_edits.get(flag).text() if self._probe_edits.get(flag) else "",
                }
                for flag, chk in self._probe_chks.items()
            },
            "dns": self._dns_edit.text(),
            "ports": self._ports_edit.text(),
            "exclude_ports": self._excl_ports_edit.text(),
            "port_flags": {flag: chk.isChecked() for flag, chk in self._port_flags.items()},
            "top_chk": self._top_chk.isChecked(),
            "top_spin": self._top_spin.value(),
            "ratio_chk": self._ratio_chk.isChecked(),
            "ratio_spin": self._ratio_spin.value(),
            "sv_chk": self._sv_chk.isChecked(),
            "sv_light_chk": self._sv_light_chk.isChecked(),
            "sv_all_chk": self._sv_all_chk.isChecked(),
            "sv_trace_chk": self._sv_trace_chk.isChecked(),
            "sv_int_chk": self._sv_int_chk.isChecked(),
            "sv_int_spin": self._sv_int_spin.value(),
            "sc_chk": self._sc_chk.isChecked(),
            "script": self._script_edit.text(),
            "sargs": self._sargs_edit.text(),
            "sargs_file": self._sargs_file_edit.text(),
            "strace_chk": self._strace_chk.isChecked(),
            "supdatedb_chk": self._supdatedb_chk.isChecked(),
            "stimeout_chk": self._stimeout_chk.isChecked(),
            "stimeout": self._stimeout_edit.text(),
            "aggr_chk": self._aggr_chk.isChecked(),
            "os_chk": self._os_chk.isChecked(),
            "os_limit_chk": self._os_limit_chk.isChecked(),
            "os_guess_chk": self._os_guess_chk.isChecked(),
            "timing_flag": next((rb.property("flag") for rb in self._timing_bg.buttons() if rb.isChecked()), ""),
            "timing_options": {opt: {"checked": chk.isChecked(), "value": self._t_edits[opt].text()} for opt, chk in self._t_chks.items()},
            "frag_chk": self._frag_chk.isChecked(),
            "frag2_chk": self._frag2_chk.isChecked(),
            "mtu_chk": self._mtu_chk.isChecked(),
            "mtu_spin": self._mtu_spin.value(),
            "decoy_chk": self._decoy_chk.isChecked(),
            "decoy_edit": self._decoy_edit.text(),
            "spoof_ip_chk": self._spoof_ip_chk.isChecked(),
            "spoof_ip_edit": self._spoof_ip_edit.text(),
            "spoof_pn_chk": self._spoof_pn_chk.isChecked(),
            "iface_chk": self._iface_chk.isChecked(),
            "iface_edit": self._iface_edit.text(),
            "sp_chk": self._sp_chk.isChecked(),
            "sp_spin": self._sp_spin.value(),
            "prox_chk": self._prox_chk.isChecked(),
            "prox_edit": self._prox_edit.text(),
            "dl_chk": self._dl_chk.isChecked(),
            "dl_spin": self._dl_spin.value(),
            "ipo_chk": self._ipo_chk.isChecked(),
            "ipo_edit": self._ipo_edit.text(),
            "ttl_chk": self._ttl_chk.isChecked(),
            "ttl_spin": self._ttl_spin.value(),
            "smac_chk": self._smac_chk.isChecked(),
            "smac_edit": self._smac_edit.text(),
            "badsum_chk": self._badsum_chk.isChecked(),
            "output_files": {flag: self._out_edits[flag].text() for flag, chk in self._out_chks.items()},
            "output_flags": {flag: chk.isChecked() for flag, chk in self._out_chks.items()},
            "oA_chk": self._oA_chk.isChecked(),
            "oA_edit": self._oA_edit.text(),
            "verb_flags": {flag: chk.isChecked() for flag, chk in self._verb.items()},
            "misc_flags": {flag: chk.isChecked() for flag, chk in self._misc.items()},
            "priv_chk": self._priv_chk.isChecked(),
            "unpriv_chk": self._unpriv_chk.isChecked(),
            "exclude_hosts": self._excl_hosts_edit.text(),
            "excludefile": self._excl_file_edit.text(),
            "iL": self._iL_edit.text(),
            "iR": self._iR_chk.isChecked(),
            "iR_value": self._iR_spin.value(),
        }

    def _apply_profile_data(self, profile: dict[str, Any]) -> None:
        self.target_edit.setText(profile.get("target", ""))
        self._select_scan_flag(profile.get("scan_flag", ""))
        self._idle_chk.setChecked(profile.get("idle", False))
        self._idle_edit.setText(profile.get("idle_edit", ""))
        self._ftp_chk.setChecked(profile.get("ftp", False))
        self._ftp_edit.setText(profile.get("ftp_edit", ""))
        for flag, chk in self._hd.items():
            chk.setChecked(profile.get("hd", {}).get(flag, False))
        for flag, chk in self._probe_chks.items():
            data = profile.get("probes", {}).get(flag, {})
            chk.setChecked(data.get("checked", False))
            if flag in self._probe_edits:
                self._probe_edits[flag].setText(data.get("value", ""))
        self._dns_edit.setText(profile.get("dns", ""))
        self._ports_edit.setText(profile.get("ports", ""))
        self._excl_ports_edit.setText(profile.get("exclude_ports", ""))
        for flag, chk in self._port_flags.items():
            chk.setChecked(profile.get("port_flags", {}).get(flag, False))
        self._top_chk.setChecked(profile.get("top_chk", False))
        self._top_spin.setValue(profile.get("top_spin", 100))
        self._ratio_chk.setChecked(profile.get("ratio_chk", False))
        self._ratio_spin.setValue(profile.get("ratio_spin", 0.5))
        self._sv_chk.setChecked(profile.get("sv_chk", False))
        self._sv_light_chk.setChecked(profile.get("sv_light_chk", False))
        self._sv_all_chk.setChecked(profile.get("sv_all_chk", False))
        self._sv_trace_chk.setChecked(profile.get("sv_trace_chk", False))
        self._sv_int_chk.setChecked(profile.get("sv_int_chk", False))
        self._sv_int_spin.setValue(profile.get("sv_int_spin", 7))
        self._sc_chk.setChecked(profile.get("sc_chk", False))
        self._script_edit.setText(profile.get("script", ""))
        self._sargs_edit.setText(profile.get("sargs", ""))
        self._sargs_file_edit.setText(profile.get("sargs_file", ""))
        self._strace_chk.setChecked(profile.get("strace_chk", False))
        self._supdatedb_chk.setChecked(profile.get("supdatedb_chk", False))
        self._stimeout_chk.setChecked(profile.get("stimeout_chk", False))
        self._stimeout_edit.setText(profile.get("stimeout", ""))
        self._aggr_chk.setChecked(profile.get("aggr_chk", False))
        self._os_chk.setChecked(profile.get("os_chk", False))
        self._os_limit_chk.setChecked(profile.get("os_limit_chk", False))
        self._os_guess_chk.setChecked(profile.get("os_guess_chk", False))
        self._select_timing_flag(profile.get("timing_flag", ""))
        for opt, chk in self._t_chks.items():
            data = profile.get("timing_options", {}).get(opt, {})
            chk.setChecked(data.get("checked", False))
            self._t_edits[opt].setText(data.get("value", ""))
        self._frag_chk.setChecked(profile.get("frag_chk", False))
        self._frag2_chk.setChecked(profile.get("frag2_chk", False))
        self._mtu_chk.setChecked(profile.get("mtu_chk", False))
        self._mtu_spin.setValue(profile.get("mtu_spin", 24))
        self._decoy_chk.setChecked(profile.get("decoy_chk", False))
        self._decoy_edit.setText(profile.get("decoy_edit", ""))
        self._spoof_ip_chk.setChecked(profile.get("spoof_ip_chk", False))
        self._spoof_ip_edit.setText(profile.get("spoof_ip_edit", ""))
        self._spoof_pn_chk.setChecked(profile.get("spoof_pn_chk", False))
        self._iface_chk.setChecked(profile.get("iface_chk", False))
        self._iface_edit.setText(profile.get("iface_edit", ""))
        self._sp_chk.setChecked(profile.get("sp_chk", False))
        self._sp_spin.setValue(profile.get("sp_spin", 53))
        self._prox_chk.setChecked(profile.get("prox_chk", False))
        self._prox_edit.setText(profile.get("prox_edit", ""))
        self._dl_chk.setChecked(profile.get("dl_chk", False))
        self._dl_spin.setValue(profile.get("dl_spin", 25))
        self._ipo_chk.setChecked(profile.get("ipo_chk", False))
        self._ipo_edit.setText(profile.get("ipo_edit", ""))
        self._ttl_chk.setChecked(profile.get("ttl_chk", False))
        self._ttl_spin.setValue(profile.get("ttl_spin", 64))
        self._smac_chk.setChecked(profile.get("smac_chk", False))
        self._smac_edit.setText(profile.get("smac_edit", ""))
        self._badsum_chk.setChecked(profile.get("badsum_chk", False))
        for flag, chk in self._out_chks.items():
            chk.setChecked(profile.get("output_flags", {}).get(flag, False))
            self._out_edits[flag].setText(profile.get("output_files", {}).get(flag, ""))
        self._oA_chk.setChecked(profile.get("oA_chk", False))
        self._oA_edit.setText(profile.get("oA_edit", ""))
        for flag, chk in self._verb.items():
            chk.setChecked(profile.get("verb_flags", {}).get(flag, False))
        for flag, chk in self._misc.items():
            chk.setChecked(profile.get("misc_flags", {}).get(flag, False))
        self._priv_chk.setChecked(profile.get("priv_chk", False))
        self._unpriv_chk.setChecked(profile.get("unpriv_chk", False))
        self._excl_hosts_edit.setText(profile.get("exclude_hosts", ""))
        self._excl_file_edit.setText(profile.get("excludefile", ""))
        self._iL_edit.setText(profile.get("iL", ""))
        self._iR_chk.setChecked(profile.get("iR", False))
        self._iR_spin.setValue(profile.get("iR_value", 100))

        if self._spoof_ip_chk.isChecked():
            self._on_spoof_ip_toggled(True)
        else:
            self._on_spoof_ip_toggled(False)

        if self._unpriv_chk.isChecked():
            self._on_unprivileged_toggled(True)
        elif self._priv_chk.isChecked():
            self._on_privileged_toggled(True)
        else:
            self._restore_raw_options()

        self._update_command()
    
    # Saving your profile
    def _save_profile(self) -> None:
        profile = self._collect_profile()
        p, _ = QFileDialog.getSaveFileName(
            self, "Save Profile",
            str(_real_desktop() / "scan_profile.json"),
            "JSON Files (*.json);;All Files (*)"
        )
        if not p:
            return
        try:
            Path(p).write_text(json.dumps(profile, indent=2), encoding="utf-8")
            self.status.showMessage(f"Profile saved -> {p}")
        except Exception as exc:
            QMessageBox.critical(self, "Save Profile", f"Failed to save profile:\n{exc}")

    def _load_profile(self) -> None:
        p, _ = QFileDialog.getOpenFileName(
            self, "Load Profile",
            str(_real_desktop()),
            "JSON Files (*.json);;All Files (*)"
        )
        if not p:
            return
        try:
            data = json.loads(Path(p).read_text(encoding="utf-8"))
            self._apply_profile_data(data)
            self.status.showMessage(f"Profile loaded -> {p}")
        except Exception as exc:
            QMessageBox.critical(self, "Load Profile", f"Failed to load profile:\n{exc}")

    # ==================================================================
    # Command builder
    # ==================================================================
    def _build_command(self) -> list[str]:
        c: list[str] = ["nmap"]

        # scan type
        for rb in self._scan_bg.buttons():
            if rb.isChecked():
                flag = rb.property("flag")
                if flag:
                    c.append(flag)
                break
        if self._idle_chk.isChecked() and self._idle_edit.text().strip():
            c += ["-sI", self._idle_edit.text().strip()]
        if self._ftp_chk.isChecked() and self._ftp_edit.text().strip():
            c += ["-b", self._ftp_edit.text().strip()]

        # host discovery
        for flag, chk in self._hd.items():
            if chk.isChecked(): c.append(flag)
        for flag, chk in self._probe_chks.items():
            if chk.isChecked():
                ed = self._probe_edits.get(flag)
                c.append(f"{flag}{ed.text().strip()}" if ed and ed.text().strip() else flag)
        if self._dns_edit.text().strip():
            c += ["--dns-servers", self._dns_edit.text().strip()]

        # ports
        if self._ports_edit.text().strip():
            c += ["-p", self._ports_edit.text().strip()]
        if self._excl_ports_edit.text().strip():
            c += ["--exclude-ports", self._excl_ports_edit.text().strip()]
        for flag, chk in self._port_flags.items():
            if chk.isChecked(): c.append(flag)
        if self._top_chk.isChecked():
            c += ["--top-ports", str(self._top_spin.value())]
        if self._ratio_chk.isChecked():
            c += ["--port-ratio", str(self._ratio_spin.value())]

        # service/version
        if self._sv_chk.isChecked():       c.append("-sV")
        if self._sv_light_chk.isChecked(): c.append("--version-light")
        if self._sv_all_chk.isChecked():   c.append("--version-all")
        if self._sv_trace_chk.isChecked(): c.append("--version-trace")
        if self._sv_int_chk.isChecked():
            c += ["--version-intensity", str(self._sv_int_spin.value())]

        # scripts
        if self._sc_chk.isChecked():      c.append("-sC")
        if self._script_edit.text().strip():
            c += ["--script", self._script_edit.text().strip()]
        if self._sargs_edit.text().strip():
            c += ["--script-args", self._sargs_edit.text().strip()]
        if self._sargs_file_edit.text().strip():
            c += ["--script-args-file", self._sargs_file_edit.text().strip()]
        if self._strace_chk.isChecked():    c.append("--script-trace")
        if self._supdatedb_chk.isChecked(): c.append("--script-updatedb")
        if self._stimeout_chk.isChecked() and self._stimeout_edit.text().strip():
            c += ["--script-timeout", self._stimeout_edit.text().strip()]

        # OS / aggressive
        if self._aggr_chk.isChecked():      c.append("-A")
        if self._os_chk.isChecked():        c.append("-O")
        if self._os_limit_chk.isChecked():  c.append("--osscan-limit")
        if self._os_guess_chk.isChecked():  c.append("--osscan-guess")

        # timing template
        for rb in self._timing_bg.buttons():
            if rb.isChecked():
                flag = rb.property("flag")
                if flag: c.append(flag)
                break
        for opt, chk in self._t_chks.items():
            if chk.isChecked() and self._t_edits[opt].text().strip():
                c += [opt, self._t_edits[opt].text().strip()]

        # evasion
        if self._frag_chk.isChecked():   c.append("-f")
        if self._frag2_chk.isChecked():  c.append("-ff")
        if self._mtu_chk.isChecked():    c += ["--mtu", str(self._mtu_spin.value())]
        if self._decoy_chk.isChecked() and self._decoy_edit.text().strip():
            c += ["-D", self._decoy_edit.text().strip()]
        if self._spoof_ip_chk.isChecked() and self._spoof_ip_edit.text().strip():
            c += ["-S", self._spoof_ip_edit.text().strip()]
        # Emit -Pn from the spoof shortcut only if the HD tab hasn't already added it
        if self._spoof_pn_chk.isChecked() and "-Pn" not in c:
            c.append("-Pn")
        if self._iface_chk.isChecked() and self._iface_edit.text().strip():
            c += ["-e", self._iface_edit.text().strip()]
        if self._sp_chk.isChecked():     c += ["-g", str(self._sp_spin.value())]
        if self._prox_chk.isChecked() and self._prox_edit.text().strip():
            c += ["--proxies", self._prox_edit.text().strip()]
        if self._dl_chk.isChecked():     c += ["--data-length", str(self._dl_spin.value())]
        if self._ipo_chk.isChecked() and self._ipo_edit.text().strip():
            c += ["--ip-options", self._ipo_edit.text().strip()]
        if self._ttl_chk.isChecked():    c += ["--ttl", str(self._ttl_spin.value())]
        if self._smac_chk.isChecked() and self._smac_edit.text().strip():
            c += ["--spoof-mac", self._smac_edit.text().strip()]
        if self._badsum_chk.isChecked(): c.append("--badsum")

        # output
        for flag, chk in self._out_chks.items():
            if chk.isChecked() and self._out_edits[flag].text().strip():
                c += [flag, self._out_edits[flag].text().strip()]
        if self._oA_chk.isChecked() and self._oA_edit.text().strip():
            c += ["-oA", self._oA_edit.text().strip()]
        for flag, chk in self._verb.items():
            if chk.isChecked(): c.append(flag)

        # misc
        for flag, chk in self._misc.items():
            if chk.isChecked(): c.append(flag)
        if self._priv_chk.isChecked():   c.append("--privileged")
        if self._unpriv_chk.isChecked(): c.append("--unprivileged")
        if self._excl_hosts_edit.text().strip():
            c += ["--exclude", self._excl_hosts_edit.text().strip()]
        if self._excl_file_edit.text().strip():
            c += ["--excludefile", self._excl_file_edit.text().strip()]
        if self._iL_edit.text().strip():
            c += ["-iL", self._iL_edit.text().strip()]
        if self._iR_chk.isChecked():
            c += ["--iR", str(self._iR_spin.value())]

        # target
        t = self.target_edit.text().strip()
        if t: c.append(t)

        return c

    # Scan options that require raw socket / root access
    _PRIV_FLAGS = {
        "-sS", "-sA", "-sW", "-sM", "-sU", "-sN", "-sF", "-sX",
        "-sY", "-sZ", "-sO", "-sI", "-O", "-A",
        "--traceroute", "-PE", "-PP", "-PM", "-PO",
        "-D", "-S", "--spoof-mac", "--ip-options", "--send-eth",
    }
    _PRIV_PREFIXES = ("-PS", "-PA", "-PU", "-PY", "-PO")

    def _needs_privileges(self, cmd: list[str]) -> bool:
        """Check if any flag in the command typically requires root/admin privileges."""
        return any(
            tok in self._PRIV_FLAGS or tok.startswith(self._PRIV_PREFIXES)
            for tok in cmd
        )

    def _update_command(self) -> None:
        if not getattr(self, "_ready", False):
            return
        cmd = self._build_command()
        if not self._command_edited:
            self.cmd_edit.setText(" ".join(cmd))
        flags = set(cmd)
        priv  = self._needs_privileges(cmd)
        npcap = getattr(self, "_npcap", True)

        # Crash-risk: -T5 + OS detection on Windows
        if sys.platform == "win32" and "-T5" in flags and ("-O" in flags or "-A" in flags):
            self.priv_label.setText(
                "WARNING: -T5 + OS detection crashes nmap on Windows - use -T4 instead"
            )
            self.priv_label.setVisible(True)
            if hasattr(self, "elev_btn"): self.elev_btn.setVisible(False)
            return

        if sys.platform == "win32" and not npcap and priv:
            self.priv_label.setText(
                "ERROR: Npcap not found - reinstall nmap from nmap.org to unlock raw-socket scans"
            )
            self.priv_label.setVisible(True)
            if hasattr(self, "elev_btn"): self.elev_btn.setVisible(False)
        elif priv:
            self.priv_label.setText("WARNING: This scan requires elevated privileges")
            self.priv_label.setVisible(True)
            if sys.platform == "win32":
                self.elev_btn.setVisible(not _is_admin())
            else:
                pass
        else:
            self.priv_label.setVisible(False)
            if sys.platform == "win32":
                if hasattr(self, "elev_btn"): self.elev_btn.setVisible(False)
            else:
                pass

    # ==================================================================
    # Scan actions
    # ==================================================================

    def _preflight_check(self, cmd: list[str]) -> bool:
        """
        Validate the command for known dangerous / contradictory combinations.
        Returns True if safe to proceed, False if the user should fix something.
        Each check may show a warning or ask for confirmation.
        """
        flags = set(cmd)
        warnings = []

        # -T5 + OS detection or aggressive mode crashes nmap on Windows
        if sys.platform == "win32" and "-T5" in flags:
            if "-O" in flags or "-A" in flags:
                warnings.append(
                    "<b>-T5 + OS detection (-O / -A) on Windows</b><br>"
                    "This combination frequently crashes nmap.exe on Windows "
                    "(exit code 0xC0000005 - access violation inside Npcap).<br>"
                    "<b>Recommendation: use -T4 instead of -T5.</b>"
                )

        # -T5 + --version-all floods the network and can also crash nmap on Windows
        if sys.platform == "win32" and "-T5" in flags and "--version-all" in flags:
            warnings.append(
                "<b>-T5 + --version-all on Windows</b><br>"
                "Insane timing with maximum version probes is known to destabilise "
                "nmap on Windows. Consider -T4 and --version-intensity 7."
            )

        # --unprivileged with raw-socket scans (shouldn't reach here, but belt-and-braces)
        if "--unprivileged" in flags and self._needs_privileges(cmd):
            warnings.append(
                "<b>--unprivileged conflicts with raw-socket scan options</b><br>"
                "nmap will refuse to run. Remove --unprivileged or switch to "
                "TCP Connect (-sT)."
            )

        # -sS / raw scans with --version-all is very slow - just inform
        if "--version-all" in flags and any(f in flags for f in ("-sU", "-sO")):
            warnings.append(
                "<b>--version-all + UDP/Protocol scan</b><br>"
                "This will send an enormous number of probes and may take a very "
                "long time. Consider --version-intensity 5 or lower."
            )

        # Heavy NSE script categories without timeouts - common cause of hung scans
        heavy_scripts = {"vuln", "auth", "exploit", "brute", "intrusive"}
        script_val = " ".join(cmd)
        uses_heavy = any(s in script_val for s in heavy_scripts)
        has_script_timeout = "--script-timeout" in flags
        has_host_timeout   = "--host-timeout" in flags
        if uses_heavy and not (has_script_timeout or has_host_timeout):
            warnings.append(
                "<b>Heavy NSE scripts without a timeout</b><br>"
                "Categories like <code>vuln</code>, <code>auth</code>, <code>brute</code> "
                "can hang indefinitely on CDN-hosted targets (Akamai, Cloudflare, Fastly) "
                "because these hosts return non-standard error codes that confuse scripts "
                "like <code>http-enum</code>, causing them to probe all 2000+ fingerprints "
                "forever.<br><br>"
                "<b>Recommended fix:</b> set <code>--script-timeout 60s</code> in the "
                "Scripts tab and <code>--host-timeout 10m</code> in the Timing tab."
            )

        # Spoofing source IP - check -e and -Pn independently
        if "-S" in flags:
            missing = []
            if "-e" not in flags:
                missing.append(
                    "<b>-e (interface) is missing</b><br>"
                    "nmap needs to know which interface to send packets on "
                    "when the source IP is spoofed. Add -e and specify your "
                    "real interface (e.g. eth0)."
                )
            if "-Pn" not in flags:
                missing.append(
                    "<b>-Pn is missing</b><br>"
                    "Without -Pn, nmap sends a discovery ping from your <i>real</i> "
                    "source IP before the spoofed scan packets go out. This reveals "
                    "your actual address and can break routing. Always add -Pn when "
                    "spoofing with -S."
                )
            warnings.extend(missing)

        if not warnings:
            return True

        msg = (
            "<b>Potential issues detected:</b><br><br>"
            + "<br><br>".join(f"WARNING: {w}" for w in warnings)
            + "<br><br>Proceed anyway?"
        )
        reply = QMessageBox.warning(
            self, "Pre-flight Check",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    # Run the scan
    def _run_scan(self) -> None:
        # Use the command exactly as shown in the Command text box.
        # This ensures WYSIWYG: what you see is what gets executed.
        cmd = self._get_command_from_edit()

        # Derive target / no-target-ok conditions from the parsed command
        flags = set(cmd)
        targets = [tok for tok in cmd if not tok.startswith("-") and tok != "nmap"]
        target = targets[-1] if targets else ""
        no_target_ok = (
            "--script-updatedb" in flags
            or "--iflist" in flags
            or "--iR" in flags
            or "-iL" in flags
        )
        if not target and not no_target_ok:
            QMessageBox.warning(self, "No Target", "Please specify a target before scanning.")
            return

        # Privilege handling
        if self._needs_privileges(cmd):
            if sys.platform == "win32" and not self._npcap:
                QMessageBox.critical(
                    self, "Npcap Required",
                    "This scan type requires Npcap.\n\n"
                    "Reinstall nmap using the official Windows installer from "
                    "nmap.org - it bundles Npcap automatically."
                )
                return
            if sys.platform == "win32" and not _is_admin():
                QMessageBox.warning(
                    self, "Administrator Required",
                    "This scan type requires Administrator privileges.\n\n"
                    "Click 'Relaunch as Administrator' or run the script from "
                    "an elevated command prompt.",
                )
                return
            elif sys.platform != "win32":
                pass

        # Pre-flight validation
        if not self._preflight_check(cmd):
            return

        # Resolve relative output file paths to absolute so nmap writes
        # them where the user expects regardless of launch directory.
        resolved = []
        output_flags = {"-oN", "-oX", "-oS", "-oG", "-oA"}
        i = 0
        while i < len(cmd):
            resolved.append(cmd[i])
            if cmd[i] in output_flags and i + 1 < len(cmd):
                i += 1
                p = Path(cmd[i])
                if not p.is_absolute():
                    p = _real_desktop() / p
                resolved.append(str(p))
            i += 1
        cmd = resolved

        # Auto-inject --stats-every to drive the progress bar.
        # Insert at position 1 (right after "nmap") so it can never
        # land adjacent to a filename or target and confuse nmap's parser.
        if "--stats-every" not in cmd:
            cmd = [cmd[0], "--stats-every", "2s"] + cmd[1:]

        self.output.clear()
        self._bind_err_warned    = False
        self._last_progress_pct  = -1.0
        self._last_progress_time = time.time()
        self._stuck_warned       = False
        self.progress.setRange(0, 0)          # indeterminate pulse until % arrives
        self.progress.setFormat("Starting...")
        # Show the EXACT command being run, with a clear header
        self.output.appendPlainText(
            f"{'='*70}\n"
            f"[*] EXECUTING COMMAND:\n"
            f"    {' '.join(cmd)}\n"
            f"{'='*70}"
        )
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status.showMessage("Scanning...")

        # Stuck-scan watchdog: fires every 30s, warns if progress frozen > 3 min
        if not hasattr(self, "_stuck_timer"):
            self._stuck_timer = QTimer(self)
            self._stuck_timer.setInterval(30_000)
            self._stuck_timer.timeout.connect(self._check_stuck)
        self._stuck_timer.start()

        self._thread = NmapThread(cmd)
        self._thread.output_ready.connect(self._append)
        self._thread.scan_finished.connect(self._done)
        self._thread.start()

    def _relaunch_admin(self) -> None:
        """Re-launch this script with UAC elevation (Windows only)."""
        try:
            import ctypes
            params = " ".join(f'"{a}"' for a in sys.argv)
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params, None, 1
            )
            if ret > 32:          # success
                QApplication.quit()
            else:
                QMessageBox.warning(self, "Elevation Failed",
                                    "Could not obtain Administrator privileges.")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _check_stuck(self) -> None:
        """Warn if scan progress hasn't moved in 3 minutes."""
        if self._stuck_warned:
            return
        if time.time() - self._last_progress_time >= 180:
            self._stuck_warned = True
            self.output.appendPlainText(
                "\n[!] STUCK SCAN WARNING - progress has not moved for 3+ minutes.\n"
                "    Most likely cause: an NSE script (commonly http-enum from the\n"
                "    'vuln' category) is probing a CDN host (Akamai, Cloudflare,\n"
                "    Fastly) that returns non-standard error codes, preventing the\n"
                "    script from establishing a baseline - so it tries all 2000+\n"
                "    fingerprints indefinitely.\n"
                "\n"
                "    Options:\n"
                "      1. Click STOP and re-run with --script-timeout 60s\n"
                "         and --host-timeout 10m (Timing tab).\n"
                "      2. Use targeted scripts instead of the full 'vuln' category,\n"
                "         e.g. --script ssl-cert,http-title,vulners\n"
                "      3. Exclude http-enum: --script 'vuln and not http-enum'\n"
            )
            self.status.showMessage("WARNING: Scan appears stuck - see output for details.")

    def _stop_scan(self) -> None:
        if self._thread: self._thread.stop()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("Stopped")
        self.status.showMessage("Stopping...")

    # Matches:  "About 12.34% done; ETC: 16:05 (0:02:13 remaining)"
    _RE_PROGRESS = re.compile(r'About\s+([\d.]+)%\s+done.*?(\d+:\d+:\d+)\s+remaining', re.IGNORECASE)
    # Matches:  "Completed SYN Stealth Scan at 16:05, 10.23s elapsed"
    _RE_COMPLETE = re.compile(r'^Completed .+ at .+elapsed', re.IGNORECASE)
    # Matches the -S bind failure error
    _RE_BIND_ERR = re.compile(r'mksock_bind_addr\(\).*Cannot assign requested address', re.IGNORECASE)

    def _append(self, line: str) -> None:
        self.output.appendPlainText(line)
        self.output.moveCursor(QTextCursor.MoveOperation.End)

        # Detect -S bind failure and explain it once per scan
        if not getattr(self, "_bind_err_warned", False) and self._RE_BIND_ERR.search(line):
            self._bind_err_warned = True
            self.output.appendPlainText(
                "\n[!] SPOOFING ERROR - 'Cannot assign requested address'\n"
                "    The IP you gave -S is not assigned to any local interface.\n"
                "\n"
                "    On Linux, nmap -S does NOT forge arbitrary source IPs.\n"
                "    The kernel requires the source address to belong to one\n"
                "    of your own interfaces before it will bind a socket to it.\n"
                "\n"
                "    Valid uses of -S on Linux:\n"
                "      - You have multiple NICs / IPs - pick which one to send from\n"
                "        e.g. -S 10.8.0.2 -e tun0  (use your VPN address)\n"
                "\n"
                "    For TRUE arbitrary source-IP spoofing on Linux use:\n"
                "      hping3 --spoof <fake_ip> -S -p 80 <target>\n"
                "      scapy  (craft raw IP packets with any source you like)\n"
            )
            return

        m = self._RE_PROGRESS.search(line)
        if m:
            pct = float(m.group(1))
            remaining = m.group(2)
            if self.progress.maximum() == 0:
                self.progress.setRange(0, 100)   # switch off indeterminate
            self.progress.setValue(int(pct))
            self.progress.setFormat(f"{pct:.1f}%  -  {remaining} remaining")
            # Reset stuck watchdog when percentage actually changes
            if pct != getattr(self, "_last_progress_pct", -1.0):
                self._last_progress_pct  = pct
                self._last_progress_time = time.time()
                self._stuck_warned       = False
            return

        if self._RE_COMPLETE.search(line):
            self.progress.setValue(self.progress.value())   # hold current value

    def _done(self, code: int) -> None:
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if hasattr(self, "_stuck_timer"):
            self._stuck_timer.stop()

        # Always land the bar at a known state
        self.progress.setRange(0, 100)

        # Decode well-known Windows SEH / nmap exit codes
        _win_crash_codes = {
            -1073741819: "nmap crashed (0xC0000005 - access violation).\n"
                         "Common cause: -T5 + OS detection (-O/-A) on Windows.\n"
                         "Try -T4 instead of -T5.",
            -1073741571: "nmap crashed (0xC00000FD - stack overflow).\n"
                         "Too many concurrent probes. Try lower parallelism or -T3.",
            -1073740791: "nmap crashed (0xC0000409 - heap corruption).\n"
                         "Try reducing scan intensity.",
        }
        if code == 0:
            msg = "Scan complete."
            self.progress.setValue(100)
            self.progress.setFormat("Complete")
        elif code == -1:
            msg = "Scan error - check output above."
            self.progress.setValue(0)
            self.progress.setFormat("Error")
        elif code in _win_crash_codes:
            msg = f"nmap crashed (exit {code})."
            self.output.appendPlainText(f"\n[!] {_win_crash_codes[code]}")
            self.progress.setValue(0)
            self.progress.setFormat("Crashed")
        else:
            msg = f"Finished (exit {code})."
            self.progress.setFormat(f"Exit {code}")

        self.status.showMessage(msg)
        self.output.appendPlainText(f"\n{'-'*70}\n[*] {msg}")

    # ==================================================================
    # File helpers
    # ==================================================================
    def _browse_target_file(self) -> None:
        p, _ = QFileDialog.getOpenFileName(self, "Select Target File",
                                           str(_real_desktop()), "Text Files (*.txt);;All Files (*)")
        if p: self.target_edit.setText(p); self._iL_edit.setText(p)

    def _browse_to(self, ed: QLineEdit) -> None:
        p, _ = QFileDialog.getOpenFileName(self, "Select File",
                                           str(_real_desktop()), "All Files (*)")
        if p: ed.setText(p)

    def _save_file_to(self, ed: QLineEdit) -> None:
        p, _ = QFileDialog.getSaveFileName(self, "Save As",
                                           str(_real_desktop()), "All Files (*)")
        if p: ed.setText(p)

    def _save_output(self) -> None:
        p, _ = QFileDialog.getSaveFileName(self, "Save Output",
                                           str(_real_desktop() / "scan_output.txt"),
                                           "Text Files (*.txt);;All Files (*)")
        if p:
            Path(p).write_text(self.output.toPlainText(), encoding="utf-8")
            self.status.showMessage(f"Saved -> {p}")

    def _about(self) -> None:
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<b>{APP_NAME}</b><br>{ORG_NAME}<br>Version {APP_VERSION}<br><br>"
            "Full-featured Nmap GUI frontend.<br>"
            "Requires <b>nmap</b> installed and in PATH.",
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    _log_startup("main: start")
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "DeathsHeadSoftware.ScanOfDeath.1"
            )
        except Exception:
            pass

    # Try to enable high-DPI support (may not exist on all PyQt6 versions)
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    _log_startup("main: QApplication created")
    app.setStyleSheet(DARK_STYLE)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)

    # ---- Splash Screen --------------------------
    splash = create_splash()
    if splash:
        splash.show()
        messages = [
            "Initializing main engine…",
            "Loading security modules…",
            "Probing local environment…",
            "Armed and ready."
        ]
        for msg in messages:
            splash.showMessage(
                msg,
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
                QColor(0, 204, 0), # Cyber Green
            )
            app.processEvents()
            time.sleep(0.2) # Brief pause so messages are readable

    _log_startup("main: creating window")

    win = ScanOfDeath()
    _log_startup("main: window created")
    win.show()
    _log_startup("main: window shown")
    if splash:
        splash.finish(win)
        _log_startup("main: splash finished")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
