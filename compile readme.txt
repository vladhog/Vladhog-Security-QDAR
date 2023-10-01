python -m nuitka --mingw64 --follow-imports --standalone --plugin-enable=pylint-warnings --show-memory --windows-disable-console --show-modules main.py
python -m nuitka --mingw64 --follow-imports --onefile --plugin-enable=pylint-warnings --show-memory --windows-disable-console --show-modules startup.py
python -m nuitka --mingw64 --follow-imports --standalone --plugin-enable=pylint-warnings --show-memory --enable-plugin=tk-inter --windows-disable-console --show-modules qdarc.py
