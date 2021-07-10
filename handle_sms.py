import csv
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from get_tickers import get_tickers
import random

app = Flask(__name__)

@app.route("/wallstreettexts", methods=["GET", "POST"])
def sms_reply():
    """Responds to incoming texts with a simple text message."""

    body = request.values.get("Body", None)

    body = body.strip()

    words = body.split(" ")

    tickers = set(get_tickers())

    message = (
        "Thanks for using WallStreetTexts! Please see available requests below: \n"
        "-> '<symbol> posts' (returns posts mentioning said symbol in past 24 hrs if available, ie 'AMC posts') \n"
        "-> '<number>' (returns top <number> mentioned symbols, ie '50') \n"
    )

    if len(words) == 2 and "POSTS" == words[1].upper():

        posts = {}

        with open('posts.csv', mode='r', encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                if len(row) != 0:
                    posts[row[0]] = row[1:]

        if words[0].upper() in posts.keys():

            message = (
                f"Random posts in the past 24hrs mentioning {words[0].upper()}: \n \n"
            )

            symbol_posts = posts[words[0].upper()]

            count = 0
            seen = set()

            while count < len(symbol_posts):

                number = random.randint(0, len(symbol_posts) - 1)

                while number in seen:
                    number += 1
                    number %= len(symbol_posts)

                post = symbol_posts[number].split("<-^->")

                seen.add(number)

                if (
                    len(message + (str(post[0]) + "\n" + str(post[1]) + "\n"))
                    > 1300
                ):
                    break

                message = message + (
                    str(post[0]) + "\n" + str(post[1]) + "\n"
                )
                count += 1

        else:
            message = "No data for ticker."
    else:
        try:
            amount = int(words[0])

            formatted = []

            occurrences = {}

            with open('occurrences.csv', mode='r') as csv_file:
                reader = csv.reader(csv_file)
                for index, row in enumerate(reader):
                    if len(row) != 0 and index != 0:
                        occurrences[row[0]] = row[1]

            # format the data
            for symbol in occurrences.keys():
                formatted.append([symbol, "(" + str(occurrences[symbol]) + " Posts)"])

            # text message body
            message = f"Top {amount} tickers in the last 24 hours: \n"

            # add the top symbols to the message body
            # twilio sms messages must be less than 1600 characters
            for symbol in formatted:
                if amount == 0 or len(message) > 1300:
                    break

                message = message + (" ".join(symbol) + "\n")
                amount -= 1


        except Exception as e:

            print(e)
            message = (
                "Thanks for using WallStreetTexts! Please see available requests below: \n"
                "-> '<symbol> posts' (returns posts mentioning said symbol in past 24 hrs if available, ie 'AMC posts') \n"
                "-> '<number>' (returns top <number> mentioned symbols, ie '50') \n"
            )

    resp = MessagingResponse()
    # Add a message
    resp.message(message)

    return str(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6969)