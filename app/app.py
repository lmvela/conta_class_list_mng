from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from pymongo import MongoClient
from bson import ObjectId
from dir_def import MONGO_URL, DB_NAME

# Import logger
from logger import get_logger

logger = get_logger()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
collection = db['apuntes_desc_col']

# Ensure collection exists
if 'apuntes_desc_col' not in db.list_collection_names():
    # Create collection by inserting and deleting a dummy document
    dummy = {"_init": True}
    result = collection.insert_one(dummy)
    collection.delete_one({"_id": result.inserted_id})

@app.route('/')
def index():
    try:
        apuntes = collection.find()
        return render_template('index.html', apuntes=apuntes)
    except Exception as e:
        logger.error(f"Error in index route: {e}", exc_info=True)
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
        logger.error(f"Apunte not found for oid={oid}")
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
    try:
        collection.update_one(
            {'_id': ObjectId(oid)},
            {'$pull': {'apunte_list': item}}
        )
        flash(f'Item "{item}" eliminado con éxito.', 'success')
    except Exception as e:
        logger.error(f"Error deleting item '{item}' from apunte {oid}: {e}", exc_info=True)
        flash(f'Error eliminando item "{item}".', 'error')
    return redirect(url_for('edit', oid=oid))

@app.route('/delete/<oid>', methods=['POST'])
def delete(oid):
    try:
        collection.delete_one({'_id': ObjectId(oid)})
        flash('Apunte eliminado con éxito.', 'success')
    except Exception as e:
        logger.error(f"Error deleting apunte {oid}: {e}", exc_info=True)
        flash('Error eliminando apunte.', 'error')
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
        logger.error("Import file ./log/full_export.json not found for import_apuntes")
        flash('No se encontró ./log/full_export.json para importar.', 'error')
        return redirect(url_for('index'))

    try:
        with open(import_path, 'r', encoding='utf-8') as f:
            data = loads(f.read())

        # Remove _id from imported documents to avoid duplicate key errors
        for doc in data:
            doc.pop('_id', None)
        if data:
            collection.insert_many(data)
            flash('Importación completada desde ./log/full_export.json', 'success')
        else:
            logger.error("No data found in import_apuntes file")
            flash('No se encontraron datos para importar.', 'error')
    except Exception as e:
        logger.error(f"Error importing apuntes: {e}", exc_info=True)
        flash('Error durante la importación.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
