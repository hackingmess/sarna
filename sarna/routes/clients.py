from flask import Blueprint, render_template, redirect, url_for, request
from sarna.model import Client, Assessment, Template, User
from sarna.model import db_session, select, commit, TransactionIntegrityError
from sarna.forms import ClientForm
from sarna.forms import AssessmentForm, TemplateCreateNewForm
from sarna.aux import redirect_referer
from uuid import uuid4

import os

ROUTE_NAME = os.path.basename(__file__).split('.')[0]
blueprint = Blueprint('clients', __name__)


@blueprint.route('/')
@db_session()
def index():
    context = dict(
        route=ROUTE_NAME,
        clients=select(client for client in Client)
    )
    return render_template('clients/list.html', **context)


@blueprint.route('/new', methods=('POST', 'GET'))
@db_session()
def new():
    form = ClientForm(request.form)
    context = dict(
        route=ROUTE_NAME,
        form=form
    )
    if form.validate_on_submit():
        Client(
            short_name=form.short_name.data,
            long_name=form.long_name.data
        )
        return redirect(url_for('.index'))

    return render_template('clients/new.html', **context)


@blueprint.route('/delete/<client_id>', methods=('POST',))
@db_session()
def delete(client_id: int):
    Client[client_id].delete()
    return redirect(url_for('.index'))


@blueprint.route('/<client_id>', methods=('POST', 'GET'))
@db_session()
def edit(client_id: int):
    client = Client[client_id]

    form_data = request.form.to_dict() or client.to_dict()
    form = ClientForm(**form_data)
    context = dict(
        route=ROUTE_NAME,
        form=form,
        client=client
    )
    if form.validate_on_submit():
        data = dict(form.data)
        data.pop('csrf_token', None)
        client.set(**data)
        return redirect(url_for('.index'))
    return render_template('clients/details.html', **context)


@blueprint.route('/<client_id>/add_assessment', methods=('POST', 'GET'))
@db_session()
def add_assessment(client_id: int):
    client = Client[client_id]
    form = AssessmentForm(request.form)
    context = dict(
        route=ROUTE_NAME,
        form=form,
        client=client
    )

    if form.validate_on_submit():
        data = dict(form.data)
        data.pop('csrf_token', None)

        Assessment(client=client, **data)
        return redirect(url_for('.edit', client_id=client_id))
    return render_template('clients/add_assessment.html', **context)


@blueprint.route('/<client_id>/template/<template_id>', methods=('POST', 'GET'))
@blueprint.route('/<client_id>/add_template', methods=('POST', 'GET'))
@db_session()
def add_template(client_id: int, template_id=None):
    client = Client[client_id]
    form = TemplateCreateNewForm()
    context = dict(
        route=ROUTE_NAME,
        form=form,
        client=client
    )

    if form.validate_on_submit():
        data = dict(form.data)
        data.pop('csrf_token', None)

        file = data.pop('file')
        filename = "{}.{}".format(uuid4(), file.filename.split('.')[-1])

        data['file'] = filename

        upload_path = client.template_path()
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)

        try:
            Template(client=client, **data)
            commit()
            file.save(os.path.join(upload_path, filename))
        except TransactionIntegrityError:
            form.name.errors.append('Name already used')

        return redirect(url_for('.edit', client_id=client_id))
    return render_template('clients/add_template.html', **context)


@blueprint.route('/<client_id>/template/<template_name>/delete', methods=('POST',))
@db_session()
def delete_template(client_id: int, template_name):
    Template[client_id, template_name].delete()
    return redirect_referer(url_for('.edit', client_id=client_id))


@blueprint.route('/<client_id>/template/<template_id>/download')
@db_session()
def download_template(client_id: int, template_id):
    ## TODO: implement
    pass