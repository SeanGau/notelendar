from flask import Flask, g, request, render_template, session, redirect, url_for, jsonify, abort, send_from_directory
from sassutils.wsgi import SassMiddleware
from dateutil.relativedelta import relativedelta
import sqlite3, json, hashlib, datetime, pytz, shutil, calendar, os, locale, csv, requests
        
app = Flask(__name__)
app.config.from_pyfile('config.py', silent=True)
app.wsgi_app = SassMiddleware(app.wsgi_app, {'notelendar': ('static/sass', 'static/css', '/static/css', True)})
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')
locale.setlocale(locale.LC_ALL, "zh_TW.UTF-8")
print("sqlite:", sqlite3.sqlite_version)

holidayCalendar = {}
with open("./notelendar/static/assets/112年中華民國政府行政機關辦公日曆表.csv", encoding="utf-8-sig") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        dateString = datetime.datetime.strptime(row['西元日期'], "%Y%m%d").strftime("%Y-%m-%d")
        holidayCalendar[dateString] = {
            "isHoliday": True if row['是否放假'] == '2' else False,
            "what": row['備註']
        }

def sha_hash(str):
    str += app.config['SALT']
    return hashlib.sha3_224(str.encode('utf-8')).hexdigest()   

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        def make_dicts(cursor, row):
            return dict((cursor.description[idx][0], value)
                        for idx, value in enumerate(row))
        db.row_factory = make_dicts
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    shutil.copyfile(app.config['DATABASE'],f'db_backup/{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.db')
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route('/todaybg.jpg')
def todaybg():
    apiurl = "https://pixabay.com/api/?key=27325054-b7631ae42e9f183140ebbf121&q=kitten&image_type=photo"
    response = requests.get(apiurl)
    data = response.json()
    imgurl = data['hits'][0].get('largeImageURL')
    if imgurl and imgurl != session.get('lastbgurl'):
        img_data = requests.get(imgurl).content
        with open(os.path.join(app.root_path, 'static', 'assets', 'todaybg.jpg'), 'wb') as handler:
            handler.write(img_data)
        session['lastbgurl'] = imgurl
    return send_from_directory(os.path.join(app.root_path, 'static', 'assets'), 'todaybg.jpg', mimetype='image/jpg')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        session.pop('pwdHashed', None)
        return render_template('login.pug')
    else:
        pwd = request.form['username'].lower() + request.form['pwd']
        pwdHashed = sha_hash(pwd)
        con = get_db()
        res = con.execute("SELECT * FROM user WHERE author_hash = ?", [pwdHashed])
        user = res.fetchone()
        if user is None:
            if not app.config['ALLOW_RIGISTER']:
                return '''
                <script>
                alert("查無使用者！");
                window.location.href='/';
                </script>
                '''
            data = {
                'username': request.form['username'],
                'headers': {
                    '0_'+sha_hash(datetime.datetime.now().isoformat() + '重要事項'): {'title': '重要事項'}, 
                    '1_'+sha_hash(datetime.datetime.now().isoformat() + '欄位1'): {'title': '欄位1'}, 
                    '2_'+sha_hash(datetime.datetime.now().isoformat() + '欄位2'): {'title': '欄位2'}
                }
            }
            con.execute("INSERT INTO user ('author_hash', 'datas') VALUES (?, ?)", 
                [pwdHashed, json.dumps(data, ensure_ascii=False)])
            con.commit()
            session['headers'] = data['headers']
            session['username'] = data['username']
        else:
            session['headers'] = json.loads(user['datas'])['headers']
            session['username'] = json.loads(user['datas'])['username']
        
        session['pwdHashed'] = pwdHashed
        if request.form.get('permanent') == 'on':
            session.permanent = True
        else:
            session.permanent = False
        return redirect(url_for('home'))
    
@app.route('/')
def home():
    if 'pwdHashed' not in session:
        return redirect(url_for('login'))
    page = int(request.args.get('page', 0))
    search = request.args.get('search', None)
    today = datetime.datetime.now(tz=pytz.timezone('Asia/Taipei')).date()
    try:
        sdate = datetime.datetime.strptime(request.args.get('sdate', None), "%Y-%m-%d").date()
    except:
        sdate = today
    initDate = today.replace(day=1) + relativedelta(months=page)
    dataByDay = {}
    con = get_db()
    res = con.execute("SELECT * FROM user WHERE author_hash = ?", [session['pwdHashed']])
    user = res.fetchone()
    session['headers'] = json.loads(user['datas'])['headers']
    if search is None:
        res = con.execute("SELECT object_date, datas FROM datas WHERE author_hash = ? AND object_date >= ? AND object_date < ? ORDER BY object_date ASC", [session['pwdHashed'], initDate, initDate + relativedelta(months=1)])
        data = res.fetchall()
        for row in data:
            dataByDay[row['object_date']] = json.loads(row['datas'])
        for i in range(list(calendar.monthrange(initDate.year, initDate.month))[1]):
            curDate = initDate + relativedelta(days=i)
            if curDate.strftime('%Y-%m-%d') not in dataByDay:
                dataByDay[curDate.strftime('%Y-%m-%d')] = {}
    else:
        res = con.execute("SELECT object_date, datas FROM datas, json_each(datas) WHERE author_hash = ? AND json_each.value LIKE ? AND object_date >= ? ORDER BY object_date ASC LIMIT 31",[session['pwdHashed'], f"%{str(search)}%", sdate])
        data = res.fetchall()
        for row in data:
            dataByDay[row['object_date']] = json.loads(row['datas'])
    dataSorted = {}
    for key, val in sorted(dataByDay.items(), key = lambda ele: ele[0]):
        val['datetime'] = datetime.datetime.strptime(key, "%Y-%m-%d")
        if key in holidayCalendar:
            val['holiday'] = holidayCalendar[key]
        dataSorted[key] = val
    return render_template('day.pug', data=dataSorted, headers=session['headers'], username=session['username'], today=today)

