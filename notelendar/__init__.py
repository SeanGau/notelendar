from flask import Flask, g, request, render_template, session, redirect, url_for, jsonify
from sassutils.wsgi import SassMiddleware
from dateutil.relativedelta import relativedelta
import sqlite3, json, hashlib, datetime, pytz, shutil, calendar
        
app = Flask(__name__)
app.config.from_pyfile('config.py', silent=True)
app.wsgi_app = SassMiddleware(app.wsgi_app, {'notelendar': ('static/sass', 'static/css', '/static/css', True)})
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')
print(sqlite3.sqlite_version)

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
                    '0_'+sha_hash(datetime.datetime.now().isoformat() + '重要事項'): '重要事項', 
                    '1_'+sha_hash(datetime.datetime.now().isoformat() + '欄位1'): '欄位1', 
                    '2_'+sha_hash(datetime.datetime.now().isoformat() + '欄位2'): '欄位2'
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
        return redirect(url_for('home'))
    
@app.route('/')
def home():
    if 'pwdHashed' not in session:
        return redirect(url_for('login'))
    page = int(request.args.get('page', 0))
    search = request.args.get('search', None)
    today = datetime.datetime.now(tz=pytz.timezone('Asia/Taipei')).date()
    try:
        sdate = datetime.datetime.strptime(request.args.get('sdate', None), "%Y-%m-%d")
    except:
        sdate = today
    initDate = sdate + relativedelta(days=-6, months=page)
    dataByDay = {}
    con = get_db()
    res = con.execute("SELECT * FROM user WHERE author_hash = ?", [session['pwdHashed']])
    user = res.fetchone()
    session['headers'] = json.loads(user['datas'])['headers']
    if search is None:
        res = con.execute("SELECT object_date, datas FROM datas WHERE author_hash = ? AND object_date >= ? ORDER BY object_date ASC LIMIT 49", [session['pwdHashed'], initDate])
        data = res.fetchall()
        for row in data:
            dataByDay[row['object_date']] = json.loads(row['datas'])
        for i in range(49 - len(data)):
            curDate = initDate + relativedelta(days=i)
            if curDate.strftime('%Y-%m-%d') not in dataByDay:
                dataByDay[curDate.strftime('%Y-%m-%d')] = {}
    else:
        res = con.execute("SELECT object_date, datas FROM datas, json_each(datas) WHERE author_hash = ? AND json_each.value LIKE ? AND object_date >= ? ORDER BY object_date ASC LIMIT 49",[session['pwdHashed'], f"%{str(search)}%", initDate])
        data = res.fetchall()
        for row in data:
            dataByDay[row['object_date']] = json.loads(row['datas'])
    dataSorted = {key: val for key, val in sorted(dataByDay.items(), key = lambda ele: ele[0])}
    return render_template('day.pug', data=dataSorted, headers=session['headers'], username=session['username'], today=today.strftime('%Y-%m-%d'))

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
    dataByDay = {}
    con = get_db()
    res = con.execute("SELECT * FROM user WHERE author_hash = ?", [session['pwdHashed']])
    user = res.fetchone()
    session['headers'] = json.loads(user['datas'])['headers']
    res = con.execute("SELECT object_date, datas FROM datas WHERE author_hash = ? AND object_date >= ? ORDER BY object_date ASC LIMIT 49", [session['pwdHashed'], initDate])
    data = res.fetchall()
    for row in data:
        dataByDay[row['object_date']] = json.loads(row['datas'])
    dataSorted = {key: val for key, val in sorted(dataByDay.items(), key = lambda ele: ele[0])}
    return render_template('month.pug', data=dataSorted, headers=session['headers'], username=session['username'], today=today.strftime('%Y-%m-%d'), 
                           monthCalendar=monthCalendar, yearmonth=initDate.strftime("%Y-%m"), key=currentKey)

@app.route('/api/insert', methods=['POST'])
def insert():
    data = dict(request.json)
    con = get_db()
    res = con.execute("SELECT datas FROM datas WHERE author_hash = ? AND object_date = ?", [session['pwdHashed'], data['noteDate']])
    col = res.fetchone()
    if col is None:
        con.execute("INSERT INTO datas ('author_hash', 'datas', 'object_date') VALUES (?, ?, ?)", 
                    [session['pwdHashed'], json.dumps({data['noteKey']: data['note']}, ensure_ascii=False), data['noteDate']])
    else:
        newData = json.loads(col['datas'])
        newData[data['noteKey']] = data['note']
        con.execute("UPDATE datas SET datas = ? WHERE author_hash = ? AND object_date = ?", [json.dumps(newData, ensure_ascii=False), session['pwdHashed'], data['noteDate']])
    con.commit()
    return jsonify({"success": True}), 200, {'contentType': 'application/json'}

@app.route('/api/update-header', methods=['POST'])
def addHeader():
    inData = dict(request.json)
    print(inData)
    con = get_db()
    headers = session['headers']
    if 'key' not in inData:
        inData['key'] = f"{inData['value']}_" + sha_hash(datetime.datetime.now().isoformat() + f"欄位{inData['value']}")
        inData['value'] = f"欄位{inData['value']}"
        headers[inData['key']] = inData['value']
    elif len(inData['value'].replace("<br>","")) < 1:
        headers.pop(inData['key'])
        print("pop key", inData['key'])
    else:
        headers[inData['key']] = inData['value']
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
        init_db()
    else:
        print("not in debug, skip.")
    return redirect(url_for('login'))
    