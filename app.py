from flask import Flask , render_template ,request ,redirect ,session , flash
from mysql import Mysql
# from data import Articles (데이터 mysql로 관리하여 불필요)
from loginapi import naver_login, kakao_login
import config
import pymysql
from datetime import timedelta
# print(Articles())
from functools import wraps
from flask_mail import Mail, Message
from random import randint
# import ctypes
# from plyer import notification1
import requests
import urllib
from werkzeug.utils import secure_filename
from PIL import Image
import os


app = Flask(__name__)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=1000)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] ='123'

#0828
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 000
app.config['MAIL_USERNAME'] = '0000@gmail.com'
app.config['MAIL_PASSWORD'] = '0000'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


app.config['UPLOAD_FOLDER'] = './static/images/test_images'


mysql = Mysql(password="")

def is_loged_in(func):
    @wraps(func)
    def wrap(*args , **kwargs):
        if 'is_loged_in' in session:
            return func(*args , **kwargs)
        else:
            return redirect('/loginst')
    return wrap

@app.route('/' , methods=['GET','POST'])
# @is_loged_in
def index():
    if request.method == "GET":
        os_info = dict(request.headers)
        print(os_info)
        name = request.args.get("name")
        print(name)
        hello = request.args.get("hello")
        print(hello)
        return render_template('indexst.html',header=f'{name}님 {hello}!!' )

    elif request.method == "POST":
        data  = request.form.get("name")
        data_2 = request.form['hello']
        print(data_2)
        return render_template('indexst.html')
    print(session['is_loged_in'])
    return render_template('indexst.html')

