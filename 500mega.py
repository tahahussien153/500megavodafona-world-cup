from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, json, base64
from PIL import Image
from io import BytesIO

app = Flask(__name__)
CORS(app)

IMAGE_URL = "https://i.postimg.cc/XNg5L1r6/IMG-20260609-182037.jpg"

HEADERS = {
    'User-Agent': "okhttp/4.12.0",
    'Accept': "application/json, text/plain, */*",
    'Accept-Encoding': "gzip",
    'silentLogin': "true",
    'x-agent-operatingsystem': "15",
    'clientId': "AnaVodafoneAndroid",
    'Accept-Language': "ar",
    'x-agent-device': "OPPO CPH2565",
    'x-agent-version': "2026.4.1",
    'x-agent-build': "1139",
    'digitalId': "28LZHSGCX7QC4",
    'device-id': "aba8140ecd392169"
}

def get_image_base64():
    img_data = requests.get(IMAGE_URL, headers={"User-Agent": "Mozilla/5.0"}).content
    img = Image.open(BytesIO(img_data)).convert("RGB")
    img.thumbnail((800, 800))
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=70)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def login(number, password):
    r = requests.post(
        "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token",
        data={
            'grant_type': "password",
            'username': number,
            'password': password,
            'client_secret': "dca0pbLUWXVhXR266Gw1iT5rqwvvJQoN",
            'client_id': "AnaVF"
        },
        headers={**HEADERS, 'msisdn': number}
    )
    if r.status_code == 200:
        return r.json().get('access_token')
    return None

def get_promo(token, number):
    web_headers = {
        'User-Agent': "vodafoneandroid",
        'Accept': "application/json",
        'Authorization': f"Bearer {token}",
        'Accept-Language': "AR",
        'msisdn': number,
        'clientId': "WebsiteConsumer",
        'channel': "APP_PORTAL",
        'Content-Type': "application/json",
        'Referer': "https://web.vodafone.com.eg/portal/bf/worldCup26/home?isPostMessages=false"
    }
    r = requests.get(
        "https://web.vodafone.com.eg/services/dxl/promo/promotion",
        params={'@type': "Promo", '$.context.type': "worldCupWow26"},
        headers=web_headers
    )
    if r.status_code != 200:
        return None
    promos = r.json()
    if not isinstance(promos, list) or not promos:
        return None
    return promos[0]["id"]

def send_gift(token, number, promo_id, image_base64):
    web_headers = {
        'User-Agent': "vodafoneandroid",
        'Accept': "application/json",
        'Authorization': f"Bearer {token}",
        'Accept-Language': "AR",
        'msisdn': number,
        'clientId': "WebsiteConsumer",
        'channel': "APP_PORTAL",
        'Content-Type': "application/json",
        'Origin': "https://web.vodafone.com.eg",
        'Referer': "https://web.vodafone.com.eg/portal/bf/worldCup26/camera?isPostMessages=false"
    }
    payload = {
        "@type": "worldCupWow26",
        "id": promo_id,
        "attachment": [{"attachmentType": "Image", "content": image_base64, "mimeType": "image/jpeg"}],
        "characteristics": [{"name": "pharaohName", "value": "tutankhamun"}]
    }
    r = requests.post(
        "https://web.vodafone.com.eg/services/dxl/pj/wc/journey/promoJourney",
        data=json.dumps(payload),
        headers=web_headers,
        timeout=60
    )
    return r

@app.route("/send-gift", methods=["POST"])
def send_gift_route():
    data = request.get_json()
    number = data.get("number", "").strip()
    password = data.get("password", "").strip()

    if not number or not password:
        return jsonify({"success": False, "message": "الرقم أو كلمة السر ناقصة"}), 400

    token = login(number, password)
    if not token:
        return jsonify({"success": False, "message": "فشل تسجيل الدخول ❌ تأكد من الرقم وكلمة السر"}), 401

    promo_id = get_promo(token, number)
    if not promo_id:
        return jsonify({"success": False, "message": "مفيش عروض متاحة حالياً ❌"}), 404

    try:
        image_base64 = get_image_base64()
    except Exception as e:
        return jsonify({"success": False, "message": f"فشل تحميل الصورة: {str(e)}"}), 500

    r = send_gift(token, number, promo_id, image_base64)

    if r.status_code == 201:
        return jsonify({"success": True, "message": "تم إرسال 500 ميجا بنجاح ✅🎉"}), 201
    else:
        try:
            err = r.json()
        except Exception:
            err = {}
        msg = err.get('reason') or err.get('message') or err.get('error') or f"Status {r.status_code}"
        return jsonify({"success": False, "message": f"فشل الإرسال ❌ {msg}"}), 400

@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok", "message": "Vodafone Gift API is running 🚀"})

if __name__ == "__main__":
    app.run(debug=False)
