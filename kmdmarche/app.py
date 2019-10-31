import base64
import bbc1
import datetime
import qrcode  as qr
import requests
import time

from bbc1.core import bbclib
from bbc1.lib.app_support_lib import Database
from flask import Blueprint, render_template, request, session, redirect
from flask import g, url_for
from io import BytesIO
from PIL import Image


# Prior to use this web application, please define a currency using API,
# and put the mint_id here.
MINT_ID = 'e6500c9aefa1dddb4295dcfa102e574497dfa83baefa117b9f34f654606f876f'

# Put the initial amount when signed up
INIT_AMOUNT = '30'

# Put API host name here.
PREFIX_API = 'http://127.0.0.1:5000'

# Put base time (to count transactions) in Unix time here.
BASE_TIME = 0

# Put the number of transactions to show in a list page here.
LIST_COUNT = 10


NAME_OF_DB = 'marche_db'


kmdmarche_shop_table_definition = [
    ["timestamp", "INTEGER"],
    ["name", "TEXT"],
    ["item", "TEXT"],
]

IDX_TIMESTAMP = 0
IDX_NAME      = 1
IDX_ITEM      = 2


domain_id = bbclib.get_new_id("payment_test_domain", include_timestamp=False)


class Store:

    def __init__(self):
        self.db = Database()
        self.db.setup_db(domain_id, NAME_OF_DB)


    def close(self):
        self.db.close_db(domain_id, NAME_OF_DB)


    def get_shop_item(self, name):
        rows = self.db.exec_sql(
            domain_id,
            NAME_OF_DB,
            'select item from shop_table where name=? and timestamp>=? ' + \
            'order by rowid desc',
            name,
            BASE_TIME
        )
        if len(rows) <= 0:
            return None
        return rows[0][0]


    def get_shop_list(self, count=None):
        if count is not None:
            s_limit = ' limit {0}'.format(count)
        else:
            s_limit = ''

        rows = self.db.exec_sql(
            domain_id,
            NAME_OF_DB,
            'select * from shop_table where timestamp>=?' + \
            'order by rowid desc' + s_limit,
            BASE_TIME
        )

        dics = []
        for row in rows:
            dics.append({
                'timestamp': row[IDX_TIMESTAMP],
                'name': row[IDX_NAME],
                'item': row[IDX_ITEM]
            })

        return dics

    def setup(self):
        self.db.create_table_in_db(domain_id, NAME_OF_DB, 'shop_table',
                kmdmarche_shop_table_definition)

    def write_shop(self, timestamp, name, item):
        self.db.exec_sql(
            domain_id,
            NAME_OF_DB,
            'insert into shop_table values (?, ?, ?)',
            timestamp,
            name,
            item
        )


def get_balance(name, user_id):
    r = requests.get(PREFIX_API + '/api/status/' + user_id,
            params={'mint_id': MINT_ID})
    res = r.json()

    if r.status_code != 200:
        return render_template('kmdmarche/error.html',
                message=res['error']['message'])

    to_name = request.args.get('to_name')

    store = Store()
    store.setup()
    item = store.get_shop_item(to_name)
    store.close()

    return render_template('kmdmarche/sokin.html', name=name, user_id=user_id,
            balance=res['balance'], symbol=res['symbol'],
            to_name=to_name, item=item, sending=request.method=='GET')


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


def reform_list(txs):
    for tx in txs:
        t = datetime.datetime.fromtimestamp(tx['timestamp'])
        tx['timestamp'] = t.strftime("%H:%M")
        if len(tx['from_name']) <= 0:
            tx['from_name'] = 'Cocotano'
            tx['label'] = '*** JOINED ***'


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

    r = requests.get(PREFIX_API + '/api/user', params={'name': name})
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
    item = request.form.get('item')

    if to_name is None or len(to_name) <= 0:
        return render_template('kmdmarche/error.html',
                message='to_name is missing')

    if amount is None or len(amount) <= 0:
        return render_template('kmdmarche/error.html',
                message='amount is missing')

    r = requests.get(PREFIX_API + '/api/user', params={'name': to_name})
    res = r.json()

    if r.status_code != 200:
        return render_template('kmdmarche/error.html',
                message=res['error']['message'])

    to_user_id = res['user_id']

    r = requests.post(PREFIX_API + '/api/transfer/' + MINT_ID, data={
        'from_user_id': user_id,
        'to_user_id': to_user_id,
        'amount': amount,
        'label': item
    })

    if r.status_code != 200:
        return render_template('kmdmarche/error.html',
                message=res['error']['message'])

    return get_balance(name, user_id)


