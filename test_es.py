from app import create_app
from app.models import SymptomLog
import sqlalchemy as sa
from app import db
import os

def test():
    app = create_app()
    with app.app_context():
        es = app.elasticsearch
        if not es:
            print("No Elasticsearch client found.")
            return
        
        print(f"ES Client: {es}")
        try:
            info = es.info()
            print(f"ES Server Info: {info.body}")
        except Exception as e:
            print(f"Failed to get server info: {e}")
            return
        
        log = db.session.scalar(sa.select(SymptomLog))
        if not log:
            print("No SymptomLog found in DB.")
            return
            
        print(f"Attempting to index SymptomLog ID {log.id}")
        payload = {field: getattr(log, field) for field in log.__searchable__}
        try:
            res = es.index(index='symptom_log', id=log.id, body=payload)
            print(f"Index Success: {res}")
        except Exception as e:
            print(f"Index Failure: {e}")
            if hasattr(e, 'body'):
                print(f"Error Body: {e.body}")

if __name__ == "__main__":
    test()
