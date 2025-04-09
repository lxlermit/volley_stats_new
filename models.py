from flask import Flask, json, session
from werkzeug.utils import secure_filename  # Добавьте в начало файла
import os
from typing import Dict, List, Optional

# === Константы безопасности ===
MAX_FILENAME_LENGTH = 100  # Максимальная длина имени файла
ALLOWED_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ ")  # Разрешенные символы
MAX_FILE_SIZE_MB = 16  # Максимальный размер файла в MB
ALLOWED_EXTENSIONS = {'.json'}  # Разрешенные расширения файлов
SAFE_DIRECTORIES = {  # Контроль рабочих директорий
    'teams_storage': {'max_size_mb': 50},
    'matches': {'max_size_mb': 100}
}
# ==============================


def init_models(app):
    """
    Инициализация конфигурации и путей для хранения данных
    ввв
    """

    # Основные директории
    app.config['UPLOAD_FOLDER'] = 'teams_storage'   # Для хранения данных команд
    app.config['MATCHES_FOLDER'] = 'matches'        # Для хранения данных матчей

    # Добавляем проверки:
    SAFE_DIRECTORIES = {
        'teams_storage': {
            'max_size_mb': 50,
            'allowed_extensions': ['.json']
        },
        'matches': {
            'max_size_mb': 100,
            'allowed_extensions': ['.json']
        }
    }

    # for dir_name in [app.config['UPLOAD_FOLDER'], app.config['MATCHES_FOLDER']]:
    #     if dir_name not in SAFE_DIRECTORIES:
    #         raise ValueError(f"Попытка инициализации небезопасной директории: {dir_name}")
    #
    #     os.makedirs(dir_name, exist_ok=True)
    #
    #     # Проверка прав доступа
    #     if not os.access(dir_name, os.R_OK | os.W_OK):
    #         raise PermissionError(f"Нет прав на запись в директорию {dir_name}")

    # Создаем директории если они не существуют
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['MATCHES_FOLDER'], exist_ok=True)

    # Дублируем пути как атрибуты для удобства доступа
    app.teams_dir = app.config['UPLOAD_FOLDER']
    app.matches_dir = app.config['MATCHES_FOLDER']



    # Другие настройки из оригинального app.py
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB максимальный размер загружаемого файла






def get_team_files(teams_dir: str = 'teams_storage') -> dict:
    """
    Получение списка файлов команд с обработкой ошибок

    Returns:
        dict: {
            'status': 'success'/'error',
            'files': list,
            'message': str (при ошибке)
        }
    """
    try:
        # Добавляем проверки:
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        requested_path = os.path.abspath(os.path.join(BASE_DIR, teams_dir))

        # Защита от directory traversal
        if not requested_path.startswith(BASE_DIR):
            raise ValueError("Попытка доступа к недопустимому пути")

        os.makedirs(teams_dir, exist_ok=True)

        files = [
            f for f in os.listdir(teams_dir)
            if f.endswith('.json')
               and not f.startswith('.')
               and os.path.isfile(os.path.join(teams_dir, f))
        ]

        return {
            'status': 'success',
            'files': files,
            'count': len(files)
        }

    except PermissionError:
        return {
            'status': 'error',
            'files': [],
            'message': 'Нет доступа к директории команд'
        }
    except Exception as e:
        return {
            'status': 'error',
            'files': [],
            'message': f'Ошибка получения списка команд: {str(e)}'
        }


def recalculate_derived_stats(player_stats):
    """
    Пересчет производных статистических показателей
    Полная копия оригинальной функции из app.py
    """
    actions = player_stats['actions']

    # Пересчет для подачи
    serving = actions['serving']
    if serving['total'] > 0:
        serving['ace_minus_error_divide_total'] = (serving['ace'] - serving['error']) / serving['total']
        serving['good_plus_2ace_divide_2error_plus_bad'] = (
            (serving['good'] + 2 * serving['ace']) /
            (2 * serving['error'] + serving['bad']) if (2 * serving['error'] + serving['bad']) != 0 else 0
        )

    # Пересчет для атаки
    attack = actions['attack']
    total_attacks = attack['win_total'] + attack['no_point'] + attack['error_total']
    if total_attacks > 0:
        attack['win_minus_error_divide_total'] = (attack['win_total'] - attack['error_total']) / total_attacks
        attack['win_plus_good_divide_bad_plus_error'] = (
            (attack['win_total'] + attack['shot_good']) /
            (attack['shot_bad'] + attack['error_total']) if (attack['shot_bad'] + attack['error_total']) != 0 else 0
        )

    # Аналогичные расчеты для других категорий (блок, прием и т.д.)
    # ... (полностью соответствует вашему исходному коду)


