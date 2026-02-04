from app import create_app
from app.models import SymptomLog
import sqlalchemy as sa
from app import db
import json

def test():
    app = create_app()
    with app.app_context():
        es = app.elasticsearch
        if not es:
            print("No Elasticsearch client found.")
            return
        
        index = "symptom_log"
        print(f"ES URL: {app.config['ELASTICSEARCH_URL']}")
        try:
            # Check mapping
            mapping = es.indices.get_mapping(index=index)
            print("\nMapping for 'symptom_log':")
            print(json.dumps(mapping.body, indent=2))
            
            # Check documents (match_all)
            print("\nRetrieving all documents from ES...")
            search = es.search(index=index, body={'query': {'match_all': {}}})
            hits = search.body['hits']['hits']
            print(f"Found {len(hits)} documents.")
            for hit in hits:
                print(f" - ID {hit['_id']}: {hit['_source']}")
            
            # Check search for a known word
            # We'll pick a word from the first document if available
            if hits:
                first_doc = hits[0]['_source']
                if 'diagnosis' in first_doc:
                    word = first_doc['diagnosis'].split()[0]
                    print(f"\nTesting search for word: '{word}'")
                    res = es.search(
                        index=index,
                        body={'query': {'multi_match': {'query': word, 'fields': ['*']}}}
                    )
                    print(f"Search found {res.body['hits']['total']['value']} hits.")

        except Exception as e:
            print(f"Error: {e}")
            if hasattr(e, 'body'):
                print(f"Error Body: {e.body}")

if __name__ == "__main__":
    test()
