import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai
from dotenv import load_dotenv
import os

# set up google gemini -pro AI model
genai.configure(api_key="AIzaSyDbfw2oNlIZ3NFNRejoD_6DjSjX2umI9Es")
model = genai.GenerativeModel(model_name="gemini-1.0-pro")

# translate thr role b/w gemini and streamlit terminolgy
def translate_role(user_role):
    if user_role == 'model':
        return 'assistant'
    else:
        return user_role

# Firebase credentials and initialization (replace with your actual credentials)
cred = credentials.Certificate("test-fac5f-9129c8825690.json")
try:
    firebase_admin.initialize_app(cred)
except ValueError:
    pass
    
# Initialize session state for screen 
if "current_screen" not in st.session_state:
    st.session_state.current_screen = "signup"
if 'current_email' not in st.session_state:
    st.session_state.current_email = 'current_email'
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history = [])


# Function to create a user prompt based on entered information
def create_user_prompt(user_question,user_data):
    return f"""Hi Gemini, you are an expert in health and exercise. 
  Please provide suggestions and information related to the following question: 
  "{user_question},{user_data}"""

def get_health_recommendations():
    """Gets user input, sends it to Gemini, and displays the chat history."""
    user_question = st.text_input("Enter your question")
    if st.button("Get Health Recommendations"):
        # Load user data based on email
        try:
            with open('user_data.json', 'r') as f:
                all_user_data = json.load(f)
            user_data = all_user_data.get(st.session_state.current_email, {})
        except FileNotFoundError:
            user_data = {}

        user_prompt = create_user_prompt(user_question, user_data)
        response = st.session_state.chat_session.send_message(user_prompt)

        # Display chat history
        for message in st.session_state.chat_session.history:
            with st.chat_message(translate_role(message.role)): 
                st.markdown(message.parts[0].text)



# Function to save user data to a JSON file
def save_to_json(data):
    try:
        with open('user_data.json', 'r') as f:
            user_data = json.load(f)
    except FileNotFoundError:
        user_data = {}

    data["email"] = st.session_state.current_email
    # Use email as the key to store data for each user
    today = datetime.now().strftime("%d-%m-%Y")
    #print(user_data)
    if data['email'] not in user_data:
        user_data[data['email']] ={}
        #print(user_data)
   
    user_data[data["email"]][today] = data
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f, indent=4)  

# Function to navigate between screens
def navigate_to(screen):
    st.session_state.current_screen = screen

# Function to calculate calories
def calculate_calories(calories_per_100g, grams_consumed):
    total_calories = (calories_per_100g * grams_consumed) / 100
    return total_calories

# Function to calculate BMR
def calculate_bmr(weight_kg, height_cm, age, gender):
    if gender == 'male':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return bmr

# Function to calculate BMI
def calculate_bmi(weight_kg, height_cm):
    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2))
    return bmi


def display_user_data(email):
    try:
        with open('user_data.json', 'r') as f:
            user_data = json.load(f)
        if email in user_data:
            st.subheader(f"Data for {email}:")
            all_data = [] 
            for date_str, data in user_data[email].items():
                data['Date'] = date_str  
                all_data.append(data)
            
            df = pd.DataFrame(all_data)
            df = df.drop(columns=['email','age'])
            st.write(df)
         # Create a weight, BMI, and BMR graph using Matplotlib
            weight_df = df[['Date', 'weight_kg', 'BMI', 'BMR']]

            # Create the figure and the first y-axis (for Weight and BMR)
            fig, ax1 = plt.subplots(figsize=(10, 8)) 

            # Weight (on ax1 - left y-axis)
            ax1.plot(weight_df['Date'], weight_df['weight_kg'], marker='o', linestyle='-', label='Weight (kg)', color='blue')
            
            # BMR (on ax1 - left y-axis)
            ax1.plot(weight_df['Date'], weight_df['BMR'], marker='^', linestyle=':', color='green', label='BMR')
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Weight (kg) / BMR', color='blue')  # Label for the left y-axis
            ax1.tick_params(axis='y', labelcolor='blue')

            # Create a second y-axis (for BMI)
            ax2 = ax1.twinx()
            # BMI (on ax2 - right y-axis)
            ax2.plot(weight_df['Date'], weight_df['BMI'], marker='s', linestyle='--', color='red', label='BMI')
            ax2.set_ylabel('BMI', color='red')  # Label for the right y-axis
            ax2.tick_params(axis='y', labelcolor='red')

            plt.title('Weight, BMI, and BMR Over Time')
            plt.grid(True)

            # Legend for all lines (combine legends from both axes)
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

            #Highlighting the BMI line 
            ax2.spines['right'].set_linewidth(3)  # Make the right spine thicker
            ax2.spines['right'].set_color('red')  # Change the color of the spine

            st.pyplot(fig)  # Display the Matplotlib plot in Streamlit
        else:
            st.warning(f"No data found for {email}")

    except FileNotFoundError:
        st.error("User data file not found!")