@app.route('/registerst', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        number = request.form.get('number')
        phone = request.form.get('phone')
        password = request.form.get('password')
        print(username , email , phone , password)

        db = pymysql.connect(host=mysql.host, user=mysql.user, db=mysql.db, password=mysql.password, charset=mysql.charset)
        curs = db.cursor()

        sql = f'SELECT * FROM user WHERE email = %s;'
        curs.execute(sql , email)

        rows = curs.fetchall()
        print(rows)

        user_otp = session['user_otp']
        user_email = session['user_email']

        if rows:
            flash("이미 가입된 회원입니다.")
            # ctypes.windll.user32.MessageBoxW(0, "이미 가입된 회원입니다.", "알림", 48)
            # notification.notify(
            #     title = 'testing',
            #     message = 'message',
            #     app_icon = None,
            #     timeout = 10,)
            return render_template('registerst.html')

        elif user_otp!=number or user_email!=email:
             flash("인증번호가 일치하지 않습니다")
             return redirect('/registerst')

        else:
            result = mysql.insert_user(username, email ,phone,password )
            flash("회원가입이 완료되었습니다.")
            print(result)
            return redirect('/loginst')

    elif request.method == "GET":
        return render_template('registerst.html')

@app.route('/loginst',  methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template('loginst.html')
    elif request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        db = pymysql.connect(host=mysql.host, user=mysql.user, db=mysql.db, password=mysql.password, charset=mysql.charset)
        curs = db.cursor()

        sql = f'SELECT * FROM user WHERE email = %s;'
        curs.execute(sql , email)

        rows = curs.fetchall()
        print(rows)

        if rows:
            result = mysql.verify_password(password, rows[0][3])
            if result:
                session['is_loged_in'] = True
                session['username'] = rows[0][0]
                session['email'] = rows[0][1]
                session['phone'] = rows[0][2]
                session['password'] = rows[0][3]
                return redirect('/')
                # return render_template('index.html', is_loged_in = session['is_loged_in'] , username=session['username'] )
            else:
                flash("회원정보가 틀립니다.")
                # ctypes.windll.user32.MessageBoxW(0, "회원정보가 틀립니다.", "알림", 16)
                return redirect('/loginst')
        else:
            flash("회원정보가 틀립니다.")
            return render_template('loginst.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route("/email", methods=['GET', 'POST'])
def send_email():
    if request.method == 'GET':
        return render_template('email.html')

    elif request.method == 'POST':
        user_mail = request.form['usermail']
        db = pymysql.connect(host=mysql.host, user=mysql.user, db=mysql.db, password=mysql.password, charset=mysql.charset)
        curs = db.cursor()
        sql = f'SELECT * FROM user WHERE email = %s;'
        curs.execute(sql , user_mail)
        rows = curs.fetchall()
        if rows:
           flash("이미 가입된 이메일주소입니다.")
           return redirect('/email')
        else:
            otp = str(randint(100000, 999999))
            session['user_otp'] = otp  # 세션에 인증번호 저장
            usermail = request.form['usermail']
            session['user_email'] = usermail
            msg = Message('studioPD 이메일 인증', sender=config.MAIL_USERNAME, recipients=[usermail])
            msg.body = '안녕하세요. studioPD 입니다.\n인증번호를 입력하여 이메일 인증을 완료해 주세요.\n인증번호 : {}'.format(otp)
            mail.send(msg)
            flash("인증번호를 발송하였습니다")
            return redirect('/registerst')
# 유저 비밀번호 변경 요청
@app.route("/change_password", methods=['GET', 'POST'])
def change_password():
    if request.method == 'GET':
        return render_template('change_password.html')
    if request.method == 'POST':
        user_mail = request.form['user_mail']
        db = pymysql.connect(host=mysql.host, user=mysql.user, db=mysql.db, password=mysql.password, charset=mysql.charset)
        curs = db.cursor()
        sql = f'SELECT * FROM user WHERE email = %s;'
        curs.execute(sql , user_mail)
        rows = curs.fetchall()
        if rows:
            otp = str(randint(100000, 999999))
            session['user_otp'] = otp  # 세션에 인증번호 저장
            session['user_email'] = user_mail
            msg = Message('studioPD 이메일 인증', sender=config.MAIL_USERNAME, recipients=[user_mail])
            msg.body = '안녕하세요. studioPD 입니다.\n인증번호를 입력하여 이메일 인증을 완료해 주세요.\n인증번호 : {}'.format(otp)
            mail.send(msg)
            flash("인증번호를 발송하였습니다")
            return redirect('/update')
        else:
            flash("가입되지 않은 이메일주소입니다.")
            return redirect('/change_password')

# 유저 비밀번호 변경 창으로 이동
@app.route("/update", methods=['GET', 'POST'])
def change():
    if request.method == 'GET':
        return render_template('update.html')
    if request.method == 'POST':
        email = request.form.get('email')
        number = request.form.get('number')
        password = request.form.get('password')
        user_otp = session['user_otp']
        user_email = session['user_email']
        if user_email==email and user_otp==number:
           result = mysql.update_user(password, email)
           flash("비밀번호 변경완료! 다시 로그인해주세요.")
           print(result)
           return redirect('/loginst')
        else:
            flash("인증번호가 일치하지 않습니다.")
            return redirect('/update')

@app.route('/lists', methods=['GET' , 'POST'])
def lists():
    if request.method == "GET":
        result = mysql.get_data()
        print(result)
        return render_template('lists.html', data=result)

    elif request.method =="POST":
        title = request.form['title']
        cont = request.form['cont']
        author = request.form['author']
        result = mysql.insert_list(title , cont , author)
        print(result)
        return redirect('/lists')

@app.route('/create_list')
def create_list():
    return render_template('dashboard.html')

@app.route('/view/<ids>',methods=['GET','POST'])
def view(ids):
    if request.method == 'GET':
        db = pymysql.connect(host=mysql.host, user=mysql.user, db=mysql.db, password=mysql.password, charset=mysql.charset)
        curs = db.cursor()

        sql = f'SELECT * FROM posts WHERE `id` = %s;'
        curs.execute(sql , ids)

        rows = curs.fetchall()
        print(rows)
        db.close()
        return render_template('view.html',data = rows)

    elif request.method == 'POST':
        ids =request.form['ids']
        title = request.form['title']
        cont = request.form['cont']
        author = request.form['author']

        result = mysql.update_list(ids,title,cont,author)
        print(result)
        return redirect('/lists')

@app.route('/edit/<ids>',methods=['GET','POST'])
def edit(ids):
    print(ids)
    if request.method == 'GET':
        db = pymysql.connect(host=mysql.host, user=mysql.user, db=mysql.db, password=mysql.password, charset=mysql.charset)
        curs = db.cursor()

        sql = f'SELECT * FROM posts WHERE `id` = %s;'
        curs.execute(sql , ids)

        rows = curs.fetchall()
        print(rows)
        # db.close()
        return render_template('list_edit.html',data = rows)

    elif request.method == 'POST':
        ids = request.form['ids']
        title = request.form['title']
        cont = request.form['cont']
        author = request.form['author']
        print(ids)

        result = mysql.update_list(ids,title,cont,author)
        print(result)
        return redirect('/lists')


# @app.route('/sub' , methods=['GET','POST'])
# def sub():
#     if request.method == 'GET':
#         datas = mysql.Articles()
#         # print(data)
#         result = mysql.get_review_star()
#         print(result)
#         return render_template('sub.html', data = datas, data2 = result)

@app.route('/sub' , methods=['GET','POST'])
def sub():
    if request.method == 'GET':
        datas = mysql.star()
        print(datas)
        print('======================************')

        for i in datas:
            if i['reviewStar'] == None:
                i['reviewStar'] = 0

            else:
                i['reviewStar'] = i['reviewStar']
        print(datas)        

        return render_template('sub.html', data = datas)

# 상세페이지 이동 / 예약 기능 구현중

# @app.route('/detail/<id>',  methods=['GET', 'POST'])
# def detail(id):
#     # Check if the user is_loged_in
#     # Continue with the original code
#     if request.method == "GET":
#         result = mysql.Articles()
#         id = int(id)
#         result = result[id]
#         result2= mysql.get_reservation(id)
#         result3 = mysql.get_review_star()

#         # result3({스튜디오아이디 : 평균별점, ...})에 id값이 없을 경우
#         if result3.get(id) == None:
#             result3 = '등록된 리뷰가 없습니다'

#         # result3에 id값이 있을 경우 id를 '키'값으로 하는 '밸류'값 전달
#         else:
#             result3 = result3.get(id)

#         return render_template('detail.html', data=result, data2=result2, data3=result3)


#     elif request.method == "POST":
#         if not session.get('is_loged_in'):
#                 # Redirect the user to the login page
#                 return redirect('/loginst')
#         else:
#             result = mysql.Articles()
#             id = int(id)
#             result = result[id]
#             studio_id = request.form.get('ids')
#             studio_name = request.form.get('name')
#             studio_date = request.form.get('reservation')
#             email = session['email']
#             result2= mysql.get_reservation(id)
#             check_result = mysql.insert_reservation(studio_id, studio_name, studio_date, email)
#             flash("예약완료")
#             return redirect(f'/detail/{id}')


# 10/17 수정됨. 리뷰 사진 가져오기.
@app.route('/detail/<id>',  methods=['GET', 'POST'])
def detail(id):
    # Check if the user is_loged_in
    # Continue with the original code
    if request.method == "GET":
        result = mysql.star()
        print(result)
        id = int(id)
        print(result[0]['studio_id'])

        for i in result:
            if i['studio_id'] == id:
                print(i)
                if i['reviewStar'] == None:
                    i['reviewStar'] = 0
                result = i

        print(id)
        # result = result[id]
        print(result)
        result2= mysql.get_reservation(id)
        result3, result4 = mysql.get_review_star()
        print(result)
        print(result2)
        print(result3)
        print(result4)
        print('====***====')        
        # reivew_list = [] 
        # star_list = [] 
        # for result4_data in result4:
        #     if result4_data['studio_id'] == id:
        #        reivew_list.append(result4_data['review'])
        #        star_list.append(result4_data['reviewStar'])
        # #        print(result4_data['studio_id'])
        # #        print(result4_data['review'])     
        # #        print(result4_data['reviewStar'])
        # # print(reivew_list)
        # # print(star_list)
        # result5 = dict(zip(reivew_list, star_list))
        # print(result5)         
        reivew_list = [] 
        for result4_data in result4:
            if result4_data['studio_id'] == id:
                
                if result4_data['reivew_image'] == None:
                   result4_data['reivew_image'] =  '/static/images/test_images/1.PNG'                   
                   reivew_list.append(result4_data)
                   
                else:
                    reivew_list.append(result4_data)                   
        print(reivew_list)


            #    reivew_list.append(result4_data['reviewStar'])
            #    reivew_list.append(result4_data['reivew_image'])
        #        print(result4_data['studio_id'])
        #        print(result4_data['review'])     
        #        print(result4_data['reviewStar'])
        # print(reivew_list)
        # print(star_list)
        # result5 = dict(zip(reivew_list, star_list))
        print(reivew_list)

        # result3({스튜디오아이디 : 평균별점, ...})에 id값이 없을 경우
        if result3.get(id) == None:
            result3 = '등록된 리뷰가 없습니다'

        # result3에 id값이 있을 경우 id를 '키'값으로 하는 '밸류'값 전달
        else:
            result3 = result3.get(id)

        return render_template('detail.html', data=result, data2=result2, data3=result3, data4 = reivew_list)


    elif request.method == "POST":
        if not session.get('is_loged_in'):
                # Redirect the user to the login page
                return redirect('/loginst')
        else:
            result = mysql.star()
            id = int(id)
            for i in result:
                if i['studio_id'] == id:
                    print(i)
                    result = i
            studio_id = request.form.get('ids')
            studio_name = request.form.get('name')
            studio_date = request.form.get('reservation')
            email = session['email']
            result2= mysql.get_reservation(id)
            check_result = mysql.insert_reservation(studio_id, studio_name, studio_date, email)
            flash("예약완료")
            return redirect(f'/detail/{id}')        






@app.route('/change_email', methods=['GET'])
def change_email():
    return render_template('change_email.html')


@app.route("/update_email", methods=["POST"])
def update_email():
    username = request.form["username"]
    new_email = request.form["new_email"]
    phone = request.form["phone"]
    print('뽀뽀잉')
    db = pymysql.connect(host=mysql.host, user=mysql.user, db=mysql.db, password=mysql.password, charset=mysql.charset)
    curs = db.cursor()

    # email을 업데이트
    # sql = "UPDATE user SET email=%s WHERE username=%s"
    # curs.execute(sql, (new_email, username))
    # result = mysql.updates_user(new_email, username)
    result = mysql.updates_user( new_email,phone,username)
    db.close()
    print(new_email)
    print(username)
    # session['email'] = request.form["new_email"]
    session['phone'] = request.form["phone"]
    return redirect('/')

# 스튜디오 예약 취소 (수정됨)
@app.route('/myreservation',  methods=['GET', 'POST'])
def myreservation():
    if request.method == "GET":
        email = session['email']
        result = mysql.cancel_reservation(email)
        print(result)
        return render_template('myreservation.html', data=result)

    if request.method == "POST":
    #  request.form.getlist 는 다중 name값을 리스트형태로 저장해줌.
    #  체크박스 한개만 선택해도 리스트 형식으로 전달됨
    #  cancel_number = request.form.get("number") : 변경 전
       cancel_number = request.form.getlist("number")
       print("============================")
       print(cancel_number)
    # mysql.delete_reservation에 리스트 형태로 값을 전달
       result = mysql.delete_reservation(cancel_number)
       print(result)
       return redirect('/myreservation')

# 유저 가입정보 확인 및 비밀번호 변경
@app.route('/info',  methods=['GET', 'POST'])
def info():
    if request.method == "GET":
        return render_template('info.html')

    if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            result = mysql.update_user(password, email)
            flash("비밀번호 변경완료! 다시 로그인해주세요.")
            print(result)
            return redirect('/loginst')
            # result = mysql.info_change(username, email, number, password)
            # print(result)






@app.route('/studio_business', methods=['GET', 'POST'])
def studio_business():
    if request.method == 'GET':
#     #승인키(90일 사용가능) :  devU01TX0FVVEgyMDIzMDkyODE3MjAwOTExNDEzNjI=
#         url = "https://business.juso.go.kr/addrlink/addrLinkUrl.do"
        return render_template('studio_business.html')
 
#         _params = {
#             'confmKey' : 'devU01TX0FVVEgyMDIzMDkyODE3MjAwOTExNDEzNjI=',
#             'returnUrl' : 'http://localhost:5000/studio_business'
#         }
    if request.method == 'POST':

#         response = requests.get(url, params=_params)
#         print(response.content)
        return render_template('studio_business.html')
    


#  10.19수정(리뷰작성 팝업창에 사진첨부기능 추가 / 팝업창 서브밋 후 창닫고 부모창 리로드)
@app.route('/popup/<date>/<name>/<number>/<id>', methods=['GET', 'POST'])
def popup(date, name, number, id):
    if request.method == 'GET':
        result1 = date
        result2 = name
        result3 = number
        result4 = id
        return render_template('popup.html', data1 = result1, data2 = result2, data3 = result3, data4 = result4)
 
    if request.method == 'POST':
        number = request.form.get('number')
        studio_name = request.form.get('studio_name')
        review = request.form.get('review')
        reviewStar = request.form.get('reviewStar')
        studio_id = request.form.get('studio_id')
        user_id = session['email']
        print(user_id)
        print(number)
        print(studio_name)
        print(review)
        print(reviewStar)
        print(studio_id)

        # reivew_image 초기값을 None으로 설정
        reivew_image = None

        if 'reivew_image' in request.files:
            f1 = request.files['reivew_image']
            if f1.filename == "":
                reivew_image = None
            else:
                filename_1 = secure_filename(f1.filename)
                f1.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_1))
                print(filename_1)
                reivew_image = "/static/images/test_images/" + filename_1

        # 리뷰 등록
        result1 = mysql.insert_review(number, studio_name, review, reviewStar, studio_id, reivew_image, user_id)
        result2 = mysql.delete_reservation(number)

    # 자식창 닫고 원래 페이지를 리로드하는 스크립트를 HTML 문자열로 반환
    response = """
    <script>
        window.opener.location.reload();
        window.close();
    </script>
    """
    return response



@app.route('/review_list', methods=['GET', 'POST'])
def review_list():
    if request.method == 'GET':
        result = mysql.star()
        return render_template('review_list.html')







# 파일 전송 테스트

# 파일을 전송받으려면 아래와 같이 import 해야함
# from werkzeug.utils import secure_filename
# import os

@app.route('/test_studio', methods=['GET', 'POST'])
def test_studio():
    if request.method == 'GET':
        return render_template('test_studio.html')

    if request.method == 'POST':
        # 스튜디오명 가져오기
        studio_name = request.form["studio_name"]
        # 스튜디오 기본 주소(검색된 주소) 가져오기
        studio_addr = request.form["studio_addr"]
        # 스튜디오 상제 주소(직접 입력한 주소) 가져오기
        studio_addr_detail = request.form["studio_addr_detail"]
        # 스튜디오 지도 위치 가져오기
        studio_loc = request.form["studio_loc"]
        # 스튜디오 유형 가져오기. 여러개의 값을 한번에 받을 수 있도록
        # getlist로 동일한 name의 값을 리스트형태로 전달받음
        check_box = request.form.getlist("check_box")
        # 스튜디오 가격
        studio_price = request.form["studio_price"]
        # print(studio_name)    
        # print(studio_addr)    
        # print(studio_addr_detail)    
        # print(studio_loc)    
        # print(check_box)    
        # print(studio_price)

        # 스튜디오 기본 주소(검색된 주소)중 앞의 두글자만 따로 저장
        # 예) 경기도 파주시 : 경기
        studio_addr_1 = studio_addr[0:2]
        # print(studio_addr_1)

        # 스튜디오 기본 주소(검색된 주소)를 공백을 기준으로 스플릿(구분).
        # 예) 경기 광주시 오포읍 : ['경기', '광주시', '오포읍']
        studio_addr_2 = studio_addr.split(" ")
        # 구분된 데이터 ['경기', '광주시', '오포읍']에서 인덱스 1번째('광주시')문자 중
        #  앞의 두글자(광주)만 저장
        studio_addr_2 = studio_addr_2[1][0:2]
        print(studio_addr_2)

        # 검색주소에 공백(" ")한칸 주고 상세주소를 합친 후 저장
        # 예) '경기 파주시 가나무로 93'과'00빌딩 2층'을 '경기 파주시 가나무로 93 00빌딩 2층'으로
        studio_addr_last  = studio_addr + " "+ studio_addr_detail
        print(studio_addr_last)

        # 이미지 파일을 전달 받음
        f1 = request.files['file_1']
        f2 = request.files['file_2']
        f3 = request.files['file_3']

        # 전달받은 파일의 이름이 안전한지 secure_filename()함수로 확인
        # secure_filename()은 werkzeug프레임워크의 내장함수.
        filename_1 = secure_filename(f1.filename) 
        filename_2 = secure_filename(f2.filename)
        filename_3 = secure_filename(f3.filename)


        # 이미지 파일을 저장. 
        # app.config['UPLOAD_FOLDER']에 미리 저장경로를 저장하면
        # app.config['UPLOAD_FOLDER'] = './static/images/test_images'
        # 해당 경로에 이미지를 저장할 수 있음. 경로설정 안하면 app.py가 위치한 경로 또는 폴더에
        # 이미지가 저장됨.
        f1.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_1))
        f2.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_2))
        f3.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_3))
        # print(filename_1)
        # print(filename_2)
        # print(filename_3)


        #  아래와 같은 형태로 저장하기 위해 빈 리스트에  
        # 이미지가 저장 되어있는 경로와 이미지명을 합친 후 넣어줌.

        # ["/static/images/gwangju/timroad_inside2.PNG", 
        # "/static/images/gwangju/timroad_inside2.PNG", 
        # "/static/images/gwangju/timroad_inside2.PNG"]

        studio_img = []
        filename_1 = "/static/images/test_images/" + filename_1
        filename_2 = "/static/images/test_images/" + filename_2
        filename_3 = "/static/images/test_images/" + filename_3
        studio_img.append(filename_1)
        studio_img.append(filename_2)
        studio_img.append(filename_3)
        # print(filename_1)
        # print(filename_2)
        # print(filename_3)
        # print(studio_img)
        result = mysql.tempo_insert_studio(studio_name, studio_addr_1, studio_addr_2, studio_addr_last,
                                            check_box, studio_price, studio_loc, studio_img)

        print(result)
        return redirect('/test_studio')



