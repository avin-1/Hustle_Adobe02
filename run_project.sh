#!/bin/bash
echo "Installing requirements..."
pip3 install -r requirements.txt

echo "Running download_model.py..."
python3 download_model.py

echo "Running main.py..."
python3 src/main.py

### chmod +x run_project.sh
### ./run_project.sh
