import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db
from app.models import Caregiver, SymptomLog, get_severity_display, get_severity_options, Message, Notification, Task

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'Caregiver': Caregiver, 'SymptomLog': SymptomLog, 'Message': Message, 'Notification': Notification, 'Task': Task}

@app.context_processor
def utility_processor():
    return {
        'get_severity_display': get_severity_display,
        'get_severity_options': get_severity_options
    }