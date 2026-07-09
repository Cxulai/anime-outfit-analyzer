@echo off
echo === Building Anime Outfit Analyzer ===
pip install pyinstaller
pyinstaller --onefile --windowed ^
    --name "AnimeOutfitAnalyzer" ^
    --add-data "ui;ui" ^
    --add-data "workers;workers" ^
    --add-data "models;models" ^
    --add-data "data;data" ^
    --add-data "settings.py;." ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import ultralytics ^
    --hidden-import open_clip ^
    --hidden-import torch ^
    --hidden-import replicate ^
    --hidden-import PIL ^
    --hidden-import numpy ^
    --exclude-module matplotlib ^
    --exclude-module pandas ^
    main.py
echo === Done ===
pause
