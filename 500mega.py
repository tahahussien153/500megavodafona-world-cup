from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
import base64
from PIL import Image
from io import BytesIO

app = Flask(__name__)
CORS(app)

# -------------------------------------------------------------------------
# ⚡ تسريع خارق: تجهيز الصورة وتحويلها لـ Base64 مرة واحدة فقط عند تشغيل السيرفر
# -------------------------------------------------------------------------
print("⏳ جاري تجهيز الصورة وضغطها في الذاكرة لتسريع الطلبات...")
try:
    img_data = requests.get("https://i.postimg.cc/XNg5L1r6/IMG-20260609-182037.jpg", 
                            headers={"User-Agent": "Mozilla/5.0"}, timeout=15).content
    img = Image.open(BytesIO(img_data)).convert("RGB")
    img.thumbnail((800, 800))
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=70)
    CACHED_IMAGE_BASE64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    print("✅ تم حفظ الصورة بنجاح! السيرفر جاهز الآن للعمل بأقصى سرعة.")
except Exception as e:
    # في حال فشل التحميل أونلاين، نضع قيمة احتياطية أو نغلق السيرفر للتنبيه
    print(f"❌ فشل تجهيز الصورة الافتتاحية: {str(e)}")
    CACHED_IMAGE_BASE64 = ""

@app.route('/worldcup', methods=['POST'])
def world_cup_promo():
    # التحقق من أن الصورة تم تجهيزها بنجاح
    if not CACHED_IMAGE_BASE64:
        return jsonify({"status": "error", "message": "السيرفر واجه مشكلة في تهيئة ملفات العرض، أعد تشغيله ⚠️"}), 500

    number = request.form.get('phone')
    password = request.form.get('password')

    if not number or not password:
        return jsonify({"status": "error", "message": "برجاء إدخال رقم الهاتف وكلمة المرور ⚠️"}), 400

    # --- الخطوة 1: تسجيل الدخول وجلب التوكن ---
    HEADERS = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 13; Xiaomi) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36", 
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip, deflate, br", 
        'silentLogin': "true", 
        'msisdn': number,
        'clientId': "AnaVodafoneAndroid", 
        'Accept-Language': "ar",
        'X-Requested-With': "com.emeint.android.myservices",
        'Connection': "keep-alive"
    }

    login_url = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
    login_payload = {
        'grant_type': "password", 
        'username': number, 
        'password': password,
        'client_secret': "dca0pbLUWXVhXR266Gw1iT5rqwvvJQoN", 
        'client_id': "AnaVF"
    }

    try:
        # تقليل الـ timeout لـ 8 ثوانٍ؛ لأن العملية أصبحت مباشرة ومباشرة جداً
        r_login = requests.post(login_url, data=login_payload, headers=HEADERS, timeout=8)
    except Exception:
        return jsonify({"status": "error", "message": "ضعف في الاتصال بسيرفر فودافون، يرجى المحاولة مجدداً 🌐"}), 500

    if r_login.status_code != 200:
        return jsonify({"status": "error", "message": "رقم الهاتف أو كلمة السر خطأ ❌"}), 401

    token = r_login.json().get('access_token')

    # --- الخطوة 2: إعداد هيدرز الويب وجلب العرض ---
    WEB_HEADERS = {
        'User-Agent': "vodafoneandroid", 'Accept': "application/json",
        'Accept-Encoding': "gzip, deflate, br, zstd", 'sec-ch-ua-platform': '"Android"',
        'Authorization': f"Bearer {token}", 'Accept-Language': "AR", 'msisdn': number,
        'sec-ch-ua': '"Chromium";v="148", "Android WebView";v="148", "Not/A)Brand";v="99"',
        'clientId': "WebsiteConsumer", 'sec-ch-ua-mobile': "?1", 'channel': "APP_PORTAL",
        'Content-Type': "application/json", 'X-Requested-With': "com.emeint.android.myservices",
        'Sec-Fetch-Site': "same-origin", 'Sec-Fetch-Mode': "cors", 'Sec-Fetch-Dest': "empty",
    }

    promo_url = "https://web.vodafone.com.eg/services/dxl/promo/promotion"
    
    try:
        promos_res = requests.get(promo_url,
            params={'@type': "Promo", '$.context.type': "worldCupWow26"},
            headers={**WEB_HEADERS, 'Referer': "https://web.vodafone.com.eg/portal/bf/worldCup26/home?isPostMessages=false"},
            timeout=8)
        
        promos = promos_res.json()
        if not isinstance(promos, list) or not promos:
            return jsonify({"status": "error", "message": "لا يوجد عرض متاح لكأس العالم لهذا الرقم حالياً 🤷‍♂️"}), 404
        promo_id = promos[0]["id"]
    except Exception:
        return jsonify({"status": "error", "message": "فشل استدعاء بيانات العرض، جرب مرة أخرى ⚠️"}), 500

    # --- الخطوة 3: إرسال الصورة الجاهزة من الذاكرة وتفعيل الـ 500 ميجا ---
    journey_url = "https://web.vodafone.com.eg/services/dxl/pj/wc/journey/promoJourney"
    journey_payload = {
        "@type": "worldCupWow26", 
        "id": promo_id,
        "attachment": [{"attachmentType": "Image", "content": CACHED_IMAGE_BASE64, "mimeType": "image/jpeg"}],
        "characteristics": [{"name": "pharaohName", "value": "tutankhamun"}]
    }

    try:
        r_journey = requests.post(journey_url,
            data=json.dumps(journey_payload),
            headers={**WEB_HEADERS, 'Origin': "https://web.vodafone.com.eg",
                     'Referer': "https://web.vodafone.com.eg/portal/bf/worldCup26/camera?isPostMessages=false"},
            timeout=10)
    except Exception:
        return jsonify({"status": "error", "message": "انتهت مهلة الطلب أثناء تفعيل العرض، أعد المحاولة ⏱️"}), 504

    if r_journey.status_code == 201:
        return jsonify({"status": "success", "message": "تم تفعيل عرض الـ 500 ميجا بنجاح! ✅"})
    else:
        try:
            err = r_journey.json()
            err_msg = err.get('reason') or err.get('message') or err.get('error') or f"Status {r_journey.status_code}"
        except Exception:
            err_msg = f"Status {r_journey.status_code}"
        return jsonify({"status": "error", "message": f"فشل تفعيل العرض: {err_msg}"}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
