from flask import Flask, request, jsonify, render_template,redirect,url_for
from logic import F1db, monte_carlo_championship
import os
import time
import random
app = Flask(__name__)
db = F1db()

@app.route('/')
def index():
    all_data = db.get_all_data()
    return render_template('index.html',all_data=all_data)


@app.route('/api_update/<int:id>', methods=['POST'])
def api_update(id):
    # buraya silme işlemini yazacaksın
    print("Silinecek ID:", id)
    db.delete_driver(id)

    # işlem bittikten sonra tekrar liste sayfasına dön
    return redirect(url_for('index'))

@app.route('/api/drivers', methods=['GET','POST'])
def api_drivers():
    if request.method == 'GET':
        return jsonify(db.get_drivers())
    else:
        data = request.get_json() or {}
        drivers = data.get('drivers', [])
        incoming_ids = set()
        for d in drivers:
            did = d.get('id')
            db.upsert_driver(did, d['name'], int(d['points']), float(d.get('dnf_prob',0.05)))
            if did is not None:
                incoming_ids.add(did)
        for ex in db.get_drivers():
            if ex['id'] not in incoming_ids and len(incoming_ids)>0:
                db.delete_driver(ex['id'])
        return jsonify({'status':'ok','message':'Sürücüler güncellendi'})

@app.route('/api/races', methods=['GET','POST','DELETE'])
def api_races():
    if request.method == 'GET':
        return jsonify(db.get_remaining_races())
    elif request.method == 'POST':
        data = request.get_json() or {}
        db.upsert_race(None, data.get('name','').strip(), bool(data.get('is_sprint', False)))
        return jsonify({'status':'ok'})
    else:
        data = request.get_json() or {}
        rid = data.get('id')
        if rid:
            db.c.execute('DELETE FROM remaining_races WHERE race_id=?',(int(rid),))
            db.conn.commit()
        return jsonify({'status':'ok'})

@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    data = request.get_json() or {}
    num = int(data.get('num_simulations',10000))
    return jsonify({'status':'ok','probabilities':monte_carlo_championship(db.get_drivers(), db.get_remaining_races(), num_simulations=num)})

@app.route('/api/reset', methods=['POST'])
def api_reset():
    db.reset_data()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0', port=5000)
