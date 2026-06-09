import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
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

text_color = st.sidebar.color_picker("စာသားအရောင်", "#FFD700") # ရွှေရောင်

# --- MAIN WORKFLOW ---
uploaded_video = st.file_uploader("MP4 ဗီဒီယိုဖိုင် တင်ပါ", type=["mp4"])

if uploaded_video is not None:
    with open("temp_movie.mp4", "wb") as f:
        f.write(uploaded_video.read())
        
    st.info("🤖 AI က ဗီဒီယိုထဲမှ အကောင်းဆုံး ဇာတ်ကွက်များနှင့် ဇာတ်ကောင်များကို ရှာဖွေနေပါသည်...")
    
    # OpenCV ဖြင့် ဗီဒီယိုထဲမှ Frame များကို စနစ်တကျ ထုတ်ယူခြင်း
    cap = cv2.VideoCapture("temp_movie.mp4")
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # မတူညီသော အခန်းကဏ္ဍများ ရရှိရန် အစ၊ အလယ်၊ အဆုံး Frame များကို ယူခြင်း
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
        # --- AI TEXT GENERATION (Groq) ---
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
                                "content": "Please generate a catchy, emotional, or dramatic 4-to-6 word movie/drama title in Myanmar (Burmese) language based on a family, love, or action theme. Return ONLY the Burmese text title, nothing else. Example: 'သွေးသားရင်းတို့ ဆုံစည်းရာ'"
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

        # --- 9:16 ADVANCED POSTER COMPOSITION (1080 x 1920) ---
        poster_w = 1080
        poster_h = 1920
        half_h = poster_h // 2  # 960px စီ ခွဲမည်
        
        poster = Image.new("RGB", (poster_w, poster_h), (0,0,0))
        
        # ပုံများကို အချိုးကျ ဖြတ်ညှပ်မည့် ကူညီချက်စနစ် (Center Crop)
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

        # အပေါ်ခြမ်း: ပုံ ၂ ပုံကို ဘေးချင်းယှဉ် ထည့်မည် (တစ်ပုံလျှင် 540x960 စီ)
        top_left = crop_to_ratio(frames_list[0], poster_w // 2, half_h)
        top_right = crop_to_ratio(frames_list[1], poster_w // 2, half_h)
        
        # အောက်ခြမ်း: ပုံ ၁ ပုံကို အပြည့်ထည့်မည် (1080x960)
        bottom_full = crop_to_ratio(frames_list[2], poster_w, half_h)
        
        # Canvas ပေါ်တွင် ပုံများ စနစ်တကျ ကပ်ခြင်း
        poster.paste(top_left, (0, 0))
        poster.paste(top_right, (poster_w // 2, 0))
        poster.paste(bottom_full, (0, half_h))
        
        # --- ပုံနှစ်ခုကြား အလယ်စာသားကို လှလှပပ ထည့်သွင်းခြင်း ---
        draw = ImageDraw.Draw(poster)
        
        try:
            font = ImageFont.load_default() # စာလုံးအရွယ်အစား ပိုကြီးချင်ပါက စက်ထဲမှ .ttf ဖောင့်လမ်းကြောင်း ထည့်ပေးနိုင်သည်
        except:
            font = ImageFont.load_default()
            
        text_bbox = draw.textbbox((0, 0), poster_title, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        
        # ပိုစတာရဲ့ အလယ်တည့်တည့် (အပေါ်အောက် ဆုံချက်) နေရာ
        x_pos = (poster_w - text_w) // 2
        y_pos = half_h - (text_h // 2)
        
        # စာသား ပိုမိုပေါ်လွင်ပြီး ဖတ်ရလွယ်ကူစေရန် နောက်ခံ Shadow Box ထည့်ခြင်း
        padding_w, padding_h = 50, 30
        draw.rectangle(
            [x_pos - padding_w, y_pos - padding_h, x_pos + text_w + padding_w, y_pos + text_h + padding_h], 
            fill=(0, 0, 0, 180)
        )
        
        # စာသား ရေးသားခြင်း
        draw.text((x_pos, y_pos), poster_title, fill=text_color, font=font)
        
        # --- SHOW PREVIEW & DOWNLOAD ---
        st.subheader("🖼️ AI အလိုအလျောက် ဖန်တီးပေးလိုက်သော ပိုစတာ")
        st.image(poster, use_container_width=True)
        
        img_buf = io.BytesIO()
        poster.save(img_buf, format="JPEG", quality=95)
        poster_bytes = img_buf.getvalue()
        
        st.download_button(
            label="📥 9:16 Movie Poster ကို ရယူရန် နှိပ်ပါ",
            data=poster_bytes,
            file_name="ai_perfect_poster.jpg",
            mime="image/jpeg"
        )
    else:
        st.error("ဗီဒီယိုဖိုင်မှ ပုံရိပ်လုံလောက်စွာ ထုတ်ယူ၍ မရပါ။")
                
