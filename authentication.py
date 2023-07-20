import pyrebase
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from PIL import Image
import io
import numpy as np

app = Flask(__name__)
app.secret_key='abcde'
from keras.models import load_model

# Load the model using load_model
model = load_model('models/PCOSwithoutFilterModel.h5')
config = {
  'apiKey': "AIzaSyBbbB-BHOzzwkIpc2bzDHijSAB5Xc2KwP8",
  'authDomain': "precise-valor-300716.firebaseapp.com",
  'projectId': "precise-valor-300716",
  'storageBucket': "precise-valor-300716.appspot.com",
  'messagingSenderId': "427725702900",
  'appId': "1:427725702900:web:ed293e125464ffb17400a1",
  'measurementId': "G-B3FP53THT0",
  'databaseURL' : "https://precise-valor-300716-default-rtdb.asia-southeast1.firebasedatabase.app/"
}

firebase=pyrebase.initialize_app(config)
auth=firebase.auth()

db = firebase.database()

#Initialze person as dictionary
person = {"is_logged_in": False, "name": "", "email": "", "uid": ""}

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

#Login
@app.route("/")
@app.route('/login', methods =['GET', 'POST'])
def login():
    mesage=''
    if 'is_logged_in' not in session and request.method == "POST" and 'email' in request.form and 'password' in request.form:        #Only if data has been posted
        result = request.form           #Get the data
        email = result["email"]
        password = result["password"]
        try:
            #Try signing in the user with the given information
            user = auth.sign_in_with_email_and_password(email,password)
            #Insert the user data in the global person
            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            
            session['loggedin'] = True
            local_id = user['localId']

            # Retrieve the name of the user from the Firebase Realtime Database
            name = db.child("users").child(local_id).child("name").get().val()
            session['name']=name

            mesage='Logged In Successfully'
            return render_template('index.html',mesage=mesage)
        except Exception as e:
            
            print(f"Login Error: {str(e)}")
            mesage = 'Please enter correct email / password !'
    return render_template('login.html',mesage=mesage)

#If someone clicks on register, they are redirected to /register
@app.route("/register", methods = ["POST", "GET"])
def register():
    mesage=''
    if request.method == "POST" and 'name' in request.form and 'password' in request.form and 'email' in request.form and 'conpassword' in request.form :        #Only listen to POST
        result = request.form           #Get the data submitted
        email = result["email"]
        password = result["password"]
        name = result["name"]
        conpass=result['conpassword']
        if conpass!=password:
            mesage="Passwords Don't Match"
            return render_template('register.html',mesage=mesage)
        try:
            #Try creating the user account using the provided data
            user=auth.create_user_with_email_and_password(email, password)
            
            global person
            
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            person["name"] = name
            #Append data to the firebase realtime database
            data = {"name": name, "email": email}
            db.child("users").child(person["uid"]).set(data)
            #Go to welcome page
            mesage = 'You have successfully registered !'
        except:
            mesage='There is a problem with Account Creation'
    return render_template('register.html',mesage=mesage)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('name',None)
    global person
    person["is_logged_in"]=False
    return redirect(url_for('login')) 

@app.route('/predict', methods=['POST'])
def predict():
    file = request.files['image']
    print(file)    
    output = ""
    
    def predictimage(file):
        nonlocal output
        
        img = Image.open(io.BytesIO(file.read()))
        img = img.resize((224, 224))
        i = np.array(img) / 255.0
        input_arr = np.array([i])
        input_arr.shape
        pred = model.predict(input_arr)
        if pred == 1:
            output = "Not Affected"
        else:
            output = "Affected"

    predictimage(file)
    return render_template('index.html', prediction_text='PCOS {} '.format(output))


if __name__ == "__main__":
    app.run()