from flask import request, flash, redirect, url_for
from flask.ext.superadmin import Admin, BaseView, expose, model
from database import User, Device, db, Beacon, Role, LocatingRequest, AccessToken



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
            testuser = Role.query.get(7)

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

    admin = Admin(name='LoKI')
    admin.register(Role, session=db.session)
    admin.register(User, UserView)
    admin.register(Device, session=db.session)
    admin.register(AccessToken, session=db.session)
    admin.register(LocatingRequest, session=db.session)
    admin.register(Beacon, session=db.session)
    admin.add_view(BroadcastView(name='Broadcast', category='Tools'))
    admin.add_view(LocateView(name='Locate', category='Tools'))
    admin.add_view(DataView(name='Data', category='Tools'))
    admin.init_app(app)