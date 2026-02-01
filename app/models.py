from datetime import datetime, timezone
from hashlib import md5
import json
from time import time
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import db, login
from app.search import add_to_index, remove_from_index, query_index
from flask import current_app, url_for
import redis
import rq



class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return [], 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        query = sa.select(cls).where(cls.id.in_(ids)).order_by(
            db.case(*when, value=cls.id))
        return db.session.scalars(query), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in db.session.scalars(sa.select(cls)):
            add_to_index(cls.__tablename__, obj)

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('caregiver.id'),
              primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('caregiver.id'),
              primary_key=True)
)


class Caregiver(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    caregiver_name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    last_message_read_time: so.Mapped[Optional[datetime]]    
    symptomlogs: so.WriteOnlyMapped['SymptomLog'] = so.relationship(back_populates='observer')
    following: so.WriteOnlyMapped['Caregiver'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    followers: so.WriteOnlyMapped['Caregiver'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')
    messages_sent: so.WriteOnlyMapped['Message'] = so.relationship(
        foreign_keys='Message.sender_id', back_populates='observer')
    messages_received: so.WriteOnlyMapped['Message'] = so.relationship(
        foreign_keys='Message.recipient_id', back_populates='recipient')    
    notifications: so.WriteOnlyMapped['Notification'] = so.relationship(
        back_populates='caregiver')
    tasks: so.WriteOnlyMapped['Task'] = so.relationship(back_populates='caregiver')
    
    def __repr__(self):
        return f'<Caregiver {self.caregiver_name}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        if self.email in current_app.config['ADMINS']:
             return url_for('static', filename='admin.png')
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'
    
    def follow(self, caregiver):
        if not self.is_following(caregiver):
            self.following.add(caregiver)

    def unfollow(self, caregiver):
        if self.is_following(caregiver):
            self.following.remove(caregiver)

    def is_following(self, caregiver):
        query = self.following.select().where(Caregiver.id == caregiver.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery())
        return db.session.scalar(query)
    
    
    def following_symptomlogs(self):
        Observer = so.aliased(Caregiver)
        Follower = so.aliased(Caregiver)
        return (
            sa.select(SymptomLog)
            .join(SymptomLog.observer.of_type(Observer))
            .join(Observer.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Observer.id == self.id,
            ))
            .group_by(SymptomLog)
            .order_by(SymptomLog.timestamp.desc())
        )
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except Exception:
            return
        return db.session.get(Caregiver, id)
    
    def unread_message_count(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        query = sa.select(Message).where(Message.recipient == self,
                                         Message.timestamp > last_read_time)
        return db.session.scalar(sa.select(sa.func.count()).select_from(
            query.subquery()))

    def add_notification(self, name, data):
        db.session.execute(self.notifications.delete().where(
            Notification.name == name))
        n = Notification(name=name, payload_json=json.dumps(data), caregiver=self)
        db.session.add(n)
        return n
    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue(f'app.tasks.{name}', self.id,
                                                *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description,
                    caregiver=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        query = self.tasks.select().where(Task.complete == False)
        return db.session.scalars(query)

    def get_task_in_progress(self, name):
        query = self.tasks.select().where(Task.name == name,
                                          Task.complete == False)
        return db.session.scalar(query)
    

@login.user_loader
def load_user(id):
    return db.session.get(Caregiver, int(id))

    

class SymptomLog(SearchableMixin, db.Model):
    __searchable__ = ['diagnosis']
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    diagnosis: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    caregiver_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Caregiver.id), index=True)
    severity: so.Mapped[int] = so.mapped_column(sa.Integer, default=1)
    observer: so.Mapped[Caregiver] = so.relationship(back_populates='symptomlogs')

    def __repr__(self):
        return f'<SymptomLog {self.diagnosis}>'
    

SEVERITY_LEVELS = {
    1: {"name": "Mild", "color": "success", "description": "Occasional forgetfulness"},
    2: {"name": "Moderate", "color": "warning", "description": "Frequent memory loss"},
    3: {"name": "Severe", "color": "danger", "description": "Significant memory loss"},
    4: {"name": "Critical", "color": "dark", "description": "Complete disorientation"}
}

def get_severity_display(severity):    
    return SEVERITY_LEVELS.get(severity, {"name": "Unknown", "color": "secondary"})

def get_severity_options():    
    return [(k, f"{v['name']} - {v['description']}") for k, v in SEVERITY_LEVELS.items()]



class Message(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    sender_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Caregiver.id),
                                                 index=True)
    recipient_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Caregiver.id),
                                                    index=True)
    diagnosis: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    observer: so.Mapped[Caregiver] = so.relationship(
        foreign_keys='Message.sender_id',
        back_populates='messages_sent')
    recipient: so.Mapped[Caregiver] = so.relationship(
        foreign_keys='Message.recipient_id',
        back_populates='messages_received')

    def __repr__(self):
        return '<Message {}>'.format(self.observer)
    


class Notification(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    caregiver_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Caregiver.id),
                                               index=True)
    timestamp: so.Mapped[float] = so.mapped_column(index=True, default=time)
    payload_json: so.Mapped[str] = so.mapped_column(sa.Text)

    caregiver: so.Mapped[Caregiver] = so.relationship(back_populates='notifications')

    def get_data(self):
        return json.loads(str(self.payload_json))
    


class Task(db.Model):
    id: so.Mapped[str] = so.mapped_column(sa.String(36), primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.String(128))
    caregiver_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Caregiver.id))
    complete: so.Mapped[bool] = so.mapped_column(default=False)

    caregiver: so.Mapped[Caregiver] = so.relationship(back_populates='tasks')

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100