@app.route('/master' , methods=['POST','GET'])
def master():
    if request.method == "GET":
        return render_template('master.html')
    


# 승인대기중인 스튜디오 목록 처리
@app.route('/studio_check' , methods=['POST','GET'])
def studio_check():
    if request.method == "GET":

        # 승인대기중인 스튜디오 목록 (tempo_studio_lists 테이블)을 가져옴.
        result = mysql.check_studio()
        print(result)
        return render_template('studio_check.html', data = result)   
 

    # 승인대기중인 스튜디오 목록 (tempo_studio_lists 테이블)을 가져옴.
    if request.method == "POST":

        # accept(승인)또는 cancel(취소) 정보를 가져옴.
        # submit버튼 두개가 name은 같지만 value값이 서로 다르기에
        # 어떤 값을 보내더라도 받을 수 있도록 getlist사용. 
        print('***')
        check = request.form.getlist("check")
        # check = request.form["check"]
        print(check)

        # 체크박스 체크 후 전달 받을 때 스튜디오id를 전달받음.
        # 여러개의 id값도 받을 수 있도록 getlist 사용.
        studio_id = request.form.getlist("studio_id")
        # print(studio_id)
        # print('hihi')

        # value값이 accept(승인)일 경우  mysql.accept_studio()함수 실행
        if check == ['accept']:
            # print('yes')
            result = mysql.accept_studio(studio_id)

        # value값이 accept(승인)이 아닐 경우(cancel일 경우)  mysql.cancel_studio()함수 실행
        else:
            # print('no')
            result = mysql.cancel_studio(studio_id)

        return redirect('/studio_check')
    

app.register_blueprint(naver_login.bp)
app.register_blueprint(kakao_login.bp)


if __name__ == '__main__':
    app.run(debug=True)