from flask import Blueprint, request, jsonify

# Create a Blueprint
forms_bp = Blueprint('forms', __name__)

@forms_bp.route('/change_login', methods=['GET', 'POST'])
def change_login():
    if request.method == "POST" :
        username = request.form['username']
        password = request.form['passwd']
        print(username)
        print(password)
        if not username or not password:
            return jsonify(success=False, message="Missing username or password!")
    # Process feedback
        return jsonify(success=True, message="Details submitted successfully!")
    
    else:
        return """<html>NOT POST METHOD</html>"""
    
@forms_bp.route('/attend_time_update', methods=['GET', 'POST'])
def attend_time_update():
    if request.method == "POST" :
        early_start = request.form['early_start']
        early_end = request.form['early_end']
        late_start = request.form['late_start']
        late_end = request.form['late_end']
        print(early_start)
        print(early_end)
        print(late_start)
        print(late_end)
        if not early_start or not early_end or not late_start or not late_end:
            return jsonify(success=False, message="Missing a key field!")
    # Process feedback
        return jsonify(success=True, message="Time updated successfully!")
    
    else:
        return """<html>NOT POST METHOD</html>"""
    
@forms_bp.route('/late_fee_update', methods=['GET', 'POST'])
def late_fee_update():
    if request.method == "POST" :
        late_fee = request.form['late-fee']
        print(late_fee)
        if not late_fee:
            return jsonify(success=False, message="Missing a key field!")
    # Process feedback
        return jsonify(success=True, message="Fee updated successfully!")
    
    else:
        return """<html>NOT POST METHOD</html>"""
    
@forms_bp.route('/due_amount_update', methods=['GET', 'POST'])
def due_amount_update():
    if request.method == "POST" :
        due_fee = request.form['due-fee']
        print(due_fee)
        if not due_fee:
            return jsonify(success=False, message="Missing a key field!")
    # Process feedback
        return jsonify(success=True, message="Due amount updated successfully!")
    
    else:
        return """<html>NOT POST METHOD</html>"""
    
@forms_bp.route('/account_details', methods=['GET', 'POST'])
def account_details():
    if request.method == "POST" :
        acct_num = request.form['acct-num']
        acct_name = request.form['acct-name']
        bank_name = request.form['bank-name']
        print(acct_num)
        print(acct_name)
        print(bank_name)
        if not acct_num or not acct_name or not bank_name:
            return jsonify(success=False, message="Missing a key field!")
    # Process feedback
        return jsonify(success=True, message="Account Details updated successfully!")
    
    else:
        return """<html>NOT POST METHOD</html>"""