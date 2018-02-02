import datetime as dt
from collections import ChainMap

import pymongo
from flask_pymongo import PyMongo
from funcy import walk_values, any
from steem import Steem


def steemq_query(mongo: PyMongo, conditions=None, search=None, sort_by='new',
                 options=None):
    """ Run a query against SteemQ Posts. """
    # apply conditions, such as time constraints
    conditions = conditions or {}
    query = {
        'json_metadata.app': 'steemq/0.1',
        **conditions,
    }
    projection = {
        '_id': 0,
        'identifier': 1,
        'created': 1,
    }

    sorting = []
    if sort_by == 'new':
        sorting = [('created', pymongo.DESCENDING)]
    elif sort_by == 'payout':
        sorting = [
            ('pending_payout_value.amount', pymongo.DESCENDING),
            ('total_payout_value.amount', pymongo.DESCENDING),
        ]
    elif sort_by == 'votes':
        sorting = [('net_votes', pymongo.DESCENDING)]

    if search:
        query['$text'] = {'$search': search}
        projection['score'] = {'$meta': 'textScore'}
        sorting.insert(0, ('score', {'$meta': 'textScore'}))

    options = options or {}
    default_options = {
        'limit': 1000,
        'skip': 0,
    }
    options = ChainMap(options, default_options)

    return list(mongo.db['Posts'].find(
        filter=query,
        projection=projection,
        sort=sorting,
        limit=options.get('limit'),
        skip=options.get('skip'),
    ))


# Health Checks
# -------------
def head_block():
    s = Steem()
    return s.last_irreversible_block_num


def find_latest_item(mongo, collection_name, field_name):
    last_op = mongo.db[collection_name].find_one(
        filter={},
        projection={field_name: 1, '_id': 0},
        sort=[(field_name, pymongo.DESCENDING)],
    )
    return last_op[field_name]


def health_check(mongo):
    steemd_head = head_block()
    indexer = mongo.db['_indexer'].find_one()
    checkpoints = {k: v for k, v in indexer.items() if '_checkpoint' in k}
    del checkpoints['accounts_checkpoint']
    diff = steemd_head - min(checkpoints.values())
    return {
        **checkpoints,
        'steemd_head': steemd_head,
        'diff': diff,
        'status': 'impaired' if diff > 200 else 'ok',
    }


def collection_health(mongo):
    last_items = {
        'Posts': find_latest_item(mongo, 'Posts', 'created'),
        'Comments': find_latest_item(mongo, 'Comments', 'created'),
        'Operations': find_latest_item(mongo, 'Operations', 'timestamp'),
        'AccountOperations': find_latest_item(mongo, 'AccountOperations', 'timestamp'),
    }

    def time_delta(item_time):
        delta = dt.datetime.utcnow().replace(tzinfo=None) - item_time.replace(tzinfo=None)
        return delta.seconds

    timings = walk_values(time_delta, last_items)
    return {
        **timings,
        'status': 'impaired' if any(lambda x: x > (60 * 10), timings.values()) else 'ok'
    }


def steemd_health(remote_hostname: str):
    s = Steem()
    local_steemd = s.last_irreversible_block_num

    s.set_node(remote_hostname)
    remote_steemd = s.last_irreversible_block_num
    diff = remote_steemd - local_steemd

    return dict(
        remote_steemd=remote_steemd,
        local_steemd=local_steemd,
        diff=diff,
        status='ok' if diff < 100 else 'impaired',
    )
