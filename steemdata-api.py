import os

from flask_api import FlaskAPI
from flask_api.exceptions import ParseError, NotFound
from flask_pymongo import PyMongo
from funcy import where, first
from steemdata.helpers import timeit

app = FlaskAPI(__name__)

app.config['MONGO_URI'] = 'mongodb://steemit:steemit@mongo1.steemdata.com:27017/SteemData'

mongo = PyMongo(app)


@app.route('/')
def hello_world():
    return {'success': True}


@app.route('/busy.org/<string:account_name>/with_metadata/<string:following>')
def busy_account_following(account_name, following):
    """
    Fetch users followers or followings and their metadata.
    Returned list is ordered by follow time (newest followers first). \n
    Usage: `GET /busy/<string:account_name>/with_metadata/<string:following>`\n
    `following` must be 'following' or 'followers'.\n
    """
    if following not in ['following', 'followers']:
        raise ParseError(detail='following should be following or following')

    acc = mongo.db['Accounts'].find_one({'name': account_name}, {following: 1, '_id': 0})
    if not acc:
        raise NotFound(detail='Could not find STEEM account %s' % account_name)

    # if follower list is empty
    if not acc[following]:
        return []

    allowed_fields = {
        '_id': 0, 'name': 1, 'sp': 1, 'rep': 1,
        'followers_count': 1, 'following_count': 1, 'post_count': 1,
    }
    accounts_w_meta = list(mongo.db['Accounts'].find({'name': {'$in': acc[following]}}, allowed_fields))

    # return in LIFO order (last to follow is listed first)
    accounts_ordered = []
    with timeit():
        for a in acc[following]:
            accounts_ordered.append(first(where(accounts_w_meta, name=a)))
    return accounts_ordered[::-1]


if __name__ == '__main__':
    app.run(host=os.getenv('FLASK_HOST', '127.0.0.1'),
            debug=not os.getenv('PRODUCTION', False))
