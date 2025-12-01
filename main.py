from flask import Flask, request, jsonify, render_template,redirect,url_for,session
from logic import F1db, monte_carlo_championship
import os
import time
import random
app = Flask(__name__)
app.secret_key = "f1"
db = F1db()

@app.route('/')
def index():
    all_data = db.get_all_drivers()
    races_names = db.get_all_races_names()
    print(races_names)
    probabilities = session.pop('probabilities', None)
    if probabilities:
        return render_template('index.html',all_data=all_data,races_names=races_names, probabilities = probabilities)
    return render_template('index.html',all_data=all_data,races_names=races_names)


@app.route('/api_update/<int:id>', methods=['POST'])
def api_update(id):
    print("Silinecek ID:", id)
    db.delete_driver(id)
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

@app.route('/api/races', methods=['POST'])
def api_races():
    race_name = request.form.get("race_name")
    sprint = request.form.get("is_sprint")
    print("race name")
    print("sprint")
    db.add_race(race_name,sprint)
    return redirect("/")

@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    data = db.get_all_drivers()
    races = db.get_all_races()
    probabilities = monte_carlo_championship(data,races)
    session['probabilities'] = probabilities
    return redirect("/")

@app.route('/api/reset', methods=['POST'])
def api_reset():
    db.reset_data()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0', port=5000)
