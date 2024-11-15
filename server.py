from flask import Flask,request,Response,render_template,session,redirect,url_for,jsonify
from flask_session import Session
import socket
import pandas as pd
import numpy as np
import os
from datetime import datetime, time
import openpyxl
import random

app = Flask(__name__)
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)

# Define the path to the CSV files
x = datetime.now()
y = x.strftime("%a")
month = x.strftime("%b")
day = x.strftime("%d")
year = x.strftime("%Y")

reg_path_day = f"Attendance_logs_daily/NIESAT_KW_CDS_Attendance_{month}-{day}-{year}.csv"
reg_path_month = f"Attendance_logs_monthly/NIESAT_KW_CDS_Attendance_{month}-{year}.csv"
late_file = f"latelist.csv"
# late_file = f"Latecomers_logs_daily/latelist_{month}-{day}-{year}.csv"

# --------- ROUTES ---------- #

@app.route('/')
def index():
    return render_template ("index.html")

@app.route('/history')
def history():
    return render_template ("error.html")
    return render_template ("history.html")
    # return ("successful")
    
@app.route('/check', methods=['GET','POST'])
def check():
    # Check if the form has been submitted
    if request.method == "POST":
        statecode = request.form['statecode']
        startdate = request.form['start']
        enddate = request.form['end']
        print(startdate)
        print(enddate)

        statecode = usrname.upper()
        
        # Check if user exists in customers.csv database
        loginStatus = check_user_login_exists(statecode, startdate, enddate)
        if loginStatus == True :
            # Adds user to session if login is successful
            session['username'] = statecode
            session.permanent = True #the session will last for the lifetime of the user's browser session, or until the permanent_session_lifetime expires, whichever is sooner.
            return render_template("check.html")
        else:
            return("<h1><pre>Username and password are incorrect or do not exist.</pre>  Please go back and try again.</h1>")
             
    else:        
        return render_template ("history.html")
    
@app.route('/signin')
def signin():  
    return render_template ("signin.html")

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    # HANDLES USER SIGN-IN
    
    # Define attendance time ranges
    early_start = time(8, 45)  # 8:45 AM
    early_end = time(9, 20)    # 9:20 AM
    late_start = time(9, 20)   # 9:20 AM
    late_end = time(12, 5)     # 12:05 PM
    
    if request.method == "POST":
        fname = request.form['fname'].lower()
        mname = request.form['mname'].lower()
        sname = request.form['sname'].upper()
        statecode = request.form['statecode'].upper()
        
        signInTD = datetime.now().strftime('%Y-%m-%d %H:%M:%S')[:-3] 
        signInTime = datetime.now().strftime('%H:%M:%S')
        signInD = datetime.now().strftime('%Y-%m-%d')
        
        # Get the client IPAddress
        client_ip = get_client_IP()
        
        # Check if database file exists
        check_database_exists()
        
        # Check Registration status of user
        regStatus = check_user_reg_exists(sname, statecode, client_ip)
        
        # Handle error message or add user to database
        if regStatus != "" :
            regErrorMsg = regStatus
            return render_template ("signin.html", regErrorMsg=regErrorMsg)
        else :
            current_time = datetime.now().time()
            # if late_start <= current_time < late_end :
            # if current_time < early_end:
            if late_start <= current_time:
                request_type = "Late sign-in"
                amount = 200
                status = "Pending"
                
                # Check if user already in attendance list
                late_status = check_latefile(statecode)
                if not late_status:
                    datanew = [signInD,statecode,request_type,amount,status]
                    new_input_df = pd.DataFrame(data = [datanew])
                    new_input_df.to_csv(late_file,mode='a',index=False,header=False)
                return payment(fname,mname,sname,statecode,signInTime,signInTD,client_ip)
                
            elif early_start <= current_time < early_end :
                add_user_to_database(fname,mname,sname,statecode,signInTime,signInTD,client_ip)
            else:
                regErrorMsg = "Sign-in time elapsed or not yet reached!"
                return render_template ("signin.html", regErrorMsg=regErrorMsg)   
    
    else:    
        return render_template ("signup.html")
    
    return render_template ("thankyouregister.html")

