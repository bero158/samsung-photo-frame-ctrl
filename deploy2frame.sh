rsync -av -e ssh --exclude='*.venv' --exclude='*.pyc' --exclude "*.jpg" --exclude "__pycache__" --exclude ".git" --exclude ".vscode" --exclude "*.log" --exclude "config.py" /home/tom/data/git/samsung-frame/samsung-photo-frame-ctrl/samsung-photo-frame-ctrl pi@192.168.1.106:/home/pi/frame