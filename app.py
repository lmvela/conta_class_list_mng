import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load MongoDB config from ./config/config.json
with open(os.path.join(os.path.dirname(__file__), 'config', 'config.json')) as f:
    config = json.load(f)
mongodb_cfg = config.get('mongodb', {})
mongo_url = mongodb_cfg.get('url', 'mongodb://localhost:27017/conta_db')

client = MongoClient(mongo_url)
# If the database is specified in the URL, get_default_database() will return it
db = client.get_default_database()
collection = db['apuntes_desc_col']

@app.route('/')
def index():
    try:
        apuntes = collection.find()
        return render_template('index.html', apuntes=apuntes)
    except Exception as e:
        # If DB is unavailable, show error page
        return render_template('error.html'), 500

@app.route('/add_apunte', methods=['POST'])
def add_apunte():
    apunte_num = request.form.get('apunte_num')
    apunte_desc = request.form.get('apunte_desc')
    apunte_list = request.form.get('apunte_list').split(',')

    if apunte_num and apunte_desc and apunte_list:
        new_apunte = {
            "apunte_num": int(apunte_num),
            "apunte_desc": apunte_desc,
            "apunte_list": [apunte.strip() for apunte in apunte_list]
        }
        collection.insert_one(new_apunte)
    return redirect(url_for('index'))

@app.route('/edit/<oid>', methods=['GET', 'POST'])
def edit(oid):
    apunte = collection.find_one({'_id': ObjectId(oid)})
    if not apunte:
        flash('Apunte no encontrado.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        apunte_num = int(request.form['apunte_num'])
        apunte_desc = request.form['apunte_desc']
        apunte_list = request.form.getlist('apunte_list')

        additional_item = request.form.get('apunte_list_add')
        if additional_item:
            apunte_list.append(additional_item)

        collection.update_one(
            {'_id': ObjectId(oid)},
            {'$set': {'apunte_num': apunte_num, 'apunte_desc': apunte_desc, 'apunte_list': apunte_list}}
        )

        flash('Apunte actualizado con éxito.', 'success')
        return redirect(url_for('index'))

    return render_template('edit.html', apunte=apunte)

@app.route('/delete_item/<oid>/<item>')
def delete_item(oid, item):
    collection.update_one(
        {'_id': ObjectId(oid)},
        {'$pull': {'apunte_list': item}}
    )
    flash(f'Item "{item}" eliminado con éxito.', 'success')
    return redirect(url_for('edit', oid=oid))

@app.route('/delete/<oid>', methods=['POST'])
def delete(oid):
    collection.delete_one({'_id': ObjectId(oid)})
    flash('Apunte eliminado con éxito.', 'success')
    return redirect(url_for('index'))

@app.route('/export_apuntes', methods=['POST'])
def export_apuntes():
    import os
    from bson.json_util import dumps

    # Ensure log directory exists
    log_dir = os.path.join(os.path.dirname(__file__), 'log')
    os.makedirs(log_dir, exist_ok=True)
    export_path = os.path.join(log_dir, 'full_export.json')

    # Export all apuntes
    apuntes = list(collection.find())
    with open(export_path, 'w', encoding='utf-8') as f:
        f.write(dumps(apuntes, ensure_ascii=False, indent=2))

    flash('Exportación completada: ./log/full_export.json', 'success')
    return redirect(url_for('index'))

@app.route('/import_apuntes', methods=['POST'])
def import_apuntes():
    import os
    from bson.json_util import loads

    import_path = os.path.join(os.path.dirname(__file__), 'log', 'full_export.json')
    if not os.path.exists(import_path):
        flash('No se encontró ./log/full_export.json para importar.', 'error')
        return redirect(url_for('index'))

    with open(import_path, 'r', encoding='utf-8') as f:
        data = loads(f.read())

    # Remove _id from imported documents to avoid duplicate key errors
    for doc in data:
        doc.pop('_id', None)
    if data:
        collection.insert_many(data)
        flash('Importación completada desde ./log/full_export.json', 'success')
    else:
        flash('No se encontraron datos para importar.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
