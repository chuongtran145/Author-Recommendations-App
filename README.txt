# Author Collaborator Finder (Desktop)

This is a desktop (Tkinter) version of your Streamlit app.

## How to run (no packaging)
1) Install Python 3.11+ on Windows.
2) Open Command Prompt in this folder.
3) Install deps:
   `python -m pip install -r requirements.txt`
4) Run:
   `python app_desktop.py`

## Build EXE (Windows)
1) Double-click `build_exe.bat`
   - It installs PyInstaller and builds a single-file EXE.
2) Find the EXE in the `dist` folder.

## Notes
- Default columns: authors (author list separated by ';'), mdate (year/date), journal (venue)
- Only rows with year <= split_year are used to construct the training graph.
- Candidates must share at least one valid common journal.
- Three weights JJ/AA/CN always sum to 1 (drag any slider; app renormalizes).
