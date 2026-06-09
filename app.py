import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import os
import urllib.request
from groq import Groq

st.set_page_config(page_title="AI Smart Short Drama Poster", page_icon="🎬", layout="centered")
st.title("🎬 AI Short Drama Poster Generator")
st.write("ဗီဒီယို တင်ပေးရုံဖြင့် ဘယ်/ညာ ဇာတ်ကောင်ပုံရိပ်များ ပေါင်းစပ်ပြီး ဆွဲဆောင်မှုရှိသော Short Drama ပိုစတာ ဖန်တီးပေးမည့် စနစ်")

# --- SideBar ---
st.sidebar.header("⚙️ Settings")
groq_api_key = st.sidebar.text_input("Groq API Key (Optional)", type="password", placeholder="gsk_...")
text_option = st.sidebar.radio("စာသားပုံစံ", ["AI ကို စဉ်းစားခိုင်းမည်", "ကိုယ်တိုင်ရေးမည်"])

custom_title = ""
if text_option == "ကိုယ်တိုင်ရေးမည်":
    custom_title = st.sidebar.text_input("စာသား ရေးပါ", value="ဒေါ်လာဘီလီယံချီ တန်ဖိုးရှိတဲ့ ဇနီးသည်ကို ပစ်ပယ်မိသောအခါ")

text_color = st.sidebar.color_picker("စာသားအရောင်", "#FFD700") # Default ရွှေရောင်

# --- DOWNLOAD PREMIUM MYANMAR FONT ---
FONT_PATH = "Pyidaungsu.ttf"
if not os.path.exists(FONT_PATH):
    try:
        font_url = "https://github.com/google/fonts/raw/main/ofl/pyidaungsu/Pyidaungsu-Regular.ttf"
        urllib.request.urlretrieve(font_url, FONT_PATH)
    except:
        pass

# --- MAIN WORKFLOW ---
uploaded_video = st.file_uploader("MP4 ဗီဒီယိုဖိုင် တင်ပါ", type=["mp4"])

