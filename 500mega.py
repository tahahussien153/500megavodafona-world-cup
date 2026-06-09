from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
import base64
from PIL import Image
from io import BytesIO

app = Flask(__name__)
CORS(app)  # للسماح لصفحة الـ HTML بالاتصال بالسيرفر بدون مشاكل الـ CORS

@app.route('/worldcup', methods=['POST'])
def world_cup_promo():
    # استلام البيانات القادمة من صفحة الـ HTML
    number = request.form.get('phone')
    password = request.form.get('password')

    if not number or not password:
        return jsonify({"status": "error", "message": "برجاء إدخال رقم الهاتف وكلمة المرور ⚠️"}), 400

    # --- الخطوة 1: تجهيز الصورة وتحويلها لـ Base64 تلقائياً ---
    try:
        img_data = requests.get("https://i.postimg.cc/XNg5L1r6/IMG-20260609-182037.jpg", 
                                headers={"User-Agent": "Mozilla/5.0"}, timeout=15).content
        img = Image.open(BytesIO(img_data)).convert("RGB")
        img.thumbnail((800, 800))
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=70)
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        return jsonify({"status": "error", "message": f"فشل في معالجة الصورة بالسيرفر: {str(e)}"}), 500

    # --- الخطوة 2: تسجيل الدخول وجلب التوكن ---
    HEADERS = {
        'User-Agent': "okhttp/4.12.0", 'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip", 'silentLogin': "true", 'msisdn': number,
        'x-agent-operatingsystem': "15", 'clientId': "AnaVodafoneAndroid", 'Accept-Language': "ar",
        'x-agent-device': "OPPO CPH2565", 'x-agent-version': "2026.4.1",
        'x-agent-build': "1139", 'digitalId': "28LZHSGCX7QC4", 'device-id': "aba8140ecd392169"
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
        r_login = requests.post(login_url, data=login_payload, headers=HEADERS, timeout=20)
    except Exception:
        return jsonify({"status": "error", "message": "فشل الاتصال بسيرفر فودافون لتسجيل الدخول 🌐"}), 500

    if r_login.status_code != 200:
        return jsonify({"status": "error", "message": "رقم الهاتف أو كلمة السر خطأ ❌"}), 401

    token = r_login.json().get('access_token')

    # --- الخطوة 3: إعداد هيدرز الويب وجلب العرض ---
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
            timeout=20)
        
        promos = promos_res.json()
        if not isinstance(promos, list) or not promos:
            return jsonify({"status": "error", "message": "لا يوجد عرض متاح لكأس العالم لهذا الرقم حالياً 🤷‍♂️"}), 404
        promo_id = promos[0]["id"]
    except Exception:
        return jsonify({"status": "error", "message": "فشل استدعاء بيانات العرض من فودافون ⚠️"}), 500

    # --- الخطوة 4: إرسال الصورة وتفعيل الـ 500 ميجا ---
    journey_url = "https://web.vodafone.com.eg/services/dxl/pj/wc/journey/promoJourney"
    journey_payload = {
        "@type": "worldCupWow26", 
        "id": promo_id,
        "attachment": [{"attachmentType": "Image", "content": image_base64, "mimeType": "image/jpeg"}],
        "characteristics": [{"name": "pharaohName", "value": "tutankhamun"}]
    }

    try:
        r_journey = requests.post(journey_url,
            data=json.dumps(journey_payload),
            headers={**WEB_HEADERS, 'Origin': "https://web.vodafone.com.eg",
                     'Referer': "https://web.vodafone.com.eg/portal/bf/worldCup26/camera?isPostMessages=false"},
            timeout=60)
    except Exception:
        return jsonify({"status": "error", "message": "انتهت مهلة الطلب أثناء تفعيل العرض ⏱️"}), 504

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
    # قراءة بورت المنصة تلقائياً (مهم جداً لـ Railway لكي يعمل)
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
