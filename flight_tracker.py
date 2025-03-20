print("Starting the flight tracker web app...")

from flask import Flask, render_template, request, redirect, url_for
import requests
import time
import threading

app = Flask(__name__)

# List to store flight details
flights = []

# Your SerpApi key (in quotes)
API_KEY = "60c9e87b14e1484a755bbbc58bfdcbce744d7ac91d2e91a39fa4c30b1bea2678"  # Replace with your key

# Function to check current flight price for a specific flight
def check_flight_price(flight):
    params = {
        "engine": "google_flights",
        "departure_id": flight["origin"],
        "arrival_id": flight["destination"],
        "outbound_date": flight["depart_date"],
        "return_date": flight["return_date"],
        "api_key": API_KEY
    }
    url = "https://serpapi.com/search"
    response = requests.get(url, params=params)
    data = response.json()
    try:
        for f in data["best_flights"]:
            if f["flights"][0]["airline"] == flight["airline"]:
                return float(f["price"])
        for f in data.get("other_flights", []):
            if f["flights"][0]["airline"] == flight["airline"]:
                return float(f["price"])
        print(f"No {flight['airline']} flights found for {flight['origin']} to {flight['destination']}.")
        return None
    except Exception as e:
        print(f"Error fetching price for {flight['origin']} to {flight['destination']}: {e}")
        return None

# Background thread to check prices daily
def track_prices():
    while True:
        for flight in flights:
            print(f"Checking price for {flight['origin']} to {flight['destination']} on {time.ctime()}...")
            current_price = check_flight_price(flight)
            if current_price:
                flight["current_price"] = current_price
                if current_price < flight["original_price"]:
                    flight["status"] = f"Price dropped! Save ${flight['original_price'] - current_price}!"
                else:
                    flight["status"] = "No price drop yet."
            else:
                flight["status"] = "Failed to get price."
        print("Pausing for 24 hours...")
        time.sleep(86400)  # Wait 24 hours

# Start tracking in a background thread
tracking_thread = threading.Thread(target=track_prices, daemon=True)
tracking_thread.start()

# Route for the landing page
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # Add new flight from form input
        flight = {
            "origin": request.form["origin"].upper(),
            "destination": request.form["destination"].upper(),
            "depart_date": request.form["depart_date"],
            "return_date": request.form["return_date"],
            "airline": request.form["airline"].capitalize(),
            "original_price": float(request.form["original_price"]),
            "current_price": None,  # Will be updated by tracker
            "status": "Tracking started..."
        }
        flights.append(flight)
        print(f"Added flight: {flight['origin']} to {flight['destination']} on {flight['airline']}")
        return redirect(url_for("home"))
    return render_template("index.html", flights=flights)

# Run the app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)  # Change to 5001 if 5000 is busy