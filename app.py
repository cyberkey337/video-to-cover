import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import os
from groq import Groq

st.set_page_config(page_title="AI Smart Drama Poster", page_icon="🎬", layout="centered")

st.title("🎬 AI Smart Drama Poster Generator")
st.write("ဗီဒီယို တင်ပေးရုံဖြင့် AI က ဇာတ်ကောင်များကို ရွေးချယ်ပြီး ဆွဲဆောင်မှုရှိသော ပိုစတာကို စာသားနှင့်တကွ ဖန်တီးပေးမည့် စနစ်")

# --- SIDEBAR: SETTINGS ---
st.sidebar.header("⚙️ API Configuration")
groq_api_key = st.sidebar.text_input("Groq API Key", type="password", placeholder="gsk_...")

text_option = st.sidebar.radio("စာသား ထည့်သွင်းမှုပုံစံ", ["AI ကို အလိုအလျောက် စဉ်းစားခိုင်းမည်", "ကိုယ်တိုင် စိတ်ကြိုက်ရေးမည်"])
custom_title = ""
if text_option == "ကိုယ်တိုင် စိတ်ကြိုက်ရေးမည်":
    custom_title = st.sidebar.text_input("ထည့်ချင်သည့် စာသား ရေးပါ", value="သွေးသားရင်းတို့ ဆုံစည်းရာ")

text_color = st.sidebar.color_picker("စာသားအရောင်", "#FFD700")

# --- MAIN WORKFLOW ---
uploaded_video = st.file_uploader("MP4 ဗီဒီယိုဖိုင် တင်ပါ", type=["mp4"])

if uploaded_video is not None:
    with open("temp_movie.mp4", "wb") as f:
        f.write(uploaded_video.read())
        
    st.info("🤖 AI က ဗီဒီယိုထဲမှ အကောင်းဆုံး ဇာတ်ကွက်များနှင့် ဇာတ်ကောင်များကို ရှာဖွေနေပါသည်...")
    
    cap = cv2.VideoCapture("temp_movie.mp4")
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    sample_indices = np.linspace(int(total_frames*0.1), int(total_frames*0.9), 4, dtype=int)
    frames_list = []
    
    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames_list.append(Image.fromarray(frame_rgb))
            
    cap.release()

    if len(frames_list) >= 3:
        poster_title = "သွေးသားရင်းတို့ ဆုံစည်းရာ"
        
        if text_option == "AI ကို အလိုအလျောက် စဉ်းစားခိုင်းမည်":
            if groq_api_key:
                try:
                    client = Groq(api_key=groq_api_key)
                    completion = client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=[
                            {
                                "role": "user",
                                "content": "Please generate a catchy, emotional, or dramatic 4-to-6 word movie/drama title in Myanmar (Burmese) language. Return ONLY the Burmese text title, nothing else."
                            }
                        ],
                        temperature=0.7,
                    )
                    generated_text = completion.choices[0].message.content.strip()
                    if generated_text:
                        poster_title = generated_text.replace('"', '').replace("'", "")
                except Exception as e:
                    st.warning(f"Groq API Error: {e} ကြောင့် မူလစာသားကိုသာ သုံးထားပါသည်။")
            else:
                st.warning("⚠️ Groq API Key မရှိသဖြင့် AI မှ စာသား မစဉ်းစားပေးနိုင်ပါ။ မူလစာသားကို သုံးပါမည်။")
        else:
            poster_title = custom_title

        st.success(f"💡 AI စဉ်းစားပေးထားသော စာသား - **\"{poster_title}\"**")

        poster_w = 1080
        poster_h = 1920
        half_h = poster_h // 2
        
        poster = Image.new("RGB", (poster_w, poster_h), (0,0,0))
        
        def crop_to_ratio(img, target_w, target_h):
            orig_w, orig_h = img.size
            target_ratio = target_w / target_h
            orig_ratio = orig_w / orig_h
            if orig_ratio > target_ratio:
                new_w = int(target_ratio * orig_h)
                left = (orig_w - new_w) // 2
                return img.crop((left, 0, left + new_w, orig_h)).resize((target_w, target_h), Image.Resampling.LANCZOS)
            else:
                new_h = int(orig_w / target_ratio)
                top = (orig_h - new_h) // 2
                return img.crop((0, top, orig_w, top + new_h)).resize((target_w, target_h), Image.Resampling.LANCZOS)

        top_left = crop_to_ratio(frames_list[0], poster_w // 2, half_h)
        top_right = crop_to_ratio(frames_list[1], poster_w // 2, half_h)
        bottom_full = crop_to_ratio(frames_list[2], poster_w, half_h)
        
        poster.paste(top_left, (0, 0))
        poster.paste(top_right, (poster_w // 2, 0))
        poster.paste(bottom_full, (0, half_h))
        
        draw = ImageDraw.Draw(poster)
        font = ImageFont.load_default()
            
        text_bbox = draw.textbbox((0, 0), poster_title, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        
        x_pos = (poster_w - text_w) // 2
        y_pos = half_h - (text_h // 2)
        
        padding_w, padding_h = 50, 30
        draw.rectangle(
            [x_pos - padding_w, y_pos - padding_h, x_pos + text_w + padding_w, y_pos + text_h + padding_h], 
            fill=(0, 0, 0, 180)
        )
        
        draw.text((x_pos, y_pos), poster_title, fill=text_color, font=font)
        
        st.subheader("🖼️ AI အလိုအလျောက် ဖန်တီးပေးလိုက်သော ပိုစတာ")
        st.image(poster, use_
        