# Display the title with a health-related image
col1, col2, col3 = st.columns([1, 1, 1])  # Create 3 equal-width columns
with col2:  # Use the middle column
    st.image("health.png", width=250)  # Replace with your image path
st.markdown("<h1 style='text-align:center; color:red;'>Health Tracker</h1>", unsafe_allow_html=True)

user_data = {}  

# Sign Up Screen
def signup_screen():
    with st.form("Create account", clear_on_submit=True):
        f_name = st.text_input("Enter your name")
        e_mail = st.text_input("Enter email name")
        pass_1 = st.text_input("Create your Password", type="password")
        re_pass = st.text_input("Re-enter Your password", type="password")
        s_state = st.form_submit_button("Sign up")
        if s_state:
            if not e_mail or not pass_1 or not re_pass:
                st.warning("Please fill in all fields.")
            elif pass_1 != re_pass:
                st.warning("Passwords don't match")
            else:
                try:
                    user = auth.create_user(email=e_mail, password=pass_1)
                    st.success("Sign up successful!🚀")
                    st.form_submit_button("Please Add Health data Here", on_click=navigate_to, args=("data_add_display",))  # Navigate to data display screen after signup
                except Exception as e:
                    st.error(f"error in create user: {e}")
# Login Screen
def login_screen():
    st.subheader("Login")
    email = st.text_input("email")
    # user_data['email']  = email
    st.session_state["current_email"] = email
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")       
    if login_button:
        try:
            user = auth.get_user_by_email(email=email)
            st.success("Logged in! \n Welcome to add data click on below button⬇️")
            st.button("Add data", on_click=navigate_to, args=("data_add_display",))
            st.button("Display User Data", on_click=navigate_to, args=("display_data",))
            
        except Exception as e:
            st.error(f"invalid{e}")
    st.button("Create New Account", on_click=navigate_to, args=("signup",))