@app.route('/month')
def month():
    if 'pwdHashed' not in session:
        return redirect(url_for('login'))
    page = int(request.args.get('page', 0))
    currentKey = str(request.args.get('key', ''))
    if len(currentKey) < 1 or currentKey not in session['headers']:
        currentKey = list(session['headers'].keys())[0]
    today = datetime.datetime.now(tz=pytz.timezone('Asia/Taipei')).date()
    initDate = today.replace(day=1) + relativedelta(months=page)
    monthCalendar = calendar.monthcalendar(initDate.year, initDate.month)
    monthDatesCalendar = calendar.Calendar().monthdatescalendar(initDate.year, initDate.month)
    dataByDay = {}
    con = get_db()
    res = con.execute("SELECT * FROM user WHERE author_hash = ?", [session['pwdHashed']])
    user = res.fetchone()
    session['headers'] = json.loads(user['datas'])['headers']
    res = con.execute("SELECT object_date, datas FROM datas WHERE author_hash = ? AND object_date >= ? ORDER BY object_date ASC LIMIT 49", [session['pwdHashed'], initDate + relativedelta(days=-7)])
    data = res.fetchall()
    for row in data:
        dataByDay[row['object_date']] = json.loads(row['datas'])
    dataSorted = {key: val for key, val in sorted(dataByDay.items(), key = lambda ele: ele[0])}
    return render_template('month.pug', data=dataSorted, headers=session['headers'], username=session['username'], today=today, 
                           monthCalendar=monthDatesCalendar)

@app.route('/api/get-content/<date>/<key>')
def getContent(date, key):
    con = get_db()
    res = con.execute("SELECT datas FROM datas WHERE author_hash = ? AND object_date = ?", [session['pwdHashed'], date])
    col = res.fetchone()
    if col is not None:
        retData = {
            "success": True,
            "note": json.loads(col['datas']).get(key, {}).get('note', '')
        }
        return jsonify(retData), 200, {'contentType': 'application/json'}
    else:
        return jsonify({"success": True, "note": ""}), 200, {'contentType': 'application/json'}

@app.route('/api/update-content', methods=['POST'])
def updateContent():
    data = dict(request.json)
    con = get_db()
    res = con.execute("SELECT datas FROM datas WHERE author_hash = ? AND object_date = ?", [session['pwdHashed'], data['noteDate']])
    col = res.fetchone()
    if len(data['note'].replace("<br>","")) < 1:
        if col is not None:
            newData = json.loads(col['datas'])
            if data['noteKey'] in newData:
                newData.pop(data['noteKey'])
                con.execute("UPDATE datas SET datas = ? WHERE author_hash = ? AND object_date = ?", [json.dumps(newData, ensure_ascii=False), session['pwdHashed'], data['noteDate']])
                print("pop note:", data['noteDate'], data['noteKey'])
    elif col is None:
        con.execute("INSERT INTO datas ('author_hash', 'datas', 'object_date') VALUES (?, ?, ?)", 
                    [session['pwdHashed'], json.dumps({data['noteKey']: {'note': data['note']}}, ensure_ascii=False), data['noteDate']])
    else:
        newData = json.loads(col['datas'])
        if data['noteKey'] not in newData: newData[data['noteKey']] = {}
        newData[data['noteKey']]['note'] = data['note']
        con.execute("UPDATE datas SET datas = ? WHERE author_hash = ? AND object_date = ?", [json.dumps(newData, ensure_ascii=False), session['pwdHashed'], data['noteDate']])
    con.commit()
    return jsonify({"success": True}), 200, {'contentType': 'application/json'}

@app.route('/api/update-header', methods=['POST'])
def updateHeader():
    inData = dict(request.json)
    print(inData)
    con = get_db()
    headers = session['headers']
    if 'key' not in inData:
        inData['key'] = f"{inData['value']}_" + sha_hash(datetime.datetime.now().isoformat() + f"欄位{inData['value']}")
        inData['value'] = f"欄位{inData['value']}"
        headers[inData['key']] = {'title': inData['value']}
    elif len(inData['value'].replace("<br>","")) < 1:
        headers.pop(inData['key'])
        print("pop key", inData['key'])
    else:
        headers[inData['key']]['title'] = inData['value']
    newData = {
        'username': session['username'],
        'headers': headers
    }
    con.execute("UPDATE user SET datas = ? WHERE author_hash = ?", [json.dumps(newData, ensure_ascii=False), session['pwdHashed']])
    con.commit()
    session['headers'] = headers
    return jsonify({"success": True}), 200, {'contentType': 'application/json'}

@app.route('/initdb')
def cleardb():
    if app.debug:
        print("init db")
        init_db()
        return redirect(url_for('login'))
    else:
        return abort(403)
    