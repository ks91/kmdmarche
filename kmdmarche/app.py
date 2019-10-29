from flask import Blueprint, render_template, request, session, redirect, url_for

import datetime
from PIL import Image
import qrcode  as qr
import base64
from io import BytesIO

# Prior to use this web application, please define a currency using API,
# and put the mint_id here.
MINT_ID = 'e6500c9aefa1dddb4295dcfa102e574497dfa83baefa117b9f34f654606f876f'

# Put the initial amount when signed up
INIT_AMOUNT = '30'

# Put API host name here.
PREFIX_API = 'http://127.0.0.1:5000'


kmdmarche = Blueprint('kmdmarche', __name__, template_folder='templates',
        static_folder='./static')
title_name="CocoTano Marche"

@kmdmarche.route("/", methods=['POST','GET'])
def login():
    now = datetime.datetime.now()
    # timeString = now.strftime("%Y-%m-%d %H:%M")
    timeString = now.strftime("%H:%M")

    return render_template("kmdmarche/login.html", title_name = title_name, time=timeString)

# cocotano top
@kmdmarche.route("/top", methods=['POST','GET'])
def toppage():
    name = request.form['username']
    return render_template("kmdmarche/top.html", name = name)

@kmdmarche.route("/pay0")
def pay0():
    menu_name = ""
    info = ""
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    return render_template("kmdmarche/pay.html", menu_name = menu_name, time=timeString, info = info)

# payment
@kmdmarche.route("/pay", methods=['POST','GET'])
def pay():
    menu_name = "Cocotano Marche"
    info = ""
    code_input = request.form['code']
    # code_input = "hogehogehoge"
    qr_b64data = qrmaker(str(code_input))
    ts = datetime.datetime.now()
    qr_name = "qrcode_image_{}".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
    return render_template("kmdmarche/pay2.html",
        data=code_input,
        qr_b64data=qr_b64data,
        qr_name=qr_name,
        menu_name=menu_name,
        info=info
    )
    # code_input = request.form['code']
    # fig_url = QRmaker(code_input)
    # qr_img = qr.make(str('aaaaa'))
    # qr_img.show()

    # return render_template("kmdmarche/pay2.html", data=code_input,fig=fig_url)

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

def qrmaker(code):
    qr_img = qr.make(str(code))

    # allocate buffer and write the image there
    buf = BytesIO()
    qr_img.save(buf,format="png")

    # encode the binary data into base64 and decode with UTF-8
    qr_b64str = base64.b64encode(buf.getvalue()).decode("utf-8")

    # to embed it as src attribute of image element
    qr_b64data = "data:image/png;base64,{}".format(qr_b64str)

    return qr_b64data

@kmdmarche.route("/sokin")
def sokin():
    who = "BOB"
    info = "Enter the amount to transfer"

    return render_template("kmdmarche/sokin.html", who = who, title_name = title_name, info = info)

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

@kmdmarche.route("/mypage")
def mypage():
    menu_name = "My Page"
    info = "24"
    spendcoin = "56"
    getcoin = "9"
    now = datetime.datetime.now()
    timeString = now.strftime("%H:%M")
    return render_template("kmdmarche/mypage.html", menu_name = menu_name, title_name = title_name, info = info, time=timeString, spendcoin = spendcoin, getcoin = getcoin)

# end of app.py
