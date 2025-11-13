# Author Collaborator Finder (Desktop)
## How to run
** Method 1
1) Install Python 3.11+ on Windows.
2) Open Command Prompt in this folder.
3) Run:
   `python -m pip install -r requirements.txt`
4) Run:
   `python app_desktop.py`

** Method 2
Double-click on 'run_desktop.bat'

** Method 3
1) Open Command Prompt in this folder.
2) Run:
   `pip install pyinstaller`
3) Run:
   `py -3.11 -m venv .venv`
   `call .venv\Scripts\activate.bat`
   `python -m pip install --upgrade pip`
   `python -m pip install -r requirements.txt pyinstaller`
4) Build file .exe:
   `pyinstaller --onefile --noconsole ^
     --distpath "%cd%\dist" --workpath "%cd%\build" --specpath "%cd%\build" ^
     app_desktop.py`
-> File .exe will place in 'dist' folder
