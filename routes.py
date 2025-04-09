from flask import render_template, request, redirect, url_for, session, flash, jsonify, abort, current_app
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename

from models import get_team_files, save_match_data, load_team_data

import logging

from datetime import timedelta

logging.basicConfig(level=logging.DEBUG)

# === Лимиты для запросов ===
MAX_TEAM_NAME_LENGTH = 50  # Максимальная длина имени команды
MAX_PLAYERS_PER_TEAM = 20  # Максимальное количество игроков
# ==========================


def init_routes(app):

    # Сохраняем ссылку на app для доступа в функциях
    global flask_app
    flask_app = app

    # Инициализация путей
    app.teams_dir = 'teams_storage'  # относительный путь к папке с волейбольными командами
    app.matches_dir = 'matches'  # относительный путь к папке с волейбольными матчами (внутри них статистика)

    # Создаем папки при их отсутствии
    os.makedirs(app.teams_dir, exist_ok=True)
    os.makedirs(app.matches_dir, exist_ok=True)

    @app.route('/')
    def index():
        try:
            # Получим список файлов - созданных пользователем команд из папки app.teams_dir(teams_storage)
            team_files = [f.replace('.json', '') for f in os.listdir(app.teams_dir) if f.endswith('.json')]  # = ['ekran', 'tagila', 'new']
            return render_template('index.html', teams=team_files)
        except Exception as e:
            flash(f'Ошибка загрузки команд: {str(e)}', 'error')
            return render_template('index.html', teams=[])

    @app.route('/live_stats')
    def live_stats():
        if 'match_data' not in session:
            flash('Сначала настройте параметры матча', 'error')
            return redirect(url_for('match'))

        # logging.debug(f"--------------- session =  {session}")
        # logging.debug(f"--------------- session['current_match_file'] =  {session['current_match_file']}")
        # logging.debug(f"--------------- session['match_data'] =  {session['match_data']}")
        # logging.debug(f"--------------- flask_app.config =  {flask_app.config}")
        # logging.debug(f"--------------- flask_app.config['MATCHES_FOLDER'] =  {flask_app.config['MATCHES_FOLDER']}")

        # Путь к файлу со статистикой текущего матча
        # app.matches_dir_file = app.matches_dir + '/' + session['current_match_file']        # matches/ekran_2025_04_07__09_43_Соперник.json
        # logging.debug(f"--------------- app.matches_dir_file =  {app.matches_dir_file}")
        # session['matches_dir_file'] = app.matches_dir_file

        team_name = session['match_data']['our_team']           # Название нашей команды
        filename = os.path.join(flask_app.config['UPLOAD_FOLDER'], f"{team_name}.json")
        # print(f'---63--- filename = {filename}')

        with open(filename, 'r', encoding='utf-8') as f:
            team_data = json.load(f)    # = {'team': 'ekran', 'players': [{'number': '1', 'last_name': 'Максимов', ...}, {'number': '2'... ]


        return render_template('live_stats.html',
                               team=team_data['players'],
                               match_data=session['match_data'],
                               players_data=team_data['players'],
                               team_data=team_data)



    @app.route('/teams_edit')
    def teams_edit():
        try:
            # Проверяем существование директории
            if not os.path.exists(app.teams_dir):
                os.makedirs(app.teams_dir)
                return render_template('teams_edit.html', teams=[])

            # Получаем список файлов команд
            team_files = [f for f in os.listdir(app.teams_dir)
                          if f.endswith('.json') and os.path.isfile(os.path.join(app.teams_dir, f))]

            list_teams_info = []

            for filename in team_files:
                try:
                    with open(os.path.join(app.teams_dir, filename), 'r', encoding='utf-8') as f:
                        team_data = json.load(f)
                        list_teams_info.append({
                            'name': team_data.get('team', filename[:-5]),
                            'filename': filename,
                            'player_count': len(team_data.get('players', []))
                        })
                except json.JSONDecodeError:
                    continue  # Пропускаем битые JSON-файлы

            # list_teams_info =
            # [{'name': 'ekran', 'filename': 'ekran.json', 'player_count': 17},
            #  {'name': 'new', 'filename': 'new.json', 'player_count': 0},
            #  {'name': 'tagila', 'filename': 'tagila.json', 'player_count': 1}]

            return render_template('teams_edit.html', teams=list_teams_info)

        except Exception as e:
            flash(f'Ошибка загрузки команд: {str(e)}', 'error')
            return render_template('teams_edit.html', teams=[])

    @app.route('/team/<team_name>')
    def team_detail(team_name):
        # Загружаем данные с обработкой ошибок
        team_result = load_team_data(team_name, app.teams_dir)

        # Обработка ошибок
        if team_result['status'] != 'success':
            flash(team_result.get('message', 'Команда не найдена'), 'error')
            abort(404)

        team_data = team_result['data']

        # Инициализация стартового состава если отсутствует -
        if 'starting_lineup' not in team_data:
            team_data['starting_lineup'] = {f'pos_{i}': None for i in range(1, 7)}

        # Группировка игроков по амплуа
        players_by_role = {}
        for player in team_data.get('players', []):
            role = player.get('role', 'Без амплуа')
            if role not in players_by_role:
                players_by_role[role] = []
            players_by_role[role].append(player)

        return render_template('team_detail.html',
                               team=team_data,
                               players_by_role=players_by_role,
                               team_name=team_name)


    @app.route('/edit_team/<team_name>')
    def edit_existing_team(team_name):
        try:
            filename = os.path.join(app.teams_dir, f"{team_name}.json")

            if not os.path.exists(filename):
                flash(f'Команда "{team_name}" не найдена', 'error')
                return redirect(url_for('teams_edit'))

            with open(filename, 'r', encoding='utf-8') as f:
                team_data = json.load(f)

            # Инициализация стартового состава если отсутствует -
            if 'starting_lineup' not in team_data:
                team_data['starting_lineup'] = {f'pos_{i}': None for i in range(1, 7)}

            # Группируем игроков по номерам для удобства редактирования
            players_sorted = sorted(team_data['players'], key=lambda x: int(x['number']))

            return render_template('edit_team.html',
                                   players=players_sorted,
                                   team_name=team_name,
                                   starting_lineup=team_data['starting_lineup'])  # Передаем в шаблон


        except Exception as e:
            flash(f'Ошибка загрузки команды: {str(e)}', 'error')
            return redirect(url_for('teams_edit'))

    @app.route('/save_team', methods=['POST'])
    def save_team():
        try:
            team_name = request.form['team_name']
            if not team_name:
                flash('Название команды не может быть пустым', 'error')
                return redirect(url_for('teams_edit'))

            players = []
            used_numbers = set()

            # Собираем игроков из формы
            i = 1
            while f'number_{i}' in request.form:
                number = request.form[f'number_{i}']
                last_name = request.form[f'last_name_{i}']
                first_name = request.form[f'first_name_{i}']

                if not (number and last_name and first_name):
                    i += 1
                    continue  # Пропускаем пустые строки

                if number in used_numbers:
                    flash(f'Номер {number} уже используется!', 'error')
                    return redirect(url_for('edit_existing_team', team_name=team_name))

                used_numbers.add(number)
                players.append({
                    'number': number,
                    'last_name': last_name,
                    'first_name': first_name,
                    'role': request.form[f'role_{i}'],
                    'front_pos': request.form[f'front_pos_{i}'],
                    'back_pos': request.form[f'back_pos_{i}'],
                    'color': request.form.get(f'color_{i}', '#FF5733')
                })
                i += 1

            # Получаем стартовый состав из формы
            starting_lineup = {
                'pos_1': request.form.get('pos_1'),
                'pos_2': request.form.get('pos_2'),
                'pos_3': request.form.get('pos_3'),
                'pos_4': request.form.get('pos_4'),
                'pos_5': request.form.get('pos_5'),
                'pos_6': request.form.get('pos_6')
            }

            # print(f"--------------Стартовый состав:{starting_lineup}")  # Добавьте перед сохранением
            # print("Form data:", request.form)  # Логируем все данные формы
            # print("POSITIONS:", {
            #     'pos_1': request.form.get('pos_1'),
            #     'pos_2': request.form.get('pos_2'),
            #     'pos_3': request.form.get('pos_3'),
            #     'pos_4': request.form.get('pos_4'),
            #     'pos_5': request.form.get('pos_5'),
            #     'pos_6': request.form.get('pos_6')
            # })


            # Сохраняем обновлённую команду
            filename = os.path.join(app.teams_dir, f"{team_name}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'team': team_name,
                    'players': players,
                    'starting_lineup': starting_lineup  # Добавляем стартовый состав
                }, f, ensure_ascii=False, indent=4)

            flash(f'Команда "{team_name}" успешно обновлена!', 'success')
            return redirect(url_for('teams_edit'))

        except Exception as e:
            flash(f'Ошибка сохранения: {str(e)}', 'error')
            return redirect(url_for('teams_edit'))

    @app.route('/delete_team', methods=['POST'])
    def delete_team():
        try:
            team_name = request.form['team_name']
            filename = os.path.join(app.teams_dir, f"{team_name}.json")

            if os.path.exists(filename):
                os.remove(filename)
                flash(f'Команда "{team_name}" удалена', 'success')
            else:
                flash(f'Команда "{team_name}" не найдена', 'error')

            return redirect(url_for('teams_edit'))
        except Exception as e:
            flash(f'Ошибка удаления команды: {str(e)}', 'error')
            return redirect(url_for('teams_edit'))

    @app.route('/match', methods=['GET', 'POST'])
    # По кнопке - Начать матч - попадаем сюда
    def match():
        if request.method == 'POST':
            # Проверка обязательных полей
            if 'our_team' not in request.form or not request.form['our_team']:
                flash('Не выбрана наша команда!', 'error')
                return redirect(url_for('match'))

            # Сохраняем данные матча в сессию
            session['match_data'] = {
                'city': request.form.get('city', 'Санкт-Петербург'),
                'address': request.form.get('address', ''),
                'competition': request.form.get('competition', ''),
                'opponent': request.form.get('opponent', 'Команда соперника'),
                'our_team': request.form['our_team']
            }

            our_team_name = request.form['our_team']
            team_file = os.path.join(app.teams_dir, f"{our_team_name}.json")

            # Загружаем данные команды
            try:
                with open(team_file, 'r', encoding='utf-8') as f:
                    team_data = json.load(f)
            except Exception as e:
                flash(f'Ошибка загрузки команды: {str(e)}', 'error')
                return redirect(url_for('match'))

            # Формируем информацию о стартовом составе
            starting_lineup = {}
            if 'starting_lineup' in team_data:
                for pos, player_num in team_data['starting_lineup'].items():
                    if player_num:  # Если позиция заполнена
                        player = next((p for p in team_data['players'] if p['number'] == player_num), None)
                        if player:
                            starting_lineup[pos] = {
                                'number': player_num,
                                'name': f"{player['last_name']} {player['first_name'][0]}.",
                                'role': player.get('role', '')
                            }

            print(f'----- routes 307 ----- starting_lineup ----- = {starting_lineup}')
            # Сохраняем данные матча в сессию
            session['match_data'] = {
                'city': request.form.get('city', 'Санкт-Петербург'),
                'address': request.form.get('address', ''),
                'competition': request.form.get('competition', ''),
                'opponent': request.form.get('opponent', 'Команда соперника'),
                'our_team': request.form['our_team'],
                'starting_lineup': starting_lineup  # Добавляем стартовый состав
            }




            sorted_players = dict(sorted(
                {
                    int(p['number']): f"{p['last_name']} {p['first_name'][0]}."
                    for p in team_data['players']
                }.items()
            ))

            session['my_teams_bench'] = sorted_players        # {1: "Максимов Г.", 2:"Сампо С.", ... }
            # print(f"session['my_teams_bench'] =  {session['my_teams_bench']}")

            # Подготавливаем структуру для статистики игроков
            players_stats = {}
            for player in team_data['players']:
                players_stats[player['number']] = {
                    'player_info': player,
                    'actions': {
                        'serving': {'ace': 0, 'good': 0, 'bad': 0, 'error': 0, 'total': 0},
                        'attack': {'win_total': 0, 'shot_good': 0, 'shot_bad': 0, 'no_point': 0, 'error_total': 0},
                        'block': {'win': 0, 'cover': 0, 'error': 0, 'total': 0},
                        'receive': {'excellent': 0, 'good': 0, 'bad': 0, 'error': 0, 'total': 0},
                        'set': {'excellent': 0, 'good': 0, 'bad': 0, 'error': 0, 'total': 0},
                        'defence': {'excellent': 0, 'good': 0, 'bad': 0, 'error': 0, 'total': 0}
                    },
                    'time_played': 0,
                    'rotations': []
                }

            # Генерируем безопасное имя файла для матча
            now = datetime.now()
            opponent_team_name = request.form.get('opponent', 'Команда соперника')

            # Очищаем имя от недопустимых символов
            def sanitize_filename(name):
                keepchars = (' ', '.', '_')
                return "".join(c for c in name if c.isalnum() or c in keepchars).rstrip()

            safe_opponent = sanitize_filename(opponent_team_name)
            filename = (
                f"{our_team_name}_{now.strftime('%Y_%m_%d__%H_%M')}_"
                f"{safe_opponent}.json"
            ).replace(" ", "_")

            # Создаем директорию matches если её нет
            os.makedirs(app.matches_dir, exist_ok=True)

            # Формируем структуру данных матча
            match_stats = {
                "meta": {
                    "date": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "filename": filename,
                    "city": request.form.get('city', 'Санкт-Петербург'),
                    "address": request.form.get('address', ''),
                    "competition": request.form.get('competition', ''),
                    "our_team": our_team_name,
                    "opponent": opponent_team_name,
                    "status": "ongoing",
                    "team_lineup": [p['number'] for p in team_data['players']],
                    "starting_lineup": starting_lineup,  # Добавляем стартовый состав
                },
                "sets": {},
                "players_stats": players_stats,
                "match_events": [],
                "team_stats": {
                    "total_points": 0,
                    "attack_points": 0,
                    "block_points": 0,
                    "serve_points": 0,
                    "opponent_errors": 0,
                    "timeouts_used": 0,
                    "substitutions_used": 0
                }
            }

            # Сохраняем данные матча
            try:
                filepath = os.path.join(app.matches_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(match_stats, f, ensure_ascii=False, indent=4)
            except Exception as e:
                flash(f'Ошибка при создании файла матча: {str(e)}', 'error')
                return redirect(url_for('match'))

            session['current_match_file'] = filename
            return redirect(url_for('live_stats'))

        # GET запрос - отображаем форму
        teams_result = get_team_files(app.teams_dir)

        if teams_result['status'] != 'success':
            flash(f"Ошибка загрузки команд: {teams_result.get('message', 'Неизвестная ошибка')}", 'error')
            return redirect(url_for('index'))

        names_teams = [f.replace('.json', '') for f in teams_result['files']]       # = ['ekran', 'new', 'tagila']

        if not names_teams:
            flash('Сначала создайте команду!', 'error')
            return redirect(url_for('index'))

        return render_template('pre_game_setup.html',
                               teams=names_teams,                                   # = ['ekran', 'new', 'tagila']
                               default_city='Санкт-Петербург',
                               default_opponent='Команда соперника')

    @app.route('/stats')
    def stats():
        try:
            with open('match_data.json', 'r') as f:
                match_data = json.load(f)
            return render_template('stats.html', data=match_data)
        except FileNotFoundError:
            return render_template('stats.html', data=None)


    @app.route('/settings')
    def settings():
        return render_template('app_settings.html')


    @app.route('/add_team', methods=['GET', 'POST'])
    def add_team():
        if request.method == 'POST':
            team_name = request.form.get('team_name').strip()
            if not team_name:
                return render_template('add_team.html', error="Введите название команды")

            filename = f"{team_name}.json"
            if filename in get_team_files(app.teams_dir):
                return render_template('add_team.html', error="Команда с таким именем уже существует")

            new_team = {
                "team": team_name,
                "players": [],
                "starting_lineup": {
                    "pos_1": 0, "pos_2": 0, "pos_3": 0, "pos_4": 0, "pos_5": 0, "pos_6": 0
                }
            }

            with open(os.path.join(app.teams_dir, filename), 'w', encoding='utf-8') as f:
                json.dump(new_team, f, ensure_ascii=False, indent=4)

            return redirect(url_for('teams_edit'))

        return render_template('add_team.html')


    @app.route('/record_event', methods=['POST'])
    def record_event():
        try:
            data = request.json
            filename = session.get('current_match_file')
            if not filename:
                return jsonify({'status': 'error', 'message': 'No active match'}), 400

            filepath = os.path.join(app.matches_dir, filename)

            with open(filepath, 'r+', encoding='utf-8') as f:
                stats = json.load(f)
                event = {
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'type': data['event_type'],
                    'player': data['player_number'],
                    'details': data.get('details', {}),
                    'set': data['current_set'],
                    'score': data['score']
                }
                stats['match_events'].append(event)

                player_stats = stats['players_stats'].get(data['player_number'])
                if player_stats:
                    action_type = data['event_type'].split('_')[0]
                    quality = data['event_type'].split('_')[-1]

                    if action_type in player_stats['actions']:
                        if quality in player_stats['actions'][action_type]:
                            player_stats['actions'][action_type][quality] += 1
                        player_stats['actions'][action_type]['total'] += 1

                    recalculate_derived_stats(player_stats)

                f.seek(0)
                json.dump(stats, f, ensure_ascii=False, indent=4)
                f.truncate()

            return jsonify({'status': 'success'})

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    def recalculate_derived_stats(player_stats):
        actions = player_stats['actions']

        serving = actions['serving']
        if serving['total'] > 0:
            serving['ace_minus_error_divide_total'] = (serving['ace'] - serving['error']) / serving['total']
            serving['good_plus_2ace_divide_2error_plus_bad'] = (serving['good'] + 2 * serving['ace']) / (
                    2 * serving['error'] + serving['bad'])

        attack = actions['attack']
        total_attacks = attack['win_total'] + attack['no_point'] + attack['error_total']
        if total_attacks > 0:
            attack['win_minus_error_divide_total'] = (attack['win_total'] - attack['error_total']) / total_attacks
            attack['win_plus_good_divide_bad_plus_error'] = (attack['win_total'] + attack['shot_good']) / (
                    attack['shot_bad'] + attack['error_total'])

    @app.route('/end_match', methods=['POST'])
    def end_match():
        try:
            filename = session.get('current_match_file')
            if not filename:
                return redirect(url_for('index'))

            filepath = os.path.join(app.matches_dir, filename)

            with open(filepath, 'r+', encoding='utf-8') as f:
                stats = json.load(f)
                stats['meta']['status'] = 'completed'
                stats['meta']['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.seek(0)
                json.dump(stats, f, ensure_ascii=False, indent=4)
                f.truncate()

            session.pop('current_match_file', None)
            flash('Матч успешно завершен и статистика сохранена', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            flash(f'Ошибка при завершении матча: {str(e)}', 'error')
            return redirect(url_for('live_stats'))

    @app.route('/save_set', methods=['POST'])
    def save_set():
        try:
            logging.debug(f"Attempting to save to: {os.path.abspath(app.matches_dir)}")
            # Получаем данные из запроса
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'No data provided'}), 400

            filename = session.get('current_match_file')
            if not filename:
                return jsonify({'status': 'error', 'message': 'No active match'}), 400

            # Создаем директорию matches, если её нет
            os.makedirs(app.matches_dir, exist_ok=True)

            filepath = os.path.join(app.matches_dir, filename)

            # Читаем текущие данные матча
            with open(filepath, 'r', encoding='utf-8') as f:
                match_data = json.load(f)

            # Обновляем данные сета
            set_num = data.get('set_number')
            if not set_num:
                return jsonify({'status': 'error', 'message': 'Set number not provided'}), 400

            match_data['sets'][f"set_{set_num}"] = [
                data.get('result', {}).get('our', 0),
                data.get('result', {}).get('opponent', 0)
            ]

            # Если матч завершён
            if data.get('end_match'):
                match_data['meta']['status'] = 'completed'
                match_data['meta']['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session.pop('current_match_file', None)

            # Записываем обновлённые данные
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(match_data, f, ensure_ascii=False, indent=4)

            return jsonify({'status': 'success'})

        except json.JSONDecodeError as e:
            return jsonify({'status': 'error', 'message': f'JSON decode error: {str(e)}'}), 500
        except IOError as e:
            return jsonify({'status': 'error', 'message': f'File operation failed: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Unexpected error: {str(e)}'}), 500

    @app.route('/debug')
    def debug_info():
        def json_serializer(obj):
            """Кастомный сериализатор для не-JSON объектов"""
            if isinstance(obj, timedelta):
                return str(obj)  # Конвертируем timedelta в строку
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            return str(obj)  # Все остальное в строку

        # Собираем данные сессии
        session_data = dict(session)

        # Собираем данные app с обработкой несериализуемых объектов
        app_data = {
            'config': {
                k: json_serializer(v)
                for k, v in current_app.config.items()
                if not k.startswith('SECRET')
            },
            'extensions': list(current_app.extensions.keys()),
            'url_map': [str(rule) for rule in current_app.url_map.iter_rules()],
            'debug': current_app.debug
        }

        return jsonify({
            'session': session_data,
            'app': app_data
        })