import os
from contextlib import suppress

from flask import render_template
from flask_api import FlaskAPI
from flask_api.exceptions import ParseError, NotFound
from flask_cors import CORS
from flask_pymongo import PyMongo
from funcy.seqs import repeat

app = FlaskAPI(__name__, template_folder='../templates', static_folder='../static')

app.config['MONGO_URI'] = 'mongodb://steemit:steemit@mongo1.steemdata.com:27017/SteemData'

mongo = PyMongo(app)
CORS(app)  # enable cors defaults (*)


@app.route('/')
def hello_world():
    return render_template('index.html')


# busy.org
# --------
@app.route('/busy.org/<string:account_name>/<string:following>')
def busy_account_following(account_name, following):
    """
    Fetch users followers or followings and their metadata.
    Returned list is ordered by follow time (newest followers first). \n
    Usage: `GET /busy/<string:account_name>/<string:following>`\n
    `following` must be 'following' or 'followers'.\n
    """
    if following not in ['following', 'followers']:
        raise ParseError(detail='Please specify following or followers.')

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
    accounts_ordered = list(repeat('', len(acc[following])))
    for a in accounts_w_meta:
        with suppress(ValueError):
            accounts_ordered[acc[following].index(a.get('name', None))] = a
    return [x for x in accounts_ordered if x][::-1]


if __name__ == '__main__':
    app.run(host=os.getenv('FLASK_HOST', '127.0.0.1'),
            debug=not os.getenv('PRODUCTION', False))
