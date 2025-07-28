@echo off

echo Installing requirements...
pip install -r requirements.txt

echo Running download_model.py...
python download_model.py

echo Running main.py...
python src\main.py

pause