# Data Display Screen
def data_add_screen():
    st.button("click here to back ", on_click=navigate_to, args=("signup",))
    st.button("Already have an account? Login Here", on_click=navigate_to, args=("login",))
    st.header("What is your main goal🎯 ")
    goal = st.radio("Select", ["📉Lose weight", "👀Maintain weight", "📈Gain weight", "💪Build muscle"])
    user_data["goal"] = goal

    st.subheader("What experience do you have with weight loss?")
    weight_loss_exp = st.selectbox("Select🏋️", [
        "i have lost before and want to lose more",
        "I tired before but unsuccessful",
        "I lost but now i gain back",
        "i never try"
    ])
    user_data["weight_loss_exp"] = weight_loss_exp

    st.subheader("What's your gender")
    gender = st.selectbox("select", ["🚹male", "🚺female"])
    user_data["gender"] = gender

    activity_level = st.selectbox(
        "Activity Level",
        ["Sedentary🧑🏿‍💻", "Lightly Active🏃🏾‍♂️", "Moderately Active🚴🏽", "Very Active🏋🏽🔥💪🏼🎧"]
    )
    user_data["activity_level"] = activity_level

    st.subheader("Tell us more about you:")
    age = st.number_input("Age🗓️", min_value=13, max_value=80, value=25)
    user_data["age"] = age

    height_format = st.radio('Select your height format: ', ('cms', 'meters', 'feet'))
    if height_format == 'cms':
        height = st.number_input('Centimeters', min_value=100, max_value=400, value=171)
    elif height_format == "meters":
        meter = st.number_input("Meters", min_value=1, max_value=7)
        height = round(meter * 100)
        st.write(f'Your height {height} cm')
    else:
        feet, inch = st.columns([3, 2])  # Create columns for feet and inches
        feet_value = feet.number_input("Feet", min_value=1, max_value=6)
        inch_value = inch.number_input("Inches", min_value=0, max_value=11)
        total_inches = (feet_value * 12) + inch_value
        height = round(total_inches * 2.54, 2)
        st.write(f"Your height is {height} cm")

    user_data["height"] = height

    # Weight
    weight = st.number_input("Weight (kg)", min_value=45, max_value=100, value=80)
    user_data["weight_kg"] = weight

    # Calculate BMI
    bmi = calculate_bmi(user_data["weight_kg"], user_data["height"])
    user_data["BMI"] = bmi 
    st.write(f"**Note** : *Your estimated Body Mass Index (BMI) is: {bmi:.2f} calories per day*")

    # Calculate BMR
    bmr = calculate_bmr(
        user_data["weight_kg"],
        user_data["height"],
        user_data["age"],
        user_data["gender"]
    )
    user_data["BMR"] = bmr
    st.write(f"**Note** : *Your estimated Basal Metabolic Rate (BMR) is: {bmr:.2f} calories per day*")

    medical_conditions = st.text_input("Any medical conditions we should be aware of?👨‍⚕️",value='no')
    user_data["medical_conditions"] = medical_conditions

    allergies = st.text_input("Any allergies?",value= 'no')
    user_data["allergies"] = allergies

    # Sidebar for Food Calorie Tracking
    st.sidebar.subheader("Food Calorie Tracking")
    custom_food_name = st.sidebar.text_input("Enter Food Name🌯🍱🍜🍲")
    calories_per_100g = st.sidebar.number_input("Calories per 100 grams")
    grams_consumed = st.sidebar.number_input("Grams Consumed")
    calculate_button = st.sidebar.button("Calculate Calories")
    if calculate_button:
        total_calories = calculate_calories(calories_per_100g, grams_consumed)
        st.sidebar.success(f"Total Calories: {total_calories:.2f}")
        user_data["food_data"] = {
            "food_name": custom_food_name,
            "grams": grams_consumed,
            "calories": total_calories
        }

    # Save data to JSON when a button is clicked
    if st.button("Save Data"):
        save_to_json(user_data) 
        #print(user_data)
        st.success("Data saved to user_data.json")
    get_health_recommendations() 

    return
# Display user data screen
def display_data_screen():
    st.subheader("Display User Data")
    email_to_display = st.session_state.current_email
    #if st.button("Display Data"):
    display_user_data(email_to_display)
    st.write("If data not store please add data click bellow button")
    st.button("Please Add Health data Here", on_click=navigate_to, args=("data_add_display",))
    # Add Logout Button
    st.button("Logout", on_click=navigate_to, args=("login",))  
    
# Main App Logic
if st.session_state.current_screen == "signup":
    signup_screen()
    
    st.button("Already have an account? Login Here", on_click=navigate_to, args=("login",))
elif st.session_state.current_screen == "login":
    login_screen()
elif st.session_state.current_screen == "data_add_display":
    data_add_screen()
    st.button("Display User Data", on_click=navigate_to, args=("display_data",))
elif st.session_state.current_screen == "display_data":
    display_data_screen()
# get_health_recommendations()
