rem --- SYNTAX --------------------------------
rem -------------------------------------------
::
::	pyinstaller --noconfirm --log-level=WARN ^
::		--onefile --nowindow ^
::		--add-data "splash.png;." ^
::		--add-data "icon.ico;." ^
::		--add-data ".Nmap_Cheatsheet.md;." ^
::		--add-binary="libfoo.so:lib" ^
::		--hidden-import=secret1 ^
::		--hidden-import=secret2 ^
::		--icon=..\MLNMFLCN.ICO ^
::		myscript.spec
::
rem ------------------------------------------

rem Method 1 — (PowerShell) Add hidden imports

::	pyinstaller --onefile --windowed --icon "icon.ico" ^
::		--hidden-import=PyQt6 ^
::		--hidden-import=PyQt6.QtCore ^
::		--hidden-import=PyQt6.QtGui ^
::		--hidden-import=PyQt6.QtWidgets ^
::		--add-data "splash.png;." ^
::		--add-data "icon.ico;." ^
::		scan_of_death.py

rem Method 2 — Including a "splash screen":

::	pyinstaller --onefile --windowed --icon "icon.ico" ^
::		--add-data "splash.png;." ^
::		--add-data "icon.ico;." ^
::		--collect-all PyQt6 ^
::		scan_of_death.py

rem Method 3 — Including a cheatsheet + collect-all: ('windowed' or 'console')

::	pyinstaller --onefile --console --icon "icon.ico" ^
::	pyinstaller --onefile --windowed --icon "icon.ico" ^
::		--add-data "splash.png;." ^
::		--add-data "icon.ico;." ^
::		--add-data ".Nmap_Cheatsheet.md;." ^
::		--collect-all PyQt6 ^
::		"scan_of_death.py"
::

rem Method 4 — Including cheatsheet but without collect-all
::pyinstaller --noconfirm --clean --onefile --windowed --icon "icon.ico" ^
pyinstaller --noconfirm --clean --onefile --console --icon "icon.ico" ^
	--add-data "splash.png;." ^
	--add-data "icon.ico;." ^
	--add-data ".Nmap_Cheatsheet.md;." ^
	"scan_of_death.py"