@kmdmarche.route("/sokin_later")
def sokin_later():

    return render_template("kmd/marche/sokin_later.html")

# shop registration
@kmdmarche.route("/shopowner", methods=['GET'])
def shopowner():
    if 'user_id' not in session:
        now = datetime.datetime.now()
        timeString = now.strftime('%H:%M')

        return render_template('kmdmarche/register.html',
                title_name=title_name, time=timeString)

    menu_name = "Register a shop!"
    info = ""
    now = datetime.datetime.now()
    timeString = now.strftime("%H:%M")
    return render_template("kmdmarche/shopowner.html", menu_name = menu_name,
            title_name = title_name, info = info, time=timeString)


@kmdmarche.route("/shopowner", methods=['POST'])
def shopowner_later():
    if 'user_id' not in session:
        now = datetime.datetime.now()
        timeString = now.strftime('%H:%M')

        return render_template('kmdmarche/register.html',
                title_name=title_name, time=timeString)

    name = session['name']

    item = request.form.get('a')

    if item is None or len(item) <= 0:
        return render_template('kmdmarche/error.html',
                message='item is missing')

    store = Store()
    store.setup()
    store.write_shop(int(time.time()), name, item)
    store.close()

    return render_template("kmdmarche/shopowner_later.html")


# list of transactions
@kmdmarche.route("/tx")
def tx():
    menu_name = "Transactions"
    info = "Your transaction will be listed bellow"
    now = datetime.datetime.now()
    timeString = now.strftime("%H:%M")

    offset = request.args.get('offset')

    if offset is None:
        offset = 0

    r = requests.get(PREFIX_API + '/api/transactions/' + MINT_ID, params={
        'basetime': BASE_TIME,
        'count': LIST_COUNT,
        'offset': offset,
    })
    res = r.json()

    reform_list(res['transactions'])

    return render_template("kmdmarche/tx.html", menu_name = menu_name,
            title_name = title_name, info = info, time=timeString,
            transactions=res['transactions'], count=LIST_COUNT,
            count_before=res['count_before'], count_after=res['count_after'])


# list of shops
@kmdmarche.route("/ownerlist")
def ownerlist():
    if 'user_id' not in session:
        now = datetime.datetime.now()
        timeString = now.strftime('%H:%M')

        return render_template('kmdmarche/register.html',
                title_name=title_name, time=timeString)

    name = session['name']

    menu_name = "Recommend Shop"
    info = "Show in Time Order"
    now = datetime.datetime.now()
    timeString = now.strftime("%H:%M")

    store = Store()
    store.setup()
    shops = store.get_shop_list(5)
    store.close()

    for shop in shops:
        t = datetime.datetime.fromtimestamp(shop['timestamp'])
        shop['timestamp'] = t.strftime("%H:%M")

    return render_template("kmdmarche/ownerlist.html", menu_name=menu_name,
            title_name=title_name, info=info, time=timeString, name=name,
            shops=shops)


@kmdmarche.route('/mypage')
def mypage():
    if 'user_id' not in session:
        now = datetime.datetime.now()
        timeString = now.strftime('%H:%M')

        return render_template('kmdmarche/register.html',
                title_name=title_name, time=timeString)

    name = session['name']
    user_id = session['user_id']

    r = requests.get(PREFIX_API + '/api/status/' + user_id,
            params={'mint_id': MINT_ID})
    res = r.json()

    if r.status_code != 200:
        return render_template('kmdmarche/error.html',
                message=res['error']['message'])

    balance=res['balance']
    symbol=res['symbol']

    r = requests.get(PREFIX_API + '/api/transactions/' + MINT_ID, params={
        'name': name,
        'basetime': BASE_TIME,
    })
    res = r.json()

    reform_list(res['transactions'])

    spendcoin = 0
    getcoin = 0

    for tx in res['transactions']:
        if tx['to_name'] == name:
            getcoin += int(tx['amount'])
        else:
            spendcoin += int(tx['amount'])

    menu_name = "My Page"
    now = datetime.datetime.now()
    timeString = now.strftime("%H:%M")
    return render_template("kmdmarche/mypage.html", menu_name="",
        title_name="", name=name, balance=balance, symbol=symbol,
        time=timeString, spendcoin=spendcoin, getcoin=getcoin,
        transactions=res['transactions'])


# end of app.py
