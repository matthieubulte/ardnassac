import streamlit as st
import sqlite3
from dotenv import load_dotenv; load_dotenv()
import os
import pandas as pd
import json
import cv2
import datetime

conn = sqlite3.connect(os.environ['DB_FILE'])

def humanize_date_difference(otherdate):
    if isinstance(otherdate, str):
        otherdate = datetime.datetime.fromisoformat(otherdate)

    now = datetime.datetime.now()

    dt = now - otherdate
    offset = dt.seconds + (dt.days * 60*60*24)

    delta_s = offset % 60
    offset /= 60
    delta_m = offset % 60
    offset /= 60
    delta_h = offset % 24
    offset /= 24
    delta_d = offset

    if delta_d > 1:
        if delta_d > 6:
            date = now + datetime.timedelta(days=-delta_d, hours=-delta_h, minutes=-delta_m)
            return date.strftime('%A, %Y %B %m, %H:%I')
        else:
            wday = now + datetime.timedelta(days=-delta_d)
            return wday.strftime('%A')
    
    if delta_d == 1:
        return "Yesterday"
    if delta_h >= 1:
        return "%dh%dm ago" % (delta_h, delta_m)
    if delta_m >= 1:
        return "%dm%ds ago" % (delta_m, delta_s)
    else:
        return "%ds ago" % delta_s

def get_num_entries():
    return conn.cursor().execute('select count(1) from entries').fetchone()[0]

@st.cache_data
def search(search_str):
    return pd.read_sql(f"select * from entries where ocr_text like '%{search_str}%' order by created_timestamp desc", con=conn)
    
def ocr_data_iloc(ocr_data, i):
    return dict(left=ocr_data['left'][i],top=ocr_data['top'][i],width=ocr_data['width'][i],height=ocr_data['height'][i],conf=ocr_data['conf'][i],text=ocr_data['text'][i])

@st.cache_data
def load_image(path):
    return cv2.imread(path)

@st.cache_data
def show_entry(search_str, entry):
    print(f'render {entry["file"]}' )
    ocr_data = json.loads(entry['ocr_data'])
    n_boxes = len(ocr_data['level'])
    img = cv2.imread(entry['file'])

    for i in range(n_boxes):
        ocr_i = ocr_data_iloc(ocr_data, i)
        if search_str.lower() in ocr_i['text'].lower():
            cv2.rectangle(img, (ocr_i['left'] - 2, ocr_i['top'] - 2), (ocr_i['left'] + ocr_i['width'] + 2, ocr_i['top'] + ocr_i['height'] + 2), (0, 255, 0), 4)

    st.image(img, channels='BGR')

st.markdown(f"<h1 style='text-align: center'>Ardnassac</h1>", unsafe_allow_html=True)

st.text_input('', placeholder="Search your past...", key="search_str")

if st.session_state.search_str:
    if 'shown_idx' not in st.session_state or st.session_state.last_search != st.session_state.search_str:
        st.session_state['shown_idx'] = 0
        st.session_state['last_search'] = st.session_state.search_str

    s = search(st.session_state.search_str)
    records = s.to_dict('records')

    if len(records):
        entry = records[st.session_state.shown_idx]
        
        col1, col2, col3 = st.columns([1,4,1])
        if st.session_state.shown_idx < len(records)-1 and col1.button('← Earlier'):
            st.session_state.shown_idx += 1
            
        col2.markdown(f"<h3 style='text-align: center'>{humanize_date_difference(entry['created_timestamp'])}</h3>", unsafe_allow_html=True)

        if st.session_state.shown_idx > 0 and col3.button('Later →'):
            st.session_state.shown_idx -= 1

        show_entry(st.session_state.search_str, entry)

        cols = st.columns([1,1,1,1,1,2,1,1,1,1,1])
        for i in range(-5, 6):
            e_idx = st.session_state.shown_idx - i
            if e_idx < 0 or e_idx >= len(records):
                continue
            with cols[5 + i]:
                img = load_image(records[e_idx]['file'])
                st.image(img, channels='BGR')
    else:
        st.text('Maybe it was a dream?')



        