if uploaded_video is not None:
    with open("temp_movie.mp4", "wb") as f:
        f.write(uploaded_video.read())
        
    st.info("🤖 AI က ဗီဒီယိုထဲမှ အကောင်းဆုံး ဇာတ်ကွက်များနှင့် ဇာတ်ကောင်များကို ထုတ်ယူနေပါသည်...")
    
    cap = cv2.VideoCapture("temp_movie.mp4")
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # ဗီဒီယိုထဲက မတူညီတဲ့ အခန်း ၅ ခန်းက frame ကို ယူမယ်
    sample_indices = np.linspace(int(total_frames*0.1), int(total_frames*0.9), 5, dtype=int)
    frames_list = []
    
    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # ပိုပြီး ပေါ့ပေါ့ပါးပါးနဲ့ အလုပ်မြန်အောင် ပုံဆိုဒ်ကို ညှိဖတ်မယ်
            frame = cv2.resize(frame, (720, 1280))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames_list.append(Image.fromarray(frame_rgb))
    cap.release()

    if len(frames_list) >= 2:
        poster_title = "ဒေါ်လာဘီလီယံချီ တန်ဖိုးရှိတဲ့ ဇနီးသည်ကို ပစ်ပယ်မိသောအခါ"
        
        if text_option == "AI ကို စဉ်းစားခိုင်းမည်":
            if groq_api_key:
                try:
                    client = Groq(api_key=groq_api_key)
                    completion = client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=[{"role": "user", "content": "Generate a dramatic dramatic Burmese drama title about wealth or romance. Return ONLY Burmese text."}],
                        temperature=0.7,
                    )
                    generated_text = completion.choices[0].message.content.strip()
                    if generated_text:
                        poster_title = generated_text.replace('"', '').replace("'", "")
                except Exception as e:
                    st.warning(f"API Error: {e}")
            else:
                st.warning("⚠️ API Key မရှိသဖြင့် မူလစာသားကို သုံးပါမည်။")
        else:
            poster_title = custom_title

        st.success(f"💡 ပိုစတာစာသား - **\"{poster_title}\"**")

        # --- SHORT DRAMA SPLIT STYLE COMPOSITION (1080 x 1920) ---
        poster_w, poster_h = 1080, 1920
        half_w = poster_w // 2  # 540px စီ ဘယ်၊ ညာ ခွဲမည်
        
        poster = Image.new("RGB", (poster_w, poster_h), (0,0,0))
        
        # ဘယ်၊ ညာ ပုံတွေအတွက် အချိုးကျ ဖြတ်ညှပ်ပေးမည့် စနစ် (540x1920 ခွဲထွက်ရန်)
        def crop_to_vertical_half(img, target_w, target_h):
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

        # သင့်ဗီဒီယိုထဲက ပထမပုံကို "ဘယ်ဘက်ခြမ်း"၊ ဒုတိယပုံကို "ညာဘက်ခြမ်း" အဖြစ် ပေါင်းစပ်မည်
        left_img = crop_to_vertical_half(frames_list[0], half_w, poster_h)
        right_img = crop_to_vertical_half(frames_list[1], half_w, poster_h)
        
        # Canvas ပေါ်တွင် ဘယ်နှင့်ညာ ကပ်ခြင်း
        poster.paste(left_img, (0, 0))
        poster.paste(right_img, (half_w, 0))
        
        # --- DRAW ADVANCED TEXT (TEXT WITH BLACK OUTLINE) ---
        draw = ImageDraw.Draw(poster)
        
        # စာလုံးအရွယ်အစားကို Short Drama ပုံစံအတိုင်း ထင်ထင်ရှားရှားဖြစ်အောင် ၇၅ အထိ မြှင့်ထားပါတယ်
        if os.path.exists(FONT_PATH):
            font = ImageFont.truetype(FONT_PATH, 75)
        else:
            font = ImageFont.load_default()
            
        # စာသားကို စာကြောင်းအရှည်ကြီး မဖြစ်စေဘဲ စကားလုံး ၅ လုံး/ ၆ လုံးစီ အလိုအလျောက် စာကြောင်းဖြတ်ပေးမည့် စနစ်
        words = poster_title.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line) + len(word) < 15:
                current_line += " " + word if current_line else word
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
            
        # စာကြောင်းအားလုံးရဲ့ အမြင့်စုစုပေါင်းကို တွက်ချက်ခြင်း
        line_heights = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_heights.append(bbox[3] - bbox[1])
            
        total_text_h = sum(line_heights) + (len(lines) - 1) * 20
        start_y = (poster_h - total_text_h) // 2 + 200 # အနည်းငယ် အောက်ဘက်သို့ ရွှေ့ပေးထားခြင်း
        
        # စာကြောင်းတစ်ကြောင်းစီကို အမည်းရောင် Stroke (ဘောင်) ဖြင့် ရေးဆွဲခြင်း
        current_y = start_y
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            line_x = (poster_w - line_w) // 2
            
            # စာလုံးဘောင် ထူထူလှလှလေး ဖြစ်စေရန် ပတ်ပတ်လည် ၄ ပစ်ဇယ် အမည်းရောင် အရင်ခြစ်ပေးခြင်း
            stroke_width = 5
            for adj_x in range(-stroke_width, stroke_width + 1):
                for adj_y in range(-stroke_width, stroke_width + 1):
                    if adj_x != 0 or adj_y != 0:
                        draw.text((line_x + adj_x, current_y + adj_y), line, fill="#000000", font=font)
                        
            # အပေါ်ကနေ မိမိရွေးချယ်ထားသော စာသားအရောင် (ဥပမာ ရွှေရောင်) ကို အထပ်လိုက် တင်ပေးခြင်း
            draw.text((line_x, current_y), line, fill=text_color, font=font)
            current_y += line_heights[i] + 20
            
        # --- PREVIEW & DOWNLOAD ---
        st.subheader("🖼️ AI Short Drama Poster Style")
        st.image(poster, use_container_width=True)
        
        img_buf = io.BytesIO()
        poster.save(img_buf, format="JPEG", quality=95)
        poster_bytes = img_buf.getvalue()
        
        st.download_button(
            label="📥 Short Drama Poster (9:16) ဒေါင်းလုဒ်ဆွဲရန်",
            data=poster_bytes,
            file_name="short_drama_poster.jpg",
            mime="image/jpeg"
        )
        
        if os.path.exists("temp_movie.mp4"):
            os.remove("temp_movie.mp4")
    else:
        st.error("ဗီဒီယိုဖိုင်မှ ပုံရိပ်လုံလောက်စွာ ထုတ်ယူ၍ မရပါ။")
            
