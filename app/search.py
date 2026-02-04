from flask import current_app

def add_to_index(index, model):
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    try:
        current_app.elasticsearch.index(index=index, id=model.id, body=payload)
        current_app.logger.info(f'Indexed document {model.id} in index {index}')
    except Exception as e:
        current_app.logger.error(f'Search index error for ID {model.id} in {index}: {e}')

def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    try:
        current_app.elasticsearch.delete(index=index, id=model.id)
        current_app.logger.info(f'Removed document {model.id} from index {index}')
    except Exception as e:
        current_app.logger.error(f'Search delete error for ID {model.id} in {index}: {e}')

def clear_index(index):
    if not current_app.elasticsearch:
        return
    try:
        if current_app.elasticsearch.indices.exists(index=index):
            current_app.elasticsearch.indices.delete(index=index)
            current_app.logger.info(f'Deleted index {index}')
    except Exception as e:
        current_app.logger.error(f'Error clearing index {index}: {e}')

def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        return [], 0
    try:
        current_app.logger.info(f'Searching {index} for "{query}" (page {page}, query_string mode)')
        # Use query_string for better wildcard/multi-word behavior
        # "*" attached to query allows partial word matching
        search_query = query if '*' in query else f"*{query}*"
        search = current_app.elasticsearch.search(
            index=index,
            body={
                'query': {
                    'query_string': {
                        'query': search_query,
                        'fields': ['*'],
                        'default_operator': 'AND'
                    }
                }
            },
            from_=(page - 1) * per_page,
            size=per_page)
        ids = [int(hit['_id']) for hit in search['hits']['hits']]
        total = search['hits']['total']['value']
        current_app.logger.info(f'Search found {total} hits. IDs: {ids}')
        return ids, total
    except Exception as e:
        current_app.logger.error(f'Search query error for "{query}" in {index}: {e}')
        return [], 0