param(
    [int]$Port = 8080
)

if (-Not (Test-Path .venv)) {
    python -m venv .venv
}

.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

if (-Not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Arquivo .env criado. Edite antes de usar em produção."
}

$env:APP_PORT = "$Port"
python app/main.py
