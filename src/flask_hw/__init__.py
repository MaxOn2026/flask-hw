from flask import Flask

app = Flask(__name__)


def main() -> None:
    """Точка входа для uv-скрипта."""
    print("Hello from flask-hw!")
