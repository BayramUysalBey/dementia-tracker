import json
import sys
import time
import sqlalchemy as sa
from flask import render_template
from rq import get_current_job
from app import create_app, db
from app.models import Caregiver, SymptomLog, Task
from app.email import send_email


app = create_app()
app.app_context().push()


def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = db.session.get(Task, job.get_id())
        task.caregiver.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()
        
def export_symptomlogs(caregiver_id):
    try:
        caregiver = db.session.get(Caregiver, caregiver_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_symptomlogs = db.session.scalar(sa.select(sa.func.count()).select_from(
            caregiver.symptomlogs.select().subquery()))
        for symptomlogs in db.session.scalars(caregiver.symptomlogs.select().order_by(
                SymptomLog.timestamp.asc())):
            data.append({'diagnosis': symptomlogs.diagnosis,
                         'timestamp': symptomlogs.timestamp.isoformat() + 'Z'})
            time.sleep(5)
            i += 1
            _set_task_progress(100 * i // total_symptomlogs)

        send_email(
            '[Dementia Tracker] Your blog posts',
            sender=app.config['ADMINS'][0], recipients=[caregiver.email],
            text_body=render_template('email/export_symptomlogs.txt', caregiver=caregiver),
            html_body=render_template('email/export_symptomlogs.html', caregiver=caregiver),
            attachments=[('symptomlogs.json', 'application/json',
                          json.dumps({'symptomlog': data}, indent=4))],
            sync=True)
    except Exception:
        _set_task_progress(100)
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)

def reindex_search():
    try:
        _set_task_progress(0)
        SymptomLog.reindex()
        _set_task_progress(100)
    except Exception:
        _set_task_progress(100)
        app.logger.error('Unhandled exception during reindexing', exc_info=sys.exc_info())