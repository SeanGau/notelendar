from flask import Flask, g, request, render_template, session, redirect, url_for, jsonify
from sassutils.wsgi import SassMiddleware
import sqlite3, json, hashlib, datetime, pytz
        
app = Flask(__name__)
app.config.from_pyfile('config.py', silent=True)
app.wsgi_app = SassMiddleware(app.wsgi_app, {'notelendar': ('static/sass', 'static/css', '/static/css', True)})
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')

def sha256(str):
    str += app.config['SALT']
    return hashlib.sha256(str.encode('utf-8')).hexdigest()   

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
        pwd = request.form['username'] + request.form['pwd']
        pwdHashed = sha256(pwd)
        con = get_db()
        res = con.execute("SELECT * FROM user WHERE author_hash = ?", [pwdHashed])
        user = res.fetchone()
        if user is None:
            data = {
                'username': request.form['username'],
                'headers': {
                    '0_'+sha256(datetime.datetime.now().isoformat() + '重要事項'): '重要事項', 
                    '1_'+sha256(datetime.datetime.now().isoformat() + '欄位1'): '欄位1', 
                    '2_'+sha256(datetime.datetime.now().isoformat() + '欄位2'): '欄位2'
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
    con = get_db()
    initDate = datetime.datetime.now(tz=pytz.timezone('Asia/Taipei')).date() + datetime.timedelta(days=(-7 + page * 30))
    res = con.execute("SELECT object_date, datas FROM datas WHERE author_hash = ? AND object_date >= ?ORDER BY object_date ASC LIMIT 60", [session['pwdHashed'], initDate])
    data = res.fetchall()
    dataArray = []
    dataDateArray = []
    for row in data:
        dataArray.append({
            'object_date': row['object_date'],
            'datas': json.loads(row['datas'])
        })
        dataDateArray.append(row['object_date'])
    for i in range(60):
        curDate = initDate + datetime.timedelta(days=i)
        if curDate.strftime('%Y-%m-%d') not in dataDateArray:
            dataArray.append({
                'object_date': curDate.strftime('%Y-%m-%d'),
                'datas': {}
            })
    dataArray.sort(key=lambda data: data['object_date'])
            
    return render_template('home.pug', data=dataArray, headers=session['headers'], username=session['username'])

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
    if 'key' not in inData:
        inData['key'] = f"{inData['value']}_" + sha256(datetime.datetime.now().isoformat() + f"欄位{inData['value']}")
        inData['value'] = f"欄位{inData['value']}"
    headers = session['headers']
    headers[inData['key']] = inData['value']
    newData = {
        'username': session['username'],
        'headers': headers
    }
    con = get_db()
    con.execute("UPDATE user SET datas = ? WHERE author_hash = ?", [json.dumps(newData, ensure_ascii=False), session['pwdHashed']])
    con.commit()
    session['headers'] = headers
    return jsonify({"success": True}), 200, {'contentType': 'application/json'}

@app.route('/cleardb')
def cleardb():
    if app.debug:
        init_db()
    else:
        print("not in debug, skip.")
    return redirect(url_for('login'))
    