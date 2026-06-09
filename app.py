import streamlit as st
import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io

# Page Configuration
st.set_page_config(page_title="TikTok Cover Generator", page_icon="🎬", layout="centered")

st.title("🎬 TikTok Video Cover Generator")
st.write("MP4 ဗီဒီယိုထဲကနေ လှပတဲ့ TikTok Cover (9:16) ပုံရိပ်တွေ ဖန်တီးပေးမယ့် App ဖြစ်ပါတယ်။")

# --- SIDEBAR: API & Settings ---
st.sidebar.header("⚙️ Settings")
# Groq API Key Space (ဖော်ပြပါ လုပ်ဆောင်ချက်အတွက် လောလောဆယ် API မလိုသော်လည်း တောင်းဆိုချက်အရ ထည့်သွင်းပေးထားပါသည်)
groq_api_key = st.sidebar.text_input("Groq API Key", type="password", placeholder="gsk_...")
if groq_api_key:
    st.sidebar.success("Groq API Key ထည့်သွင်းပြီးပါပြီ။")

# အလယ်မှာ ထည့်ချင်တဲ့ စာသား
cover_text = st.sidebar.text_input("Cover ပေါ်တွင် ထည့်လိုသည့် စာသား", value="Amazing Video!")
text_color = st.sidebar.color_picker("စာသား အရောင်", "#FFFFFF")

st.sidebar.markdown("---")
st.sidebar.info("Note: ဗီဒီယိုဖိုင် အရွယ်အစားကြီးလျှင် Processing လုပ်ရန် အနည်းငယ် ကြာနိုင်ပါသည်။")

# --- MAIN UI: File Uploader ---
uploaded_file = st.file_uploader("MP4 ဗီဒီယိုဖိုင် တင်ပါ", type=["mp4"])

if uploaded_file is not None:
    # ဗီဒီယိုဖိုင်ကို ယာယီသိမ်းဆည်းခြင်း
    with open("temp_video.mp4", "wb") as f:
        f.write(uploaded_file.read())
    
    st.success("ဗီဒီယို Upload တင်ခြင်း အောင်မြင်ပါသည်။")
    
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
    