$ErrorActionPreference = 'Stop'
$taskPython = if (Test-Path -LiteralPath '.venv/Scripts/python.exe') { (Resolve-Path -LiteralPath '.venv/Scripts/python.exe').Path } else { 'python' }
& $taskPython -m PyInstaller --noconfirm --onefile --windowed --name SyrianSegoe `
  --icon "src/logo.ico" --paths src --collect-all customtkinter `
  --add-data "src/engine.py;." --add-data "src/grid_sync_engine.py;." `
  --add-data "src/engine_italic.py;." --add-data "src/grid_sync_engine_italic.py;." `
  --add-data "src/glyph_policy.py;." `
  --add-data "src/SyrianSegoe_Banner.png;." --add-data "src/SyrianSegoe_Banner_Light.png;." `
  --add-data "src/logo.ico;." "src/app.py"
if ($LASTEXITCODE -ne 0) { throw 'GUI packaging failed' }
& $taskPython -m PyInstaller --noconfirm --onefile --name SyrianSegoe-Korean-Build --paths src "src/korean_builder.py"
if ($LASTEXITCODE -ne 0) { throw 'Build-only CLI packaging failed' }

& $taskPython -m PyInstaller --noconfirm --onefile --name SyrianSegoe-Korean-Install --paths src "src/font_transaction.py"
if ($LASTEXITCODE -ne 0) { throw "Korean installer packaging failed" }
