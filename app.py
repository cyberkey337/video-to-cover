import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import os
from groq import Groq

st.set_page_config(page_title="AI Smart Drama Poster", page_icon="🎬", layout="centered")

st.title("🎬 AI Smart Drama Poster Generator")
st.write("ဗီဒီယို တင်ပေးရုံဖြင့် AI က ဇာတ်ကောင် ၃ ဦးအား အလိုအလျောက် ရွေးချယ်ပြီး ဆွဲဆောင်မှုရှိသော စာသားကိုပါ စဉ်းစားပေးမည့် စနစ်")

# --- SIDEBAR: SETTINGS ---
st.sidebar.header("⚙️ API Configuration")
groq_api_key = st.sidebar.text_input("Groq API Key", type="password", placeholder="gsk_...")

# စာသားအတွက် Option
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
        
    st.info("🤖 AI က ဗီဒီယိုထဲမှ အဓိက ဇာတ်ကောင်များနှင့် ဇာတ်ကွက်ကို လေ့လာနေပါသည်...")
    
    # --- STEP 1: OPENCV FACE DETECTION ---
    # လူမျက်နှာ ရှာဖွေသည့် စနစ်ကို ဖွင့်ခြင်း
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    cap = cv2.VideoCapture("temp_movie.mp4")
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    detected_faces = []
    
    # ဗီဒီယိုထဲက Frame များကို ကျော်ပြီး ရှာဖွေခြင်း (မျက်နှာ ၃ ခု မတူတာ မိအောင်)
    step = max(1, total_frames // 20)
    for f_idx in range(0, total_frames, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
        
        for (x, y, w, h) in faces:
            # မျက်နှာကို ခေါင်းပိုင်း အပြည့်အဝ ပါအောင် ဘေးဘောင် ချဲ့ပြီး ဖြတ်ယူခြင်း
            pad = int(w * 0.4)
            y_start = max(0, y - pad)
            y_end = min(frame.shape[0], y + h + pad)
            x_start = max(0, x - pad)
            x_end = min(frame.shape[1], x + w + pad)
            
            face_crop = frame[y_start:y_end, x_start:x_end]
            face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
            pil_face = Image.fromarray(face_rgb)
            
            # ပုံစံတူလွန်းတာတွေ ဖယ်ဖို့အတွက် နမူနာသိမ်းဆည်းခြင်း
            detected_faces.append(pil_face)
            if len(detected_faces) >= 3:
                break
        if len(detected_faces) >= 3:
            break
            
    cap.release()

    # အကယ်၍ ဗီဒီယိုထဲမှာ မျက်နှာ မရှာတွေ့ရင် Frame အလိုက် Random ၃ ပုံ ယူပေးခြင်း
    if len(detected_faces) < 3:
        cap = cv2.VideoCapture("temp_movie.mp4")
        sample_indices = np.linspace(0, total_frames - 1, 3, dtype=int)
        detected_faces = []
        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                detected_faces.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        cap.release()

    # --- STEP 2: AI TEXT GENERATION (Groq) ---
    poster_title = "မုန်တိုင်းအလွန် စောင့်မျှော်သူများ" # Default စာသား
    
    if text_option == "AI ကို အလိုအလျောက် စဉ်းစားခိုင်းမည်":
        if groq_api_key:
            try:
                client = Groq(api_key=groq_api_key)
                # ဗီဒီယိုရဲ့ သဘောသဘာဝကို အခြေခံပြီး စာသားလှလှလေး စဉ်းစားခိုင်းခြင်း
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

    # --- STEP 3: 9:16 TRIPLE POSTER COMPOSITION ---
    poster_w = 1080
    poster_h = 1920
    segment_h = poster_h // 3 # ပုံ ၃ ပုံဖြစ်သဖြင့် တစ်ပုံလျှင် 640px စီ ရရှိမည်
    
    poster = Image.new("RGB", (poster_w, poster_h))
    
    # ပုံ ၃ ပုံလုံးကို 1080x640 အချိုးကျ Center Crop လုပ်ပြီး ပေါင်းစပ်ခြင်း
    for i in range(3):
        img = detected_faces[i]
        orig_w, orig_h = img.size
        target_w, target_h = poster_w, segment_h
        
        target_ratio = target_w / target_h
        orig_ratio = orig_w / orig_h
        
        if orig_ratio > target_ratio:
            new_w = int(target_ratio * orig_h)
            left = (orig_w - new_w) // 2
            top = 0
            img_cropped = img.crop((left, top, left + new_w, orig_h))
        else:
            new_h = int(orig_w / target_ratio)
            left = 0
            top = (orig_h - new_h) // 2
            img_cropped = img.crop((left, top, orig_w, top + new_h))
            
        img_resized = img_cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
        poster.paste(img_resized, (0, i * segment_h))

    # --- STEP 4: ADD SMART TEXT OVERLAY ---
    draw = ImageDraw.Draw(poster)
    
    try:
        font = ImageFont.load_default() # အရွယ်အစား ကြီးချင်လျှင် .ttf ဖိုင် ထည့်ပေးရန် လိုအပ်ပါသည်
    except:
        font = ImageFont.load_default()
        
    text_bbox = draw.textbbox((0, 0), poster_title, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    
    # စာသားကို ဒုတိယပုံရဲ့ အလယ် (ပိုစတာရဲ့ စင်တာ) တည့်တည့်မှာ တင်ခြင်း
    x_pos = (poster_w - text_w) // 2
    y_pos = (poster_h // 2) - (text_h // 2)
    
    # စာသား နောက်ခံ ဘောင်အနက်ရောင်လေး ခံပေးခြင်း
    padding = 40
    draw.rectangle(
        [x_pos - padding, y_pos - padding, x_pos + text_w + padding, y_pos + text_h + padding], 
        fill=(0, 0, 0, 170)
    )
    
    # စာသားဆွဲခြင်း
    draw.text((x_pos, y_pos), poster_title, fill=text_color, font=font)
    
    # --- SHOW PREVIEW & DOWNLOAD ---
    st.subheader("🖼️ AI အလိုအလျောက် ဖန်တီးပေးလိုက်သော ပိုစတာ")
    st.image(poster, use_container_width=True)
    
    img_buf = io.BytesIO()
    poster.save(img_buf, format="JPEG", quality=95)
    poster_bytes = img_buf.getvalue()
    
    st.download_button(
        label="📥 9:16 AI Movie Poster ကို ရယူရန် နှိပ်ပါ",
        data=poster_bytes,
        file_name="ai_smart_poster.jpg",
        mime="image/jpeg"
    )
    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # Server မဒေါင်းအောင် ပုံစိုက်ကို အနည်းငယ် လျှော့ချဖတ်မယ်
            frame = cv2.resize(frame, (640, 360))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames_list.append(Image.fromarray(frame_rgb))
            
    cap.release()

    if len(frames_list) >= 2:
        st.warning("⚠️ ဗီဒီယိုထဲက ပုံများကို အောက်ပါ Slider ဖြင့် စိတ်ကြိုက် ရွေးချယ်ပေးပါ။")
        top_idx = st.slider("အပေါ်ပိုင်း (ဇာတ်ကောင်ပုံ) အတွက် Frame ရွေးပါ", 0, len(frames_list)-1, 1)
        bottom_idx = st.slider("အောက်ပိုင်း (နောက်ခံဇာတ်ကွက်) အတွက် Frame ရွေးပါ", 0, len(frames_list)-1, 3)
        top_img = frames_list[top_idx]
        bottom_img = frames_list[bottom_idx]

        # --- 9:16 ပိုစတာ ပေါင်းစပ်ဖန်တီးခြင်း ---
        poster_w, poster_h = 720, 1280  # ဖုန်းအတွက် အဆင်ပြေမယ့် ပေါ့ပါးတဲ့ 9:16 ဆိုဒ်
        half_h = poster_h // 2
        
        top_resized = top_img.resize((poster_w, half_h), Image.Resampling.LANCZOS)
        bottom_resized = bottom_img.resize((poster_w, half_h), Image.Resampling.LANCZOS)
        
        poster = Image.new("RGB", (poster_w, poster_h))
        poster.paste(top_resized, (0, 0))
        poster.paste(bottom_resized, (0, half_h))
        
        # --- အလယ်မြှုပ်ကြောင်း (Blending Effect) ---
        # မှုန်ဝါးဝါး Gradient လေးဖြင့် ပုံနှစ်ပုံကြား ဆက်ကြောင်းကို ဖျောက်ခြင်း
        mask = Image.new("L", (poster_w, poster_h), 255)
        mask_draw = ImageDraw.Draw(mask)
        for y in range(half_h - 80, half_h + 80):
            alpha = int((y - (half_h - 80)) / 160 * 255)
            mask_draw.line([(0, y), (poster_w, y)], fill=alpha)
            
        # --- စာသား ထည့်သွင်းခြင်း ---
        text_draw = ImageDraw.Draw(poster)
        font = ImageFont.load_default() # စက်တိုင်းအလုပ်လုပ်မယ့် ပုံသေ Font

        # စာသား တည့်တည့်တွက်ချက်ခြင်း
        text_bbox = text_draw.textbbox((0, 0), poster_title, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        
        x_pos = (poster_w - text_w) // 2
        y_pos = half_h - (text_h // 2)
        
        # စာသား နောက်ခံ အရိပ်လိုင်း (Shadow effect)
        text_draw.text((x_pos+2, y_pos+2), poster_title, fill="#000000", font=font)
        text_draw.text((x_pos, y_pos), poster_title, fill=text_color, font=font)
        
        # --- Preview & Download ---
        st.subheader("🖼️ ထွက်လာမည့် AI Drama Poster Preview")
        st.image(poster, use_container_width=True)
        
        img_buf = io.BytesIO()
        poster.save(img_buf, format="JPEG", quality=90)
        poster_bytes = img_buf.getvalue()
        
        st.download_button(
            label="📥 9:16 Movie Poster ကို ဒေါင်းလုဒ်ဆွဲရန် နှိပ်ပါ",
            data=poster_bytes,
            file_name="ai_drama_poster.jpg",
            mime="image/jpeg"
        )
        
        # ယာယီဖိုင်အား ဖျက်သိမ်းခြင်း
        if os.path.exists("temp_movie.mp4"):
            os.remove("temp_movie.mp4")
    else:
        st.error("ဗီဒီယိုဖိုင်မှ ပုံရိပ်များ ထုတ်ယူ၍ မရပါ။")
    # OpenCV ဖြင့် ဗီဒီယိုကို ဖတ်ခြင်း
    video = cv2.VideoCapture("temp_video.mp4")
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    
    if total_frames > 0:
        # ဗီဒီယိုထဲက အလယ်ပိုင်း၊ အစပိုင်း၊ အဆုံးပိုင်း Frame တွေကို နမူနာထုတ်ပြရန် Slider ထည့်ခြင်း
        st.subheader("📸 Cover လုပ်လိုသည့် ပုံရိပ်ကို ရွေးချယ်ပါ")
        frame_idx = st.slider("ဗီဒီယို Frame ရွေးရန်", 0, total_frames - 1, int(total_frames / 2))
        
        # ရွေးချယ်လိုက်သော Frame ကို ဖတ်ခြင်း
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = video.read()
        
        if success:
            # OpenCV (BGR) မှ RGB သို့ ပြောင်းခြင်း
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            
            # --- 9:16 TikTok Ratio သို့ ပြောင်းလဲခြင်း ---
            # TikTok Cover Standard Size: 1080 x 1920
            target_w, target_h = 1080, 1920
            orig_w, orig_h = img.size
            
            # 9:16 ဖြစ်အောင် ဖြတ်ညှပ်ခြင်း (Center Crop)
            img_ratio = orig_w / orig_h
            target_ratio = target_w / target_h
            
            if img_ratio > target_ratio:
                # ပုံက ပိုပြားနေလျှင် ဘေးဘယ်ညာကို ဖြတ်မည်
                new_w = int(target_ratio * orig_h)
                left = (orig_w - new_w) / 2
                top = 0
                right = left + new_w
                bottom = orig_h
            else:
                # ပုံက ပိုရှည်နေလျှင် အပေါ်အောက်ကို ဖြတ်မည်
                new_h = int(orig_w / target_ratio)
                left = 0
                top = (orig_h - new_h) / 2
                right = orig_w
                bottom = top + new_h
                
            img_cropped = img.crop((left, top, right, bottom))
            img_resized = img_cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            # --- စာသားထည့်သွင်းခြင်း ---
            draw = ImageDraw.Draw(img_resized)
            
            # Default Font သုံးထားပါသည် (မြန်မာစာအတွက်ဆိုလျှင် ပိုမိုလှပသော မည်သည့် font ကိုမဆို လမ်းကြောင်းပေးသုံးနိုင်ပါသည်)
            try:
                # တကယ်လို့ ကိုယ့်စက်ထဲမှာ Font ရှိရင် ဒီနေရာမှာ လမ်းကြောင်းပြောင်းပေးလို့ရပါတယ်
                font = ImageFont.load_default()
                # Font size ကြီးချင်ရင် သီးသန့် font ဖိုင် (.ttf) သုံးရပါမယ်
            except:
                font = ImageFont.load_default()
            
            # စာသားကို အလယ်တည့်တည့်မှာ နေရာချခြင်း
            text_w, text_h = draw.textbbox((0, 0), cover_text, font=font)[2:]
            text_x = (target_w - text_w) / 2
            text_y = (target_h - text_h) / 2  # ပုံရဲ့ အလယ်တည့်တည့်
            
            # စာသား နောက်ခံ ဘောင်အမည်းလေး ထည့်ပေးခြင်း (စာသားပိုပေါ်လွင်စေရန်)
            draw.rectangle([text_x - 20, text_y - 20, text_x + text_w + 20, text_y + text_h + 20], fill=(0, 0, 0, 100))
            # စာသားရေးခြင်း
            draw.text((text_x, text_y), cover_text, fill=text_color, font=font)
            
            # --- ပြသခြင်းနှင့် Download လုပ်ရန် ပြင်ဆင်ခြင်း ---
            st.image(img_resized, caption="TikTok Cover Preview (9:16)", use_container_width=True)
            
            # ပုံကို Memory ထဲသိမ်းပြီး Download Button ပြုလုပ်ခြင်း
            buf = io.BytesIO()
            img_resized.save(buf, format="JPEG")
            byte_im = buf.getvalue()
            
            st.download_button(
                label="📥 TikTok Cover ပုံကို ရယူရန် နှိပ်ပါ",
                data=byte_im,
                file_name="tiktok_cover.jpg",
                mime="image/jpeg"
            )
            
    video.release()
    