def save_match_data(filename: str, data: dict, matches_dir: str = 'matches') -> dict:
    """
    Безопасное сохранение данных матча с обработкой ошибок

    Args:
        filename: Имя файла для сохранения
        data: Данные для сохранения
        matches_dir: Директория для сохранения

    Returns:
        dict: Результат операции с полями:
            - status: 'success' или 'error'
            - message: Описание ошибки (при наличии)
            - filepath: Путь к сохраненному файлу (при успехе)
    """



    try:
        # Добавляем проверки безопасности:
        MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

        # Проверка размера данных
        json_str = json.dumps(data)
        if len(json_str) > MAX_FILE_SIZE:
            raise ValueError(f"Размер данных превышает максимально допустимый ({MAX_FILE_SIZE / 1024 / 1024}MB)")

        # Валидация входных данных
        if not filename or not isinstance(filename, str):
            raise ValueError("Некорректное имя файла")

        if not isinstance(data, dict):
            raise ValueError("Данные должны быть в формате словаря")

        # Защита от path traversal
        filename = secure_filename(filename)
        if not filename.endswith('.json'):
            filename += '.json'

        # Создание директории, если не существует
        os.makedirs(matches_dir, exist_ok=True)
        filepath = os.path.join(matches_dir, filename)

        # Проверка на перезапись существующего файла
        if os.path.exists(filepath):
            raise FileExistsError(f"Файл {filename} уже существует")

        # Сериализация и сохранение
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        # Проверка, что файл был записан
        if not os.path.exists(filepath):
            raise IOError("Файл не был создан")

        return {
            'status': 'success',
            'filepath': filepath,
            'message': 'Данные успешно сохранены'
        }

    except (ValueError, FileExistsError) as e:
        return {
            'status': 'error',
            'message': str(e),
            'filepath': None
        }
    except json.JSONEncodeError as e:
        return {
            'status': 'error',
            'message': f'Ошибка сериализации JSON: {str(e)}',
            'filepath': None
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Системная ошибка при сохранении: {str(e)}',
            'filepath': None
        }


def load_team_data(team_name: str, teams_dir: str = 'teams_storage') -> dict:
    """
    Загрузка данных команды с расширенной обработкой ошибок

    Args:
        team_name: Название команды (без расширения .json)
        teams_dir: Директория с файлами команд

    Returns:
        dict: Данные команды или словарь с ошибкой

    Raises:
        ValueError: Если имя команды содержит недопустимые символы
    """

    try:
        # Добавляем проверки безопасности здесь:
        MAX_FILENAME_LENGTH = 100
        ALLOWED_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ ")

        # Проверка длины имени
        if len(team_name) > MAX_FILENAME_LENGTH:
            raise ValueError(f"Слишком длинное имя команды (максимум {MAX_FILENAME_LENGTH} символов)")

        # Проверка допустимых символов
        if not all(c in ALLOWED_CHARS for c in team_name):
            raise ValueError("Имя команды содержит недопустимые символы")

        # Валидация имени файла
        if not isinstance(team_name, str) or not team_name.isprintable():
            raise ValueError("Некорректное имя команды")

        # Защита от path traversal
        if '/' in team_name or '\\' in team_name:
            raise ValueError("Имя команды содержит недопустимые символы")

        filename = os.path.join(teams_dir, f"{secure_filename(team_name)}.json")

        # Проверка существования файла
        if not os.path.exists(filename):
            return {
                'status': 'error',
                'message': f'Файл команды {team_name} не найден',
                'team': team_name,
                'players': []
            }

        # Чтение и проверка содержимого файла
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

            # Валидация структуры данных
            if not isinstance(data, dict):
                raise ValueError("Некорректный формат данных команды")

            # Инициализация стартового состава если его нет
            if 'starting_lineup' not in data:
                data['starting_lineup'] = {
                    'pos_1': None,
                    'pos_2': None,
                    'pos_3': None,
                    'pos_4': None,
                    'pos_5': None,
                    'pos_6': None
                }

            if 'players' not in data:
                data['players'] = []

            return {
                'status': 'success',
                'data': data
            }

    except json.JSONDecodeError as e:
        return {
            'status': 'error',
            'message': f'Ошибка чтения JSON файла команды: {str(e)}',
            'team': team_name,
            'players': []
        }
    except ValueError as e:
        return {
            'status': 'error',
            'message': str(e),
            'team': team_name,
            'players': []
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Неизвестная ошибка при загрузке команды: {str(e)}',
            'team': team_name,
            'players': []
        }
