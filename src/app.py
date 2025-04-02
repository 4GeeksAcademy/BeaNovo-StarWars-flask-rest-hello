"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planets, characters, Favorites
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def get_user():
    data = db.session.scalars(db.select(User)).all()
    result = list(map(lambda item: item.serialize(),data))

    if result == []:
        return jsonify({"msg":"there are no users"}), 404

    response_body = {
        "results": result
    }

    return jsonify(response_body), 200


@app.route('/characters', methods=['GET'])
def get_all_characters():
    data = db.session.scalars(db.select(characters)).all()
    result = list(map(lambda item: item.serialize(),data))

    if result == []:
        return jsonify({"msg":"there are no humanoid records"}), 404

    response_body = {
        "results": result
    }

    return jsonify(response_body), 200

@app.route('/characters/<int:characters_id>', methods=['GET'])
def get_characters(characters_id):
    try:
        characters = db.session.execute(db.select(characters).filter_by(id=characters_id)).scalar_one()
        return jsonify({"result":characters.serialize()}), 200
    except:
        return jsonify({"msg":"characters do not exist"}), 404

@app.route('/planets', methods=['GET'])
def get_all_planets():
    data = db.session.scalars(db.select(Planets)).all()
    result = list(map(lambda item: item.serialize(),data))

    if result == []:
        return jsonify({"msg":"there are no existing planetary records"}), 404

    response_body = {
        "msg": "Hello, this is your GET /user response ",
        "results": result
    }

    return jsonify(response_body), 200

@app.route('/planets/<int:planets_id>', methods=['GET'])
def get_planet(planets_id):
    try:
        planets = db.session.execute(db.select(Planets).filter_by(id=planets_id)).scalar_one()
        return jsonify({"result":planets.serialize()}), 200
    except:
        return jsonify({"msg":"planet do not exist"}), 404
    
@app.route('/user/<int:user_id>/favorites/planets/<int:planet_id>', methods=['POST'])
def post_favorite_planets(user_id,planet_id):
    try:
        user = db.session.query(db.select(User).filter_by(id=user_id).exists()).scalar()
        planet = db.session.query(db.select(Planets).filter_by(id=planet_id).exists()).scalar()
        favorite = db.session.query(db.select(Favorites).filter_by(user_id=user_id, planet_id=planet_id).exists()).scalar()
        if not favorite:
            if planet and user:
                new_favorite = Favorites(user_id=user_id, characters_id=None, planet_id=planet_id)
                db.session.add(new_favorite)
                db.session.commit()
                return jsonify({"msg":"added favorite"}), 201
            else:
                return jsonify({"msg": "User or Planet not found"}), 404
        else:
            return jsonify({"msg": "Favorite already exists"}), 404
    except Exception as e:
        return jsonify({"msg":"Error", "error": str(e)}), 500
    
@app.route('/user/<int:user_id>/favorites', methods=['GET'])
def get_favorites_characters(user_id):
    try:
        favorites = db.session.execute(db.select(Favorites).filter_by(user_id=user_id)).scalars().all()
        if favorites != []:
            return jsonify({"result": [fav.serialize() for fav in favorites]}), 200
        return jsonify({"msg": "dont have favorites"})
    except Exception as e:
        return jsonify({"msg":"Error", "error": str(e)}), 500


@app.route('/user/<int:user_id>/favorites/characters/<int:characters_id>', methods=['POST'])
def post_favorite_characters(user_id,characters_id):
    try:
        user = db.session.query(db.select(User).filter_by(id=user_id).exists()).scalar()
        planet = db.session.query(db.select(characters).filter_by(id=characters_id).exists()).scalar()
        favorite = db.session.query(db.select(Favorites).filter_by(user_id=user_id, characters_id=characters_id).exists()).scalar()
        if not favorite:
            if planet and user:
                new_favorite = Favorites(user_id=user_id, characters_id=characters_id, planet_id=None)
                db.session.add(new_favorite)
                db.session.commit()
                return jsonify({"msg":"added favorite"}), 201
            else:
                return jsonify({"msg": "User or characters not found"}), 404
        else:
            return jsonify({"msg": "Favorite already exists"}), 404
    except Exception as e:
        return jsonify({"msg":"Error", "error": str(e)}), 500

@app.route('/user/<int:user_id>/favorites/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(user_id,planet_id):
    try:
        favorite = db.session.execute(db.select(Favorites).filter_by(user_id=user_id, planet_id=planet_id)).scalar_one_or_none()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            return jsonify({"msg":"deleted favorite"}), 201
        else:
            return jsonify({"msg": "Favorite or user not found"}), 404
    except Exception as e:
        return jsonify({"msg":"Error", "error": str(e)}), 500
    
@app.route('/user/<int:user_id>/favorites/characters/<int:characters_id>', methods=['DELETE'])
def delete_favorite_characters(user_id,characters_id):
    try:
        favorite = db.session.execute(db.select(Favorites).filter_by(user_id=user_id, characters_id=characters_id)).scalar_one_or_none()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            return jsonify({"msg":"deleted favorite"}), 201
        else:
            return jsonify({"msg": "Favorite or user not found"}), 404
    except Exception as e:
        return jsonify({"msg":"Error", "error": str(e)}), 500

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
