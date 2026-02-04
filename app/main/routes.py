from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, current_app, g
from flask_login import current_user, login_required
from flask_babel import _, get_locale
import sqlalchemy as sa
from app import db
from app.main.forms import EditProfileForm, EmptyForm, SymptomLogForm, SearchForm, MessageForm, EditSymptomlogForm
from app.models import Caregiver, SymptomLog, Message, Notification
from app.main import bp



@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())
        

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = SymptomLogForm()
    if form.validate_on_submit():
        symptomlog = SymptomLog(diagnosis=form.symptomlog.data, observer=current_user, severity=form.severity.data)
        db.session.add(symptomlog)
        db.session.commit()
        flash(_('Your symptomlog is now live!'))
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    symptomlogs = db.paginate(current_user.following_symptomlogs(), page=page,
                        per_page=current_app.config['SYMPTOMLOGS_PER_PAGE'], error_out=False)
    next_url = url_for('main.index', page=symptomlogs.next_num) \
        if symptomlogs.has_next else None
    prev_url = url_for('main.index', page=symptomlogs.prev_num) \
        if symptomlogs.has_prev else None
    return render_template('index.html', title=_('Home'), form=form,
                           symptomlogs=symptomlogs.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    query = sa.select(SymptomLog).order_by(SymptomLog.timestamp.desc())
    symptomlogs = db.paginate(query, page=page,
                        per_page=current_app.config['SYMPTOMLOGS_PER_PAGE'], error_out=False)
    next_url = url_for('main.explore', page=symptomlogs.next_num) \
        if symptomlogs.has_next else None
    prev_url = url_for('main.explore', page=symptomlogs.prev_num) \
        if symptomlogs.has_prev else None
    return render_template('index.html', title=_('Explore'), symptomlogs=symptomlogs.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/caregiver/<caregiver_name>')
@login_required
def caregiver(caregiver_name):
    caregiver = db.first_or_404(sa.select(Caregiver).where(Caregiver.caregiver_name == caregiver_name))
    page = request.args.get('page', 1, type=int)
    query = caregiver.symptomlogs.select().order_by(SymptomLog.timestamp.desc())
    symptomlogs = db.paginate(query, page=page,
                        per_page=current_app.config['SYMPTOMLOGS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.caregiver', caregiver_name=caregiver.caregiver_name, page=symptomlogs.next_num) \
        if symptomlogs.has_next else None
    prev_url = url_for('main.caregiver', caregiver_name=caregiver.caregiver_name, page=symptomlogs.prev_num) \
        if symptomlogs.has_prev else None
    form = EmptyForm()
    return render_template('caregiver.html', caregiver=caregiver, symptomlogs=symptomlogs.items, next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/caregiver/<caregiver_name>/popup')
@login_required
def caregiver_popup(caregiver_name):
    caregiver = db.first_or_404(sa.select(Caregiver).where(Caregiver.caregiver_name == caregiver_name))
    form = EmptyForm()
    return render_template('caregiver_popup.html', caregiver=caregiver, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.caregiver_name)
    if form.validate_on_submit():
        current_user.caregiver_name = form.caregiver_name.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.caregiver_name.data = current_user.caregiver_name
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/follow/<caregiver_name>', methods=['POST'])
@login_required
def follow(caregiver_name):
    form = EmptyForm()
    if form.validate_on_submit():
        caregiver = db.session.scalar(
            sa.select(Caregiver).where(Caregiver.caregiver_name == caregiver_name))
        if caregiver is None:
            flash(_(f'Caregiver {caregiver_name} not found.'))
            return redirect(url_for('main.index'))
        if caregiver == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('main.caregiver', caregiver_name=caregiver_name))
        current_user.follow(caregiver)
        db.session.commit()
        flash(_(f'You are following {caregiver_name}!'))
        return redirect(url_for('main.caregiver', caregiver_name=caregiver_name))
    else:
        return redirect(url_for('main.index'))
    

@bp.route('/unfollow/<caregiver_name>', methods=['POST'])
@login_required
def unfollow(caregiver_name):
    form = EmptyForm()
    if form.validate_on_submit():
        caregiver = db.session.scalar(
            sa.select(Caregiver).where(Caregiver.caregiver_name == caregiver_name))
        if caregiver is None:
            flash(_(f'Caregiver {caregiver_name} not found.'))
            return redirect(url_for('main.index'))
        if caregiver == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('main.caregiver', caregiver_name=caregiver_name))
        current_user.unfollow(caregiver)
        db.session.commit()
        flash(_(f'You are not following {caregiver_name}.'))
        return redirect(url_for('main.caregiver', caregiver_name=caregiver_name))
    else:
        return redirect(url_for('main.index'))
    

@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    symptomlogs, total = SymptomLog.search(g.search_form.q.data, page,
                               current_app.config['SYMPTOMLOGS_PER_PAGE'])
    symptomlogs_list = list(symptomlogs)
    current_app.logger.info(f'Search results: Found {total} in index, {len(symptomlogs_list)} matched in database.')
    
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['SYMPTOMLOGS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), symptomlogs=symptomlogs_list,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    caregiver = db.first_or_404(sa.select(Caregiver).where(Caregiver.caregiver_name == recipient))
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(observer=current_user, recipient=caregiver,
                      diagnosis=form.message.data)
        db.session.add(msg)  
        caregiver.add_notification('unread_message_count',
                              caregiver.unread_message_count())
        db.session.commit()
        flash(('Your message has been sent.'))
        return redirect(url_for('main.caregiver', caregiver_name=recipient))
    return render_template('send_message.html', title=('Send Message'),
                           form=form, recipient=recipient)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.now(timezone.utc)
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    query = current_user.messages_received.select().order_by(
        Message.timestamp.desc())
    messages = db.paginate(query, page=page,
                           per_page=current_app.config['MESSAGES_PER_PAGE'],
                           error_out=False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/export_symptomlogs')
@login_required
def export_symptomlogs():
    if current_user.get_task_in_progress('export_symptomlogs'):
        flash(_('An export task is currently in progress'))
    else:
        current_user.launch_task('export_symptomlogs', _('Exporting symptomlogs...'))
        db.session.commit()
    return redirect(url_for('main.caregiver', caregiver_name=current_user.caregiver_name))



@bp.route('/reindex_search')
@login_required
def reindex_search():
    if current_user.email not in current_app.config['ADMINS']:
        flash(_('You do not have permission to perform this action.'))
        return redirect(url_for('main.index'))
    if current_user.get_task_in_progress('reindex_search'):
        flash(_('A reindexing task is currently in progress.'))
    else:
        try:
            current_app.logger.info(f'User {current_user.email} triggered search reindexing.')
            current_user.launch_task('reindex_search', _('Reindexing search...'))
            db.session.commit()
            flash(_('Reindexing task started in the background.'))
        except Exception as e:
            # Fallback for environments without Redis (e.g. Render free tier)
            current_app.logger.warning(f'Redis queue unavailable or failed: {e}. Falling back to synchronous reindexing.')
            try:
                from app.search import clear_index
                db_count = db.session.scalar(sa.select(sa.func.count()).select_from(SymptomLog))
                current_app.logger.info(f'Starting manual synchronous reindexing for {db_count} documents...')
                clear_index(SymptomLog.__tablename__)
                SymptomLog.reindex()
                current_app.logger.info('Synchronous reindexing completed successfully.')
                flash(_('Reindexing completed (synchronously).'))
            except Exception as reindex_error:
                current_app.logger.error(f'Synchronous reindexing failed: {reindex_error}')
                flash(_(f'Reindexing failed: {reindex_error}'))
    return redirect(url_for('main.index'))


@bp.route('/check_search_sync')
@login_required
def check_search_sync():
    if current_user.email not in current_app.config['ADMINS']:
        flash(_('You do not have permission to perform this action.'))
        return redirect(url_for('main.index'))
    
    report = []
    index = SymptomLog.__tablename__
    
    if not current_app.elasticsearch:
        report.append("Elasticsearch is NOT configured in the app.")
        report.append(f"ELASTICSEARCH_URL present: {'Yes' if current_app.config.get('ELASTICSEARCH_URL') else 'No'}")
        report.append(f"ELASTICSEARCH_USER present: {'Yes' if current_app.config.get('ELASTICSEARCH_USER') else 'No'}")
        report.append(f"ELASTICSEARCH_PASS present: {'Yes' if current_app.config.get('ELASTICSEARCH_PASS') else 'No'}")
    else:
        try:
            # Get ES document IDs
            search = current_app.elasticsearch.search(
                index=index,
                body={'query': {'match_all': {}}, 'fields': ['_id'], '_source': False},
                size=1000
            )
            es_ids = [int(hit['_id']) for hit in search['hits']['hits']]
            
            # Get DB document IDs
            db_ids = [log.id for log in db.session.scalars(sa.select(SymptomLog)).all()]
            
            report.append(f"Elasticsearch IDs: {es_ids}")
            report.append(f"Database IDs: {db_ids}")
            
            mismatched_es = [id for id in es_ids if id not in db_ids]
            mismatched_db = [id for id in db_ids if id not in es_ids]
            
            if mismatched_es:
                report.append(f"Mismatched IDs (in ES but NOT in DB): {mismatched_es}")
            if mismatched_db:
                report.append(f"Mismatched IDs (in DB but NOT in ES): {mismatched_db}")
                
            if not mismatched_es and not mismatched_db:
                report.append("SUCCESS: All IDs are synchronized!")
            else:
                report.append("WARNING: Sync mismatch detected. Please run /reindex_search")
                
        except Exception as e:
            report.append(f"Error during check: {e}")
            
    return "<br>".join(report)


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    query = current_user.notifications.select().where(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    notifications = db.session.scalars(query)
    return [{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications]


@bp.route('/edit_symptom/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_symptom(id):
    symptomlog = db.session.get(SymptomLog, id)
    if not symptomlog:
        flash(_('Symptom log not found.'))
        return redirect(url_for('main.index'))
    if symptomlog.observer != current_user:
        flash(_('You cannot edit this symptom log.'))
        return redirect(url_for('main.index'))
    form = EditSymptomlogForm()
    if form.validate_on_submit():
        symptomlog.diagnosis = form.symptomlog.data
        symptomlog.severity = form.severity.data
        db.session.commit()
        flash(_('The symptom log has been updated.'))
        return redirect(url_for('main.index'))
    elif request.method == 'GET':
        form.symptomlog.data = symptomlog.diagnosis
        form.severity.data = symptomlog.severity
    return render_template('edit_symptom.html', title=_('Edit Symptom Log'),
                           form=form)


@bp.route('/delete_symptom/<int:id>', methods=['POST'])
@login_required
def delete_symptom(id):
    symptomlog = db.session.get(SymptomLog, id)
    if not symptomlog:
        flash(_('Symptom log not found.'))
        return redirect(url_for('main.index'))
    if symptomlog.observer != current_user:
        flash(_('You cannot delete this symptom log.'))
        return redirect(url_for('main.index'))
    db.session.delete(symptomlog)
    db.session.commit()
    flash(_('The symptom log has been deleted.'))
    return redirect(url_for('main.index'))