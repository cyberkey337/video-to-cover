import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io

# Page Setting
st.set_page_config(page_title="AI Drama Poster Generator", page_icon="🎬", layout="centered")

st.title("🎬 AI Drama Poster & Cover Generator")
st.write("ဗီဒီယို တင်ပေးလိုက်ရုံနဲ့ အပေါ်အောက် ဇာတ်ကောင်ပုံရိပ်တွေ ပေါင်းစပ်ပြီး ဇာတ်လမ်းပိုစတာ ဖန်တီးပေးမယ့် App")

# --- SIDEBAR: SETTINGS ---
st.sidebar.header("⚙️ Configuration")
groq_api_key = st.sidebar.text_input("Groq API Key (Optional)", type="password", placeholder="gsk_...")
poster_title = st.sidebar.text_input("ပိုစတာပေါ်တွင် ထည့်မည့် စာသား", value="သွေးသားရင်းတို့ ဆုံစည်းရာ")
text_color = st.sidebar.color_picker("စာသားအရောင်", "#FFD700") # Default ရွှေရောင်

# --- MAIN UI ---
uploaded_video = st.file_uploader("MP4 ဗီဒီယိုဖိုင် တင်ပါ", type=["mp4"])

if uploaded_video is not None:
    # ယာယီဗီဒီယိုသိမ်းရန်
    with open("temp_movie.mp4", "wb") as f:
        f.write(uploaded_video.read())
        
    st.info("ဗီဒီယိုဖိုင်ကို စစ်ဆေးနေပါသည်...")
    
    # OpenCV ဖြင့် Frame များ ဆွဲထုတ်ခြင်း
    cap = cv2.VideoCapture("temp_movie.mp4")
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # ပေါ့ပေါ့ပါးပါးဖြစ်အောင် frame ၅ ခုပဲ အချိုးကျ ခွဲထုတ်မယ်
    sample_indices = np.linspace(0, total_frames - 1, 5, dtype=int)
    frames_list = []
    
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
    
