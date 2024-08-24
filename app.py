from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = 'your_secret_key'

client = MongoClient('mongodb://localhost:27017/')
db = client['conta_db']
collection = db['apuntes_desc_col']

@app.route('/')
def index():
    apuntes = collection.find()
    return render_template('index.html', apuntes=apuntes)

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

if __name__ == '__main__':
    app.run(debug=True)
