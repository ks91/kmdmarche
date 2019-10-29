import base64
import datetime
import qrcode  as qr
import requests

from flask import Blueprint, render_template, request, session, redirect, url_for
from io import BytesIO
from PIL import Image


# Prior to use this web application, please define a currency using API,
# and put the mint_id here.
MINT_ID = 'e6500c9aefa1dddb4295dcfa102e574497dfa83baefa117b9f34f654606f876f'

# Put the initial amount when signed up
INIT_AMOUNT = '30'

# Put API host name here.
PREFIX_API = 'http://127.0.0.1:5000'


def get_balance(name, user_id):
    r = requests.get(PREFIX_API + '/api/status/' + user_id + \
            '?mint_id=' + MINT_ID)
    res = r.json()

    if r.status_code != 200:
        return render_template('kmdmarche/error.html',
                message=res['error']['message'])

    return render_template('kmdmarche/sokin.html', name=name, user_id=user_id,
            balance=res['balance'], symbol=res['symbol'],
            to_name=request.args.get('to_name'),
            sending=request.method=='GET')


def qrmaker(s):
    qr_img = qr.make(s)

    # allocate buffer and write the image there
    buf = BytesIO()
    qr_img.save(buf,format="png")

    # encode the binary data into base64 and decode with UTF-8
    qr_b64str = base64.b64encode(buf.getvalue()).decode("utf-8")

    # to embed it as src attribute of image element
    qr_b64data = "data:image/png;base64,{}".format(qr_b64str)

    return qr_b64data


kmdmarche = Blueprint('kmdmarche', __name__, template_folder='templates',
        static_folder='./static')
title_name="CocoTano Marche"


@kmdmarche.route('/')
@kmdmarche.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return render_template('kmdmarche/top.html', name=session['name'])

    if request.method == 'GET':
        now = datetime.datetime.now()
        timeString = now.strftime('%H:%M')

        return render_template('kmdmarche/register.html',
                title_name=title_name, time=timeString)

    name = request.form.get('name')

    if name is None or len(name) <= 0:
        return render_template('kmdmarche/error.html',
                message='name is missing')

    r = requests.post(PREFIX_API + '/api/user', data={'name': name})
    res = r.json()

    if r.status_code != 201:
        return render_template('kmdmarche/error.html',
                message=res['error']['message'])

    user_id = res['user_id']

    session['name'] = name
    session['user_id'] = user_id

    r = requests.post(PREFIX_API + '/api/issue/' + MINT_ID,
            data={'user_id': user_id, 'amount': INIT_AMOUNT})

    if r.status_code != 200:
        return render_template('kmdmarche/error.html',
                message=res['error']['message'])

    return render_template('kmdmarche/top.html', name=name)


@kmdmarche.route('/log-in', methods=['GET', 'POST'])
def log_in():
    if request.method == 'GET':
        return render_template('kmdmarche/login.html')

    name = request.form.get('name')

    if name is None or len(name) <= 0:
        return render_template('kmdmarche/error.html',
                message='name is missing')

    r = requests.get(PREFIX_API + '/api/user' + '?name=' + name)
    res = r.json()

    if r.status_code != 200:
        return render_template('kmdmarche/error.html',
                message=res['error']['message'])

    session['name'] = name
    session['user_id'] = res['user_id']

    return render_template('kmdmarche/top.html', name=name)


@kmdmarche.route('/log-out')
def log_out():
    session.pop('user_id', None)
    session.pop('name', None)

    return render_template('kmdmarche/register.html')


# payment
@kmdmarche.route("/pay", methods=['POST','GET'])
def pay():
    if 'user_id' not in session:
        now = datetime.datetime.now()
        timeString = now.strftime('%H:%M')

        return render_template('kmdmarche/register.html',
                title_name=title_name, time=timeString)

    name = session['name']

    menu_name = "Cocotano Marche"
    info = ""
    s_url = PREFIX_API + '/kmdmarche/sokin?to_name=' + name
    qr_b64data = qrmaker(s_url)
    ts = datetime.datetime.now()
    return render_template('kmdmarche/pay2.html',
        qr_b64data=qr_b64data,
        qr_name=s_url,
        menu_name=menu_name,
        info=info
    )


