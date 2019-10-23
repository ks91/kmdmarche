from flask import Flask, render_template, Response,request,redirect,url_for

import datetime
from PIL import Image
import qrcode  as qr
import base64
from io import BytesIO

app = Flask(__name__)
title_name="ここたのマルシェ"

# ここたのトップ
@app.route("/")
def login():
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")


    return render_template("login.html", title_name = title_name, time=timeString)

# ここたのトップ
@app.route("/top", methods=['POST','GET'])
def toppage():
    name = request.form['username']
    return render_template("top.html", name = name)

@app.route("/pay0")
def pay0():
    menu_name = "支払うためのQRコードを発行します"
    info = "ニックネームを入れてくださいな"
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    return render_template("pay.html", menu_name = menu_name, time=timeString, info = info)
# 支払い画面
@app.route("/pay", methods=['POST','GET'])
def pay():
    menu_name = "支払うためのQRコードを発行します"
    info = "下記のQRコードをお客さんに見せてください"
    code_input = request.form['code']
    # code_input = "hogehogehoge"
    qr_b64data = qrmaker(str(code_input))
    ts = datetime.datetime.now()
    qr_name = "qrcode_image_{}".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
    return render_template("pay2.html",
        data=code_input,
        qr_b64data=qr_b64data,
        qr_name=qr_name
    )
    # code_input = request.form['code']
    # fig_url = QRmaker(code_input)
    # qr_img = qr.make(str('aaaaa'))
    # qr_img.show()

    # return render_template("pay2.html", data=code_input,fig=fig_url)

# retry and quit
@app.route('/event', methods=['GET'] )
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

    # 画像書き込み用バッファを確保して画像データをそこに書き込む
    buf = BytesIO()
    qr_img.save(buf,format="png")

    # バイナリデータをbase64でエンコードし、それをさらにutf-8でデコードしておく
    qr_b64str = base64.b64encode(buf.getvalue()).decode("utf-8")

    # image要素のsrc属性に埋め込めこむために、適切に付帯情報を付与する
    qr_b64data = "data:image/png;base64,{}".format(qr_b64str)

    return qr_b64data
    # qr_img = qr.make(str('code')) #codeの文字をQRコードに変換
    # qr_img.show() #生成したQRコードを表示
    # ts = datetime.datetime.now()  # grab the current timestamp
    # # construct filename
    #
    # filename = "./static/qrcode_image/{}.png".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
    # qr_img.save(filename)
    # return filename
# @app.route("/qrcode", methods=["GET"])
# def get_qrcode():
#     # please get /qrcode?data=<qrcode_data>
#     data = request.args.get("data", "")
#     return send_file(qrcode(data, mode="raw"), mimetype="image/png")
@app.route("/sokin")
def sokin():
    menu_name = "『まなぶさん』に送金しますか？"
    info = "送金額を入力してください"

    return render_template("sokin.html", menu_name = menu_name, title_name = title_name, info = info)

@app.route("/sokin_later")
def sokin_later():
    menu_name = "『まなぶさん』に送金しました"
    info = "引き続きお楽しみください！"

    return render_template("sokin_later.html", menu_name = menu_name, title_name = title_name, info = info)


# 出店者登録
@app.route("/shopowner")
def shopowner():
    menu_name = "出店者登録をします"
    info = "出店者登録は簡単！"
    return render_template("shopowner.html", menu_name = menu_name, title_name = title_name, info = info)

# TX一覧
@app.route("/tx")
def tx():
    menu_name = "TX一覧を表示します"
    info = "あなたの交換は、下記をチェック"
    return render_template("tx.html", menu_name = menu_name, title_name = title_name, info = info)

# 出店者一覧
@app.route("/ownerlist")
def ownerlist():
    menu_name = "今、おすすめの出店者はこちら"
    info = "更新順に表示しています"
    return render_template("ownerlist.html", menu_name = menu_name, title_name = title_name, info = info)

@app.route("/mypage")
def mypage():
    menu_name = "マイページです"
    info = "あなたの今のコインは24コイン"
    return render_template("mypage.html", menu_name = menu_name, title_name = title_name, info = info)



if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=80)
