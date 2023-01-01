import requests
import os
import smtplib
import datetime

# ---------------------------------------------- SETTING THE CONSTANTS ---------------------------------------------- #
# Stocks / User inputs ~
STOCKS = {
	# format --> "STOCK": "Company name",
	"NFLX": "Netflix Inc",
	"GOOGL": "Alphabet Inc",
	"AMZN": "Amazon.com, Inc.",
	"TSLA": "Tesla Inc",
}
ALERT_PERCENTAGE = 5  # day-to-day percentage increase/decrease in stock price to trigger email alert

# SMTP and Email details
SMTP_SERVER = "smtp.gmail.com"
MY_EMAIL = os.environ.get("MY_EMAIL")
MY_PASSWORD = os.environ.get("EMAIL_PASSWORD")
LIST_OF_RECIPIENTS = [os.environ.get("RECIPIENT_1"),
					os.environ.get("RECIPIENT_2")]  # modify list of recipients as required


# --------------------------------------------- STOCK/NEWS ALERT ENGINE ---------------------------------------------- #
def get_news_articles():
	"""Gets the first three news pieces for 'Company name'"""
	try:
		news_request = requests.get(NEWS_ENDPOINT, params=NEWS_PARAMETERS)
		news_request.raise_for_status()
	except requests.exceptions.HTTPError:
		error_message = "Error retrieving news articles."
		list_of_articles = [error_message]
	else:
		articles = news_request.json()["news"]
		list_of_articles = [(article["title"],
							article["url"],
							datetime.datetime.strptime(article["published"].split()[0], "%Y-%m-%d").strftime("%d-%B-%Y"))
							for article in articles[:3]]

		# print(f"Stock: {key}")  # test code, prints STOCK
		# print(f"Close prices: {list_of_close_prices[:5]}")  # test code, visualise price changes over last 5 days
		# print(f"% change: {percentage_change}% {change_direction}")  # test code, check to validate email response
		# print(f"Number of articles: {len(list_of_articles)}")  # test code, 1 - 3; if zero troubleshoot "Company name"
		# print(f"Articles: {list_of_articles}")  # test code, check that news API outputs articles for "Company name"

	return list_of_articles


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

	# Get the daily stock price data for the given STOCK
	stock_request = requests.get(ALPHAVANTAGE_ENDPOINT, params=STOCK_PARAMETERS)
	stock_request.raise_for_status()
	stock_data = stock_request.json()

	list_of_close_prices = []
	for date in stock_data["Time Series (Daily)"]:
		stock_close_price = float(stock_data["Time Series (Daily)"][date]["4. close"])
		list_of_close_prices.append(stock_close_price)

	# Check the latest closing stock price and compare to the closing price for the previous day
	latest_price = list_of_close_prices[0]
	previous_price = list_of_close_prices[1]
	send_alert = False

	if latest_price > previous_price * (1 + ALERT_PERCENTAGE/100):  # greater than (ALERT_PERCENTAGE)% price increase
		change_direction = "UP"
		percentage_change = round(((latest_price / previous_price) - 1) * 100, 1)
		news_articles = get_news_articles()
		send_alert = True
	elif latest_price < previous_price * (1 - ALERT_PERCENTAGE/100):  # greater than (ALERT_PERCENTAGE)% price decrease
		change_direction = "DOWN"
		percentage_change = round(((latest_price / previous_price) - 1) * -100, 1)
		news_articles = get_news_articles()
		send_alert = True

	# ----------------------------------------- SETTING UP EMAIL ALERTS ------------------------------------------ #
	# If there is a movement in closing STOCK price >= (ALERT_PERCENTAGE)%, send "Company name" articles by email
	if send_alert:
		with smtplib.SMTP(SMTP_SERVER) as connection:
			connection.starttls()
			connection.login(user=MY_EMAIL, password=MY_PASSWORD)
			for recipient in LIST_OF_RECIPIENTS:
				email_message = ""
				if len(news_articles) == 0:
					email_message += "No news articles have been found."
				elif news_articles[0] == "Error retrieving news articles.":
					email_message += news_articles[0]
				else:
					for num in range(0, len(news_articles)):
						email_message += f"Published: {news_articles[num][2]}\n" \
										f"Headline {num + 1}: {news_articles[num][0]}\n" \
										f"Link to article: {news_articles[num][1]}\n\n"
				connection.sendmail(from_addr=MY_EMAIL, to_addrs=recipient,
									msg=f"Subject:{key} {change_direction} {percentage_change}%\n\n"
										f"{(email_message.encode('utf-8', 'ignore')).decode('utf-8')}")
