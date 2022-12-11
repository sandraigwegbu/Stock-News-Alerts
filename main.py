import requests
import os
import smtplib

# ---------------------------------------------- SETTING THE CONSTANTS ---------------------------------------------- #
# Stocks / User inputs ~
STOCKS = {
	# format --> "STOCK": "Company name",
	"GOEV": "Canoo Inc",
	"PATH": "UiPath Inc",
	"STNE": "StoneCo Ltd",
	"GDOT": "Green Dot Corporation",
	"AFRM": "Affirm Holdings Inc",
}
ALERT_PERCENTAGE = 5  # day-to-day percentage increase/decrease in stock price to trigger email alert

# --------------------------------------------- STOCK/NEWS ALERT ENGINE ---------------------------------------------- #
for key in STOCKS:
	# Alpha Vantage Stock API inputs
	ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")
	ALPHAVANTAGE_ENDPOINT = "https://www.alphavantage.co/query"

	STOCK_PARAMETERS = {
		"function": "TIME_SERIES_DAILY_ADJUSTED",
		"symbol": key,  # "STOCK"
		"apikey": ALPHAVANTAGE_API_KEY,
	}

	# News API inputs
	NEWS_API_KEY = os.environ.get("CURRENTS_API_KEY")
	NEWS_ENDPOINT = "https://api.currentsapi.services/v1/search"

	NEWS_PARAMETERS = {
		"keywords": STOCKS[key],  # "Company name"
		"apiKey": NEWS_API_KEY,
	}

	# SMTP and Email details
	SMTP_SERVER = "smtp.gmail.com"
	MY_EMAIL = os.environ.get("MY_EMAIL")
	MY_PASSWORD = os.environ.get("EMAIL_PASSWORD")
	LIST_OF_RECIPIENTS = [os.environ.get("RECIPIENT_1"),
						os.environ.get("RECIPIENT_2")]  # modify list of recipients as required

	# Get the daily stock price data for the given STOCK
	stock_request = requests.get(ALPHAVANTAGE_ENDPOINT, params=STOCK_PARAMETERS)
	stock_request.raise_for_status()
	stock_data = stock_request.json()

	list_of_close_prices = []
	for date in stock_data["Time Series (Daily)"]:
		stock_close_price = float(stock_data["Time Series (Daily)"][date]["4. close"])
		list_of_close_prices.append(stock_close_price)
	# print(list_of_close_prices)  # test code, to visualise historical price changes

	# Check the latest closing stock price and compare to the closing price for the previous day
	latest_price = list_of_close_prices[0]
	previous_price = list_of_close_prices[1]
	get_news = False

	if latest_price > previous_price * (1 + ALERT_PERCENTAGE/100):  # greater than (ALERT_PERCENTAGE)% price increase
		change_direction = "UP"
		percentage_change = round(((latest_price / previous_price) - 1) * 100, 1)
		get_news = True
	elif latest_price < previous_price * (1 - ALERT_PERCENTAGE/100):  # greater than (ALERT_PERCENTAGE)% price decrease
		change_direction = "DOWN"
		percentage_change = round(((latest_price / previous_price) - 1) * -100, 1)
		get_news = True

	# Get the first three news pieces for "Company name"
	news_request = requests.get(NEWS_ENDPOINT, params=NEWS_PARAMETERS)
	news_request.raise_for_status()
	news_articles = news_request.json()["news"]

	list_of_articles = [(article["title"], article["url"]) for article in news_articles[:3]]

	# ------------------------------------------- SETTING UP EMAIL ALERTS -------------------------------------------- #
	# If there is a movement in closing STOCK price >= (ALERT_PERCENTAGE)%, send "Company name" articles by email
	if get_news:
		with smtplib.SMTP(SMTP_SERVER) as connection:
			connection.starttls()
			connection.login(user=MY_EMAIL, password=MY_PASSWORD)
			for recipient in LIST_OF_RECIPIENTS:
				connection.sendmail(from_addr=MY_EMAIL, to_addrs=recipient,
									msg=f"Subject:{key} {change_direction} {percentage_change}%\n\n"
										f"Headline 1: {((list_of_articles[0][0]).encode('utf-8')).decode('utf-8')}\n"
										f"Link to article: {((list_of_articles[0][1]).encode('utf-8')).decode('utf-8')}\n\n"
										f"Headline 2: {((list_of_articles[1][0]).encode('utf-8')).decode('utf-8')}\n"
										f"Link to article: {((list_of_articles[1][1]).encode('utf-8')).decode('utf-8')}\n\n"
										f"Headline 3: {((list_of_articles[2][0]).encode('utf-8')).decode('utf-8')}\n"
										f"Link to article: {((list_of_articles[2][1]).encode('utf-8')).decode('utf-8')}"
									)