@app.route('/late/signin', methods=['GET', 'POST'])
def late_reg():
    #Add late approved user to attendance list
    if request.method == 'POST':
        fname = request.form['fname'].lower()
        mname = request.form['mname'].lower()
        sname = request.form['sname'].upper()
        statecode = request.form['statecode'].upper()
        signInTime = request.form['signInTime']
        signInTD = request.form['signInTD']
        client_ip = request.form['client_ip']
        add_user_to_database(fname,mname,sname,statecode,signInTime,signInTD,client_ip)
        
        return render_template ("thankyouregister.html")

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == "POST":
        username = request.form['adminusr'].lower()
        password = request.form['adminpwd']
        
        print(f"Received username: {username}, password: {password}")
        
        if username == 'admin' and password == 'niesat001' :
            return jsonify(success=True), 200 # Response with success status
        else :
            return jsonify(success=False), 401 # Response with failure status and 401 error
    return render_template ('adminlogin.html')

@app.route('/admin/dashboard')
def admindash():
    # UPDATES ADMIN DASHBOARD WITH UNANSWERED REQUESTS
    
    # Read the late csv file
    df = pd.read_csv(late_file)
    
    # Convert the DataFrame to a list of dictionaries for Jinja
    # pending_requests = df.to_dict(orient='records')
    pending_requests = df[df['status'] == 'Pending'].to_dict(orient='records')
    
    # Pass the data to the template
    return render_template ('admindashboard.html', pending_requests=pending_requests)

@app.route('/get_details', methods=['GET'])
def getDetails():
    # GETS THE AMOUNT FROM THE USER DATABASE AND 
    # #UPDATES THE ADMIN DASHBOARD REQUESTS TABLE
    
    # Get the user status from the query parameters
    stateCode = request.args.get('stateCode').upper()
    df = pd.read_csv(late_file)
    pending_requests = df[(df['state_code'] == stateCode) & (df['status'] == 'Pending')]
    amount = pending_requests['amount'].iloc[0]
    return str(amount)

@app.route('/status_update', methods=['POST'])
def pop_latecomer():
    # UPDATES USER STATUS AND REMOVES APPROVED USER FROM LATE FILE
    
    statecode = request.form['state_code'].upper()
    status = request.form['status']
    if status == "Approved":
        update_latecomer_status(statecode)
    else:
        pass
    return redirect(url_for('admindash'))

@app.route('/payment/late-signin')
def payment(fname,mname,sname,statecode,signInTime,signInTD,client_ip):
    # statecode = request.args.get('statecode').upper()
    
    # Get latecomer details from the CSV file
    df = pd.read_csv(late_file)
    latecomer = df[df['state_code'] == statecode]
    
    if not latecomer.empty:
        amount = latecomer['amount'].iloc[0]
        return render_template("paymentpage.html",fname=fname,mname=mname,sname=sname, statecode=statecode,signInTime=signInTime,signInTD=signInTD,client_ip=client_ip, amount=amount)
    else:
        return "<h1>Invalid Request</h1>"
    
@app.route('/check_status')
def check_status():
    statecode = request.args.get('statecode').upper()
    df = pd.read_csv(late_file)
    status = df.loc[df['state_code'] == statecode, 'status'].values[0]
    return status

@app.route('/payment/monthly-due')
def pay_monthly_due():
    return render_template ("error.html")

@app.route('/admin/settings')
def admin_settings():
    return """<html>
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta http-equiv="refresh" content="4; url= /admin/dashboard">
                <title>Error page</title>
            </head>
            <body style="align-items: center; font-size: 40px;">
                <p>
                    This page is still under construction.
                    <br>
                    Feature will be available soon.
                </p>
            </body>
            </html>"""
    # return render_template ("error.html")

@app.route('/payment2')
def payment2():
    return render_template("payment2.html")


# --------- FUNCTIONS ---------- #

def check_user_reg_exists(sname, statecode, client_ip):
    # Load the CSV file into a pandas DataFrame
    df = pd.read_csv(reg_path_day)
    
    # Check if user already in attendance list
    if (df['StateCode'] == statecode).any():
        return "StateCode already logged for today!"
    elif (df['IpAddress'] == client_ip).any():
        return "Can't use the same device for more than one signing!"
    else:
        return ""

def check_user_login_exists(statecode, startdate, enddate):
    # Load the CSV file into a pandas DataFrame
    df = pd.read_csv(reg_path_day)
    # check if the provided username and password match any row in the dataframe using pandas' boolean indexing
    match = df[(df['StateCode'] == statecode) & (df['Password'] == password)]
    # if there's a match, return True, else return False
    if not match.empty:
        return True 
    else:
        return False

