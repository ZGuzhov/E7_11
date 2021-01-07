import os
from flask_caching import Cache
from flask_pymongo import PyMongo
from flask import Flask, request, jsonify


app = Flask(__name__)
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
app.config["MONGO_URI"] = "mongodb://{mongo_host}:27017/flask".format(mongo_host=MONGO_HOST)
app.config['MONGO_DBNAME'] = 'dashboard' 
mongo = PyMongo(app)
cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': 'redis://{redis_host}:6379/0'.format(redis_host=REDIS_HOST)})


@app.route('/')
@cache.cached()
def hello():
    readme = 'Здравствуйте. <br>\
Это веб-приложение на Flask, Mongo и Redis. <br>\
Оно является Практическим заданием E7.11. <br>\
Данные хрнятся в базе данных MongoDB, кеширование проиводится с помощью Redis. <br>\
<br>\
Доступны следующие варианты: <br>\
- HTTP POST http://83.220.171.117:5000/message?text=text - создания нового сообщения с текстом text <br>\
- HTTP POST http://83.220.171.117:5000/tag/<message_id>?tag=tag - добавление тега к существующему сообщению с id message_id с текстом тега tag <br>\
- HTTP POST http://83.220.171.117:5000/comment/<message_id>?comment=comment - добавление комментария к существующему сообщению с id message_id с текстом комментария comment <br>\
- HTTP GET http://83.220.171.117:5000/message/message_id - получение полного сообщения с id message_id с тегами и комментариями <br>\
- HTTP GET http://83.220.171.117:5000/stats/message_id - получение статистики по сообщению с id message_id (количество тегов и комментариев)'
    return readme


@app.route('/message', methods=['POST'])
def message():
    data = request.args
    if request.method == 'POST':
        if data.get('text'):
            res = mongo.db.dashboard.insert_one(dict(data))
            return jsonify({'ok': True, 'message': 'Сообщение успешно создано, id: % s ' % res.inserted_id}), 200
        else:
            return jsonify({'ok': False, 'message': 'Сообщение не создано, необходимо передать аргумент text'}), 400
        
        
@app.route('/tag/<ObjectId:message_id>', methods=['POST'])
def add_tag_to_message(message_id):
    data = request.args
    if request.method == 'POST':
        if data.get('tag'):
            res = mongo.db.dashboard.update_one({"_id": message_id}, {"$addToSet": {"tags": data.get('tag')}})
            cache.clear()
            return jsonify({'ok': True, 'message': 'Tag успешно добавлен! % s ' % res}), 200
        else:
            return jsonify({'ok': False, 'message': 'Tag не добавлен, необходимо передать аргумент tag'}), 400


@app.route('/comment/<ObjectId:message_id>', methods=['POST'])
def add_comment_to_message(message_id):
    data = request.args
    if request.method == 'POST':
        if data.get('comment'):
            res = mongo.db.dashboard.update_one({"_id": message_id}, {"$push": {"comments": data.get('comment')}})
            cache.clear()
            return jsonify({'ok': True, 'message': 'Комментарий успешно добавлен! % s ' % res}), 200
        else:
            return jsonify({'ok': False, 'message': 'Комментарий не добавлен, необходимо передать аргумент comment'}), 400


@app.route('/message/<ObjectId:message_id>', methods=['GET'])
@cache.cached()
def message_by_id(message_id):
    if request.method == 'GET':
        res = mongo.db.dashboard.find_one_or_404(message_id)
        return jsonify({'ok': True, 'message': 'Message found! % s ' % res}), 200


@app.route('/stats/<ObjectId:message_id>', methods=['GET'])
@cache.cached()
def stats_by_id(message_id):
    if request.method == 'GET':
        res = mongo.db.dashboard.find_one_or_404(message_id)
        tags = 0 
        comments = 0 
        if 'tags' in res.keys():
            tags = len(res['tags'])
        if 'comments' in res.keys():
            comments = len(res['comments'])
        return jsonify({'ok': True, 'message': 'Message has {tags} tags and {comments} comments'.format(tags=tags, comments=comments)}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)