# retry and quit
@kmdmarche.route('/event', methods=['GET'] )
def event():
    if request.method == 'GET':
        if request.args.get('submit') == 'Retry':
           return redirect(url_for('pay0'))
        elif request.args.get('submit') == 'Quit':
            return Response('Please close the web browser')
        else:
            pass # unknown
    elif request.method == 'POST':
        return redirect(url_for('pay0'))


@kmdmarche.route('/sokin', methods=['GET', 'POST'])
def sokin():
    if 'user_id' not in session:
        now = datetime.datetime.now()
        timeString = now.strftime('%H:%M')

        return render_template('kmdmarche/register.html',
                title_name=title_name, time=timeString)

    name = session['name']
    user_id = session['user_id']

    if request.method == 'GET':
        return get_balance(name, user_id)

    to_name = request.form.get('to_name')
    amount = request.form.get('amount')

    if to_name is None or len(to_name) <= 0:
        return render_template('kmdmarche/error.html',
                message='to_name is missing')

    if amount is None or len(amount) <= 0:
        return render_template('kmdmarche/error.html',
                message='amount is missing')

    r = requests.get(PREFIX_API + '/api/user' + '?name=' + to_name)
    res = r.json()

    if r.status_code != 200:
        return render_template('kmdmarche/error.html',
                message=res['error']['message'])

    to_user_id = res['user_id']

    r = requests.post(PREFIX_API + '/api/transfer/' + MINT_ID, data={
        'from_user_id': user_id,
        'to_user_id': to_user_id,
        'amount': amount
    })

    if r.status_code != 200:
        return render_template('kmdmarche/error.html',
                message=res['error']['message'])

    return get_balance(name, user_id)


@kmdmarche.route("/sokin_later")
def sokin_later():

    return render_template("kmd/marche/sokin_later.html")

# shop registration
@kmdmarche.route("/shopowner")
def shopowner():
    menu_name = "Register a shop!"
    info = ""
    now = datetime.datetime.now()
    timeString = now.strftime("%H:%M")
    return render_template("kmdmarche/shopowner.html", menu_name = menu_name, title_name = title_name, info = info, time=timeString)


@kmdmarche.route("/shopowener_later")
def shopowner_later():

    return render_template("kmdmarche/shopowner_later.html")


# TX
@kmdmarche.route("/tx")
def tx():
    menu_name = "Transactions"
    info = "Your transaction will be listed bellow"
    now = datetime.datetime.now()
    timeString = now.strftime("%H:%M")
    return render_template("kmdmarche/tx.html", menu_name = menu_name, title_name = title_name, info = info, time=timeString)


# list of shops
@kmdmarche.route("/ownerlist")
def ownerlist():
    menu_name = "Recommend Shop"
    info = "Show in Time Order"
    now = datetime.datetime.now()
    timeString = now.strftime("%H:%M")
    return render_template("kmdmarche/ownerlist.html", menu_name = menu_name, title_name = title_name, info = info, time=timeString)


@kmdmarche.route('/mypage')
def mypage():
    if 'user_id' not in session:
        now = datetime.datetime.now()
        timeString = now.strftime('%H:%M')

        return render_template('kmdmarche/register.html',
                title_name=title_name, time=timeString)

    name = session['name']
    user_id = session['user_id']

    r = requests.get(PREFIX_API + '/api/status/' + user_id + \
            '?mint_id=' + MINT_ID)
    res = r.json()

    if r.status_code != 200:
        return render_template('kmdmarche/error.html',
                message=res['error']['message'])

    menu_name = "My Page"
    now = datetime.datetime.now()
    timeString = now.strftime("%H:%M")
    return render_template("kmdmarche/mypage.html", menu_name="",
        title_name="", balance=res['balance'], symbol=res['symbol'],
        time=timeString, spendcoin="", getcoin="")


# end of app.py