def check_database_exists():
    #----------------DAY---------------------
    columnsnormal = ["First Name", "Middle Name","Last Name", "StateCode", "SignIn Date&Time", "IpAddress"]
    new_input_df = pd.DataFrame(columns = columnsnormal)
    if not os.path.exists(reg_path_day):
        new_input_df.to_csv(reg_path_day,index=False,header=True)
    
    #----------------MONTH---------------------
    columnsnormalmonth = ["First Name", "Middle Name","Last Name", "StateCode"]
    new_input_df = pd.DataFrame(columns = columnsnormalmonth)
    if not os.path.exists(reg_path_month):
        new_input_df.to_csv(reg_path_month,index=False,header=True)
        
    #----------------LATE FILE-----------------
    columnsnormal = ["transanct_date","state_code","request_type","amount","status"]
    new_input_df = pd.DataFrame(columns = columnsnormal)
    if not os.path.exists(late_file):
        new_input_df.to_csv(late_file,index=False,header=True)

def get_client_IP():
    # global client_ip
    if request.headers.getlist("X-Forwarded-For") :
        client_ip = request.headers.getlist("X-Forwarded-For")[0]
        print(1)
        return client_ip
    else :
        client_ip = request.remote_addr
        print(2)
        return client_ip

    print(f"Client IP is {client_ip}")

def add_user_to_database(fname,mname,sname,statecode,signInTime,signInTD,client_ip):
    #--------- Add to day's database
    datanew = [fname,mname,sname,statecode,signInTD,client_ip]
    new_input_df = pd.DataFrame(data = [datanew])
    new_input_df.to_csv(reg_path_day,mode='a',index=False,header=False)
    
    
    #--------- Add to Monthly database
    
    # Collect current day name and date
    new_day = datetime.now().strftime('%a-%d')
    # new_day = "Thursday"
    
    
    # Check if file exists
    if os.path.exists(reg_path_month):
        print('File Exists!')
        
        # Read monthly file
        df = pd.read_csv(reg_path_month)
        print('File Read!')
        
        # Check if the current day column has been created...
        if (str(new_day) not in df.columns):
            # Add new column for the current day, initializing it with NaN
            df[new_day] = "absent"
            print('New Day Added!')
            
        # Check if the statecode exists in the DataFrame
        if (df['StateCode'].astype(str) == str(statecode)).any():
            print('StateCode Present!')
            # Update the arrival time for the user on the current day
            df.loc[df['StateCode'].astype(str) == str(statecode), new_day] = signInTime
        else:
            # if statecode doesn't exist in file yet.
            print('No StateCode Present!')
            # Save user details to the file
            datanew = [fname,mname,sname,statecode] + ["absent"] * (len(df.columns) - 4) # Ensures all columns are filled
            df.loc[len(df)] = datanew  # Append new user
            df.loc[df['StateCode'].astype(str) == str(statecode), new_day] = signInTime

        # Save the updated DataFrame
        df.to_csv(reg_path_month, index=False)
        print('File Updated!')
        
        # If the monthly file doesn't exist
    else :
        print('File does not exist. Creating new file...')
        # If file does not exist, create a new DataFrame with user details
        columnsnormalmonth = ["First Name", "Middle Name","Last Name", "StateCode", new_day]
        new_user_data = [fname, mname, sname, statecode, signInTime]
        df = pd.DataFrame([new_user_data], columns=columnsnormalmonth)
        
        # Save the new DataFrame to CSV
        df.to_csv(reg_path_month, index=False)
        print('New file created and saved!')

def update_latecomer_status(stateCode):
    # datanew = [signInD,statecode,request_type,amount,status]
    # new_input_df = pd.DataFrame(data = [datanew])
    # new_input_df.to_csv(late_file,mode='a',index=False,header=False)
    
    df = pd.read_csv(late_file)
    df.loc[df['state_code'] == stateCode, 'amount'] = 0
    df.loc[df['state_code'] == stateCode, 'status'] = "Approved"
    # drop_row = df[df['state_code'] == stateCode].index[0]
    # df = df.drop(drop_row)
    df.to_csv(late_file, index=False)

def check_latefile(statecode):
    # Load the CSV file into a pandas DataFrame
    df = pd.read_csv(late_file)
    
    # Check if statecode already in latefile
    if (df['state_code'] == statecode).any():
        return True
    else:
        return False


    

if __name__ =="__main__":
    app.run(host="0.0.0.0",port = 80, debug = True, threaded = True)
