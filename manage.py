#!/usr/bin/env python
import os, sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ansar_os.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django не найден. Активируй venv и установи зависимости: pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
