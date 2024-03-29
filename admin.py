from flask import request, flash, redirect, url_for
from flask.ext.superadmin import Admin, BaseView, expose, model, AdminIndexView
from database import User, Device, db, Beacon, Role, LocatingRequest, AccessToken
from authentication import _hash


def init_app(app, messageService, locatorService):

    class BroadcastView(BaseView):
        @expose('/')
        def index(self):
            roles = Role.query.all()

            return self.render('broadcast.jade', roles=roles)

        @expose('/send', methods=['POST'])
        def send(self):
            role_id = request.form.get('role')
            message = request.form.get('message')

            if message is None or len(message) == 0:
                flash("You need to supply a message!")
                return redirect(url_for('.index'))

            if role_id is None:
                flash("You need to select which group to target!")
                return redirect(url_for('.index'))

            if role_id < 0:
                messageService.sendBroadcast(User.query.all(), message)
            else:
                role = Role.query.get(role_id)
                messageService.sendBroadcast(role.users, message)

            flash("Successfully sent message")
            return redirect(url_for('.index'))

    class LocateView(BaseView):
        @expose('/')
        def index(self):
            users = User.query.all()

            return self.render('locate.jade', users=users)

        @expose('/send', methods=['POST'])
        def send(self):
            sender = User.query.get(request.form.get('sender', 1))
            target = User.query.get(request.form.get('target', 1))

            locatorService.startLocating(target, sender)

            flash('Started locating')
            return redirect(url_for('.index'))

        @expose('/cheeseit')
        def cheeseit(self):
            testuser = Role.query.get(27)

            messageService.sendCheesit(testuser.users)
            flash('Delicious topping activated')
            return redirect(url_for('.index'))

    class DataView(BaseView):
        @expose('/')
        def index(self):
            users = User.query.all()

            return self.render('data.jade', users=users)

        @expose('/send', methods=['POST'])
        def send(self):
            target = User.query.get(request.form.get('sender', 1))
            action = request.form.get('action')
            payload = request.form.get('payload')

            if action is None or len(action) == 0:
                flash("You need to supply an action!")
                return redirect(url_for('.index'))

            if payload is None or len(payload) == 0:
                flash("You need to supply a payload!")
                return redirect(url_for('.index'))

            messageService.sendData(target, payload, action)
            flash('Successfully sent data')
            return redirect(url_for('.index'))



    class UserView(model.ModelAdmin):
        session = db.session
        list_display = ('fullname', 'username', 'is_admin')

    class BeaconView(model.ModelAdmin):
        session = db.session
        list_display = ('location', 'uuid')


    class HashView(BaseView):
        @expose('/')
        def index(self):
            return self.render('hashview.jade')

        @expose('/send', methods=['POST'])
        def send(self):
            pw = request.form.get('password')
            hashpw = _hash(pw).hexdigest()
            flash(hashpw)
            return redirect(url_for('.index'))


    class AdminView(AdminIndexView):
        @expose('/')
        def index(self):
            return self.render('admin_index.jade')


    admin = Admin(name='LoKI', index_view=AdminView())
    admin.register(Role, session=db.session)
    admin.register(User, UserView)
    admin.register(Device, session=db.session)
    admin.register(AccessToken, session=db.session)
    admin.register(LocatingRequest, session=db.session)
    admin.register(Beacon, BeaconView)
    admin.add_view(BroadcastView(name='Broadcast', category='Tools'))
    admin.add_view(LocateView(name='Locate', category='Tools'))
    admin.add_view(DataView(name='Data', category='Tools'))
    admin.add_view(HashView(name='Hash', category='Tools'))
    admin.init_app(app)