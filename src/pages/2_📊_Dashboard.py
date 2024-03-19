import streamlit as st
import pandas as pd
import cv2
import numpy as np
import os
from pymongo import MongoClient
from datetime import datetime, timedelta
from Homepage import get_session_state, set_session_state
from streamlit_extras.switch_page_button import switch_page
from PIL import Image, ImageDraw, ImageOps
import io
import requests
from uuid import uuid4
from datetime import datetime, timedelta
import plotly.graph_objs as go
import plotly.express as px

# Connect to MongoDB
client = MongoClient("mongodb+srv://odin:qsaw1234@odin.2symxyt.mongodb.net/test")
db = client.Attendance
users = db.users
data = db.data

def is_user_logged_in():
    return get_session_state().get("is_logged_in", False)

st.title("User Dashboard")

def add_logo():
    image_url = "https://github.com/Sejal00067/ODIN-MAIN/blob/main/src/Background_I.jpg"
    st.markdown(
        f"""
        <style>
            [data-testid="stSidebarNav"] {{
                background-image: url({image_url});
                max-width: 300px;
                min-height: 100vh;
                background-repeat: no-repeat;
                padding-top: 80px;
                background-position: 20px 20px;
                background-size: 50%;
            }}
            [data-testid="stSidebarNav"]::before {{
                content: "Attendance";
                padding-top: 20px;
                margin-left: 20px;
                margin-top: 20px;
                font-size: 30px;
                position: relative;
                top: 90px;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def add_background():
    st.markdown(
        """
        <style>
            .reportview-container {
                background: url('https://github.com/Sejal00067/ODIN-MAIN/raw/main/src/Background_I.jpg') no-repeat center center fixed;
                background-size: cover;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

add_background()

if not is_user_logged_in():
    add_logo()
    st.error("You need to log in to access this page.")
    st.stop()


# Define today's date
today = datetime.now().strftime("%Y-%m-%d")

def get_user_state():
    # Get the session state for the current session ID
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid4())
    if st.session_state.session_id not in st.session_state:
        st.session_state[st.session_state.session_id] = {}
    return st.session_state[st.session_state.session_id]

# Add input field for subject name
PRN = st.text_input("Enter student PRN:")


def crop_signatures(image, bounding_boxes):
    cropped_signatures = []
    for i, box_list in enumerate(bounding_boxes):
        for box in box_list:
            if len(box) == 4:
                x, y, w, h = box
                signature = image[y:y+h, x:x+w]
                cropped_signatures.append(signature)
                st.image(signature, caption=f"Cropped signature {i+1}", use_column_width=True)
            else:
                st.warning(f"Ignoring invalid bounding box format in list {i+1}")
    return cropped_signatures




uploaded_file = st.file_uploader("Upload Attendance Sheet", type=['jpg', 'jpeg', 'png'])

# Define the bounding boxes for each day
bounding_boxes_by_day = {
    "Monday": [
        # (1550, 331, 231, 90),
        (552, 235, 190, 72),
        (552, 309, 189, 73),
        (552, 381, 187, 71),
        (551, 456, 190, 70),
        (550, 526, 189, 74),
        (546, 601, 192, 71),
        (545, 673, 192, 76),
        (540, 750, 193, 72),
        (540, 824, 193, 74),
        (539, 901, 194, 74),
    ],
    "Tuesday": [
        (1812, 334, 234, 88),
        (743, 236, 189, 70),
        (742, 307, 188, 77),
        (743, 382, 186, 77),
        (742, 456, 185, 73),
        (741, 528, 186, 75),
        (739, 603, 186, 70),
        (738, 674, 186, 73),
        (737, 749, 189, 76),
        (735, 824, 192, 77),
        (737, 903, 189, 75),
    ],
    "Wednesday": [
        (764, 425, 232, 89),
        (933, 237, 186, 70),
        (931, 310, 188, 73),
        (931, 382, 188, 77),
        (931, 463, 188, 66),
        (930, 530, 188, 75),
        (928, 604, 189, 73),
        (928, 675, 188, 76),
        (928, 750, 189, 76),
        (928, 826, 189, 77),
        (926, 903, 195, 75),
    ],
    "Thursday": [
        (1120, 240, 192, 68),
        (1122, 311, 189, 77),
        (1119, 385, 190, 75),
        (1120, 462, 188, 69),
        (1119, 533, 189, 72),
        (1119, 603, 188, 73),
        (1119, 680, 186, 72),
        (1119, 754, 188, 75),
        (1117, 827, 193, 75),
        (1123, 905, 186, 73),
    ],
    "Friday": [
        (1313, 239, 189, 72),
        (1309, 311, 190, 77),
        (1310, 388, 188, 72),
        (1310, 460, 188, 76),
        (1310, 534, 186, 73),
        (1310, 605, 186, 75),
        (1310, 676, 185, 79),
        (1309, 755, 186, 73),
        (1309, 824, 189, 80),
        (1313, 906, 185, 72),
    ],
}


# Get user-selected days
selected_days = st.multiselect("Select Days of the Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])

# Filter bounding boxes based on selected days
filtered_bounding_boxes = [bounding_boxes_by_day[day] for day in selected_days]

# Generate roll numbers for students (assuming 100 students)
roll_numbers = list(range(1, 101))

# Printing the roll numbers
for roll_number, bounding_boxes in zip(roll_numbers, filtered_bounding_boxes):
    print(f"Roll Number: {roll_number}")
    print("Bounding Boxes:")
    for box in bounding_boxes:
        print(box)

if uploaded_file is not None: 
    current_time = datetime.now().strftime("%Y-%m-%d %H-%M")
    image = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), cv2.IMREAD_COLOR)
    st.image(image, caption="Original Image", use_column_width=True)

    cropped_signatures = crop_signatures(image, filtered_bounding_boxes)


    if st.button("Save Signatures"):
        current_time = datetime.now().strftime("%Y-%m-%d ")
        folder_path = f"attendance/{current_time}"
        os.makedirs(folder_path, exist_ok=True)
        for i, signature in enumerate(cropped_signatures):
            cv2.imwrite(f"{folder_path}/{i}.png", signature)
        st.success("Signatures saved successfully!")


