from collections import ChainMap

import pymongo
from flask_pymongo import PyMongo


def steemq_query(mongo: PyMongo, conditions=None, search=None, sort_by='new', options=None):
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

    if search:
        query['$text'] = {'$search': search}
        projection['score'] = {'$meta': 'textScore'}
        sorting = [('score', {'$meta': 'textScore'})]

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


def head_block(mongo: PyMongo):
    last_op = mongo.db['Operations'].find_one(
        filter={},
        projection={'block_num': 1, '_id': 0},
        sort=[('block_num', pymongo.DESCENDING)],
    )
    return last_op['block_num']


def head_block_steem():
    from steem import Steem
    s = Steem()
    return s.last_irreversible_block_num


def health_check(mongo):
    steemd_head = head_block_steem()
    mongo_head = head_block(mongo)
    diff = steemd_head - mongo_head
    return {
        'steemd_head': steemd_head,
        'mongo_head': mongo_head,
        'diff': diff,
    }
