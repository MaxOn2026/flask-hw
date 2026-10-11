from functools import wraps

from flask import request, jsonify
from flask_hw import app
from flask_hw.db import SessionLocal, Advertisement, Users


def get_current_user() -> Users | None:
    """Извлекает текущего пользователя по токену (заголовок X-User-Id)."""
    user_id = request.headers.get('X-User-Id')
    if user_id is None:
        return None
    with SessionLocal() as session:
        return session.get(Users, int(user_id))


def require_login(f):
    """Декоратор: требует авторизации (заголовок X-User-Id)."""

    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, current_user=user, **kwargs)

    return decorated


def require_owner(f):
    """Декоратор: требует, чтобы текущий пользователь был владельцем объявления."""

    @wraps(f)
    def decorated(*args, **kwargs):
        # Берём ad_id из URL-паттерна (Flask передаёт его в view_args)
        ad_id = kwargs.get('ad_id')
        if ad_id is None:
            return jsonify({"error": "Missing ad_id"}), 400
        user = get_current_user()
        if user is None:
            return jsonify({"error": "Unauthorized"}), 401
        with SessionLocal() as session:
            ad = session.get(Advertisement, ad_id)
            if ad is None:
                return jsonify({"error": "Advertisement not found"}), 404
            if ad.owner_id != user.id:
                return jsonify({"error": "Forbidden: not the owner"}), 403
        return f(*args, current_user=user, advertisement=ad, **kwargs)

    return decorated


@app.route('/')
def index() -> str:
    """Главная страница — заглушка."""
    return "Ad API is running"


# ---- Аутентификация ----


@app.route('/auth/register', methods=['POST'])
def register() -> tuple:
    """Регистрация нового пользователя."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not all([name, email, password]):
        return jsonify({"error": "Missing fields: name, email, password"}), 400

    with SessionLocal() as session:
        # Проверяем, не занят ли email
        existing = session.query(Users).filter(Users.email == email).first()
        if existing:
            return jsonify({"error": "Email already registered"}), 409

        user = Users(name=name, email=email)
        user.set_password(password)
        session.add(user)
        session.commit()
        session.refresh(user)
        return jsonify(user.to_dict()), 201


@app.route('/auth/login', methods=['POST'])
def login() -> tuple:
    """Вход пользователя. Возвращает X-User-Id в заголовке."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"error": "Missing fields: email, password"}), 400

    with SessionLocal() as session:
        user = session.query(Users).filter(Users.email == email).first()
        if user is None or not user.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401

        # Возвращаем ID пользователя — клиент использует его как токен
        return jsonify({"user_id": user.id}), 200


# ---- Объявления ----


@app.route('/advertisement', methods=['GET'])
def get_advertisements() -> tuple:
    """Получить все объявления."""
    with SessionLocal() as session:
        ads = session.query(Advertisement).all()
        return jsonify([ad.to_dict() for ad in ads]), 200


@app.route('/advertisement/<int:ad_id>', methods=['GET'])
def get_advertisement(ad_id: int) -> tuple:
    """Получить одно объявление по ID."""
    with SessionLocal() as session:
        ad = session.get(Advertisement, ad_id)
        if ad is None:
            return jsonify({"error": "Advertisement not found"}), 404
        return jsonify(ad.to_dict()), 200


@app.route('/advertisement', methods=['POST'])
@require_login
def create_advertisement(current_user: Users) -> tuple:
    """Создать новое объявление (только для авторизованных)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    title = data.get('title')
    description = data.get('description')

    if not all([title, description]):
        return jsonify({"error": "Missing required fields: title, description"}), 400

    with SessionLocal() as session:
        new_ad = Advertisement(
            title=title,
            description=description,
            owner_id=current_user.id,  # Владелец = текущий пользователь
        )
        session.add(new_ad)
        session.commit()
        session.refresh(new_ad)
        return jsonify(new_ad.to_dict()), 201


@app.route('/advertisement/<int:ad_id>', methods=['DELETE'])
@require_owner
def delete_advertisement(ad_id: int, current_user: Users, advertisement: Advertisement) -> tuple:
    """Удалить объявление (только владелец)."""
    with SessionLocal() as session:
        session.delete(advertisement)
        session.commit()
        return '', 204


if __name__ == '__main__':
    app.run()