if st.button("Submit"):
    # Fetch the data for the current week for the entered subject name and teacher name
    week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
    week_data = list(data.find({"date_verified": {"$gte": week_start}, "PRN": PRN}))

    if len(week_data) > 0:
        # Create a DataFrame for the week's data
        df = pd.DataFrame(week_data)
# Create a pie chart to show number of students present today
        total_students = 20
        present_today = df[df['date_verified'] == today]['Name'].nunique()
        absent_today = total_students - present_today

        chart_data = pd.DataFrame({
            'status': ['Present', 'Absent'],
            'students': [present_today, absent_today]
        })
        
        st.subheader('Attendance Today')
        st.write(chart_data.set_index('status'))
        st.plotly_chart(px.pie(chart_data, values='students', names='status'))

        # Create a bar chart to show number of students present each day this week
        attendance_by_day = df.groupby('date_verified')['Name'].nunique().reset_index()
        bar_chart = st.container()
        with bar_chart:
            st.subheader('Attendance This Week')
            st.bar_chart(attendance_by_day.set_index('date_verified'))

        # Create a table to show student names and attendance count for the week
        attendance_table = st.container()
        with attendance_table:
            st.subheader('Attendance Table')
            attendance_count = df.groupby('Name')['date_verified'].nunique().reset_index()
            attendance_count.columns = ['Name', 'Attendance Count']
            st.write(attendance_count)
    else:
        st.warning("No data available for the entered student PRN for this week.")

# Redirect to Homepage button
go_to_homepage = st.button("Homepage")
if go_to_homepage:
    switch_page("Homepage")

# Main function
def main():
    add_logo() # Call the function to add logo to sidebar
    # st.title("Odin App")

    session_state = get_session_state()


    if  session_state.get("is_logged_in", False):
        add_logo()
        # Create a sidebar container for logged in user info
        user_info_container = st.sidebar.container()
        with user_info_container:
            st.subheader(f"Logged in as {session_state['username']}")

            user = users.find_one({"username": get_session_state().get("username")})
            if user:
                # Show profile photo
                profile_photo = user.get("profile_photo")
                if profile_photo:
                    image = Image.open(io.BytesIO(profile_photo))
                    image = image.resize((100, 100))
                    image = image.convert("RGBA")

                    # Create circular mask
                    size = (100, 100)
                    mask = Image.new('L', size, 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0) + size, fill=255)

                    # Apply mask to image
                    output = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
                    output.putalpha(mask)

                    output_bytes = io.BytesIO()
                    output.save(output_bytes, format='PNG')
                    output_bytes.seek(0)

                    # Show profile photo
                    st.image(output_bytes, width=100)

        
        # Create a logout button container
        logout_container = st.sidebar.container()
        with logout_container:
            st.button("Logout", on_click=logout, key="logout_button")

def logout():
    set_session_state({"is_logged_in": False, "username": None})
    st._rerun()

if __name__ == "__main__":
    main()