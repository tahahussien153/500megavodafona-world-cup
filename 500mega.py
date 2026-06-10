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

@app.route('/worldcup', methods=['POST'])
def world_cup_promo():
    # استلام البيانات من الفرونت إند
    number = request.form.get('phone')
    password = request.form.get('password')

    if not number or not password:
        return jsonify({"status": "error", "message": "برجاء إدخال رقم الهاتف وكلمة المرور ⚠️"}), 400

    try:
        # تجهيز الصورة (نفس كودك بالحرف)
        img_data = requests.get("https://i.postimg.cc/XNg5L1r6/IMG-20260609-182037.jpg",
            headers={"User-Agent": "Mozilla/5.0"}).content

        img = Image.open(BytesIO(img_data)).convert("RGB")
        img.thumbnail((800, 800))
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=70)
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # الهيدرز الأولى (نفس كودك بالحرف)
        HEADERS = {
            'User-Agent': "okhttp/4.12.0", 'Accept': "application/json, text/plain, */*",
            'Accept-Encoding': "gzip", 'silentLogin': "true", 'msisdn': number,
            'x-agent-operatingsystem': "15", 'clientId': "AnaVodafoneAndroid", 'Accept-Language': "ar",
            'x-agent-device': "OPPO CPH2565", 'x-agent-version': "2026.4.1",
            'x-agent-build': "1139", 'digitalId': "28LZHSGCX7QC4", 'device-id': "aba8140ecd392169"
        }

        # طلب التوكن (نفس كودك بالحرف)
        r = requests.post("https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token",
            data={'grant_type': "password", 'username': number, 'password': password,
                  'client_secret': "dca0pbLUWXVhXR266Gw1iT5rqwvvJQoN", 'client_id': "AnaVF"}, headers=HEADERS)

        token = r.json().get('access_token') if r.status_code == 200 else None
        if not token: 
            return jsonify({"status": "error", "message": "رقم الهاتف أو كلمة السر خطأ ❌"}), 401

        # هيدرز الويب (نفس كودك بالحرف)
        WEB_HEADERS = {
            'User-Agent': "vodafoneandroid", 'Accept': "application/json",
            'Accept-Encoding': "gzip, deflate, br, zstd", 'sec-ch-ua-platform': '"Android"',
            'Authorization': f"Bearer {token}", 'Accept-Language': "AR", 'msisdn': number,
            'sec-ch-ua': '"Chromium";v="148", "Android WebView";v="148", "Not/A)Brand";v="99"',
            'clientId': "WebsiteConsumer", 'sec-ch-ua-mobile': "?1", 'channel': "APP_PORTAL",
            'Content-Type': "application/json", 'X-Requested-With': "com.emeint.android.myservices",
            'Sec-Fetch-Site': "same-origin", 'Sec-Fetch-Mode': "cors", 'Sec-Fetch-Dest': "empty",
        }

        # جلب العرض (نفس كودك بالحرف)
        promos = requests.get("https://web.vodafone.com.eg/services/dxl/promo/promotion",
            params={'@type': "Promo", '$.context.type': "worldCupWow26"},
            headers={**WEB_HEADERS, 'Referer': "https://web.vodafone.com.eg/portal/bf/worldCup26/home?isPostMessages=false"}).json()

        if not isinstance(promos, list) or not promos: 
            return jsonify({"status": "error", "message": "لا يوجد عروض متاحة لهذا الرقم حالياً 🤷‍♂️"}), 404
        
        promo_id = promos[0]["id"]

        # الطلب الأخير وتفعيل الهدية (نفس كودك بالحرف)
        r_final = requests.post("https://web.vodafone.com.eg/services/dxl/pj/wc/journey/promoJourney",
            data=json.dumps({"@type": "worldCupWow26", "id": promo_id,
                "attachment": [{"attachmentType": "Image", "content": image_base64, "mimeType": "image/jpeg"}],
                "characteristics": [{"name": "pharaohName", "value": "tutankhamun"}]}),
            headers={**WEB_HEADERS, 'Origin': "https://web.vodafone.com.eg",
                     'Referer': "https://web.vodafone.com.eg/portal/bf/worldCup26/camera?isPostMessages=false"},
            timeout=60)

        if r_final.status_code == 201:
            return jsonify({"status": "success", "message": "تم إرسال 500 ميجا بنجاح ✅"})
        else:
            err = r_final.json() if r_final.text else {}
            err_msg = err.get('reason') or err.get('message') or err.get('error') or f'Status {r_final.status_code}'
            return jsonify({"status": "error", "message": f"فشل تفعيل العرض: {err_msg}"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": f"حدث خطأ غير متوقع: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
