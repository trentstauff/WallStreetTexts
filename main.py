from collections import Counter
from psaw import PushshiftAPI
from datetime import timedelta, datetime
import string
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from get_tickers import get_tickers
import random

app = Flask(__name__)


def count_occurrences(tickers):
    """
    Scrapes posts on r/WallStreetBets and counts the number
    of times a post talks about a symbol (in the past 24hrs)

    Returns a Counter object tallying the occurrences of all seen symbols,
    and also returns a dictionary where keys are symbols and the values contain
    all WSB posts about said symbol.

    :param tickers:

    :return occurrences, posts:
    """

    # puts tickers in set for constant lookup
    tickers = set(tickers)

    # holds all occurrences of symbol names
    symbols = []

    api = PushshiftAPI()

    today = datetime.now()
    yesterday = int((today - timedelta(days=1)).timestamp())

    # gets all results in the past 24 hours
    results = list(api.search_submissions(after=yesterday, subreddit="wallstreetbets"))

    posts = {}

    # translator used to strip punctuation
    translator = str.maketrans("", "", string.punctuation)

    black_list = {
        "A",
        "I",
        "AND",
        "HODL",
        "LOSS",
        "MOON",
        "SEC",
        "CALLS",
        "ONLY",
        "NOW",
        "BUY",
        "SELL",
        "YOLO",
        "FOMO",
        "APE",
        "WSB",
        "THE",
        "TO",
        "WHAT",
        "DO",
        "FDA",
        "NEXT",
        "ALL",
        "NO",
        "OTC",
        "YOLO",
        "TOS",
        "CEO",
        "CFO",
        "CTO",
        "DD",
        "BTFD",
        "WSB",
        "OK",
        "RH",
        "KYS",
        "FD",
        "TYS",
        "US",
        "USA",
        "IT",
        "ATH",
        "RIP",
        "GDP",
        "OTM",
        "ATM",
        "ITM",
        "IMO",
        "LOL",
        "DOJ",
        "BE",
        "PR",
        "PC",
        "ICE",
        "TYS",
        "ISIS",
        "PRAY",
        "PT",
        "FBI",
        "SEC",
        "GOD",
        "NOT",
        "POS",
        "COD",
        "FOMO",
        "TL;DR",
        "EDIT",
        "STILL",
        "LGMA",
        "WTF",
        "RAW",
        "PM",
        "LMAO",
        "LMFAO",
        "ROFL",
        "EZ",
        "RED",
        "TICK",
        "IS",
        "DOW",
        "AM",
        "PM",
        "LPT",
        "GOAT",
        "FL",
        "CA",
        "IL",
        "PDFUA",
        "MACD",
        "HQ",
        "OP",
        "DJIA",
        "PS",
        "AH",
        "TL",
        "DR",
        "JAN",
        "FEB",
        "JUL",
        "AUG",
        "SEP",
        "SEPT",
        "OCT",
        "NOV",
        "DEC",
        "FDA",
        "IV",
        "ER",
        "IPO",
        "RISE",
        "IPA",
        "URL",
        "MILF",
        "BUT",
        "SSN",
        "FIFA",
        "USD",
        "CPU",
        "AT",
        "GG",
        "ELON",
        "LFG",
        "SUB",
        "IRA",
        "LUBE",
        "APES",
        "ME",
        "DIP",
        "MEME",
        "READ",
        "YOU",
        "ARE",
        "LOW",
        "GAIN",
        "BIG",
        "IN",
        "ON",
    }

    for post in results:

        # grab title
        title = post.title

        # split title into array of words
        array = title.split(" ")

        # if word is less than 6 characters long and either of the following are true, then we can consider it:
        # 1) word is uppercase and not in the blacklist
        # 2) word starts with $
        words = [
            word
            for word in array
            if (len(word) < 6 and (word.upper() not in black_list or word[0] == "$"))
        ]

        # if a title has multiple instances of the symbol, we only want to count it once
        covered_symbols = set()

        # iterate over filtered title words
        for word in words:

            # strip punctuation
            if word[0] == "$":
                word = "$" + word[1:].translate(translator)
            else:
                word = word.translate(translator)

            # if word was purely punctuation or is in blacklist, get next word
            if len(word) == 0 or word.upper() in black_list:
                continue

            # if word starts with $ and rest of the word is alpha, good chance its a symbol
            if (
                word[0] == "$"
                and word[1:].isalpha()
                and word[1:].upper() not in covered_symbols
            ):

                word = word.upper()

                # add word to symbols, track the post, and mark the word as seen for this title
                symbols.append(word[1:])

                symbol_posts = posts.get(word[1:], [])
                symbol_posts.append(post)
                posts[word[1:]] = symbol_posts

                covered_symbols.add(word[1:])

            # case where word does not start with $
            elif word.isalpha() and 1 < len(word) < 6 and word not in covered_symbols:

                # if the word is a known ticker, process it
                if word in tickers:
                    symbols.append(word)
                    symbol_posts = posts.get(word, [])
                    symbol_posts.append(post)
                    posts[word] = symbol_posts

                    covered_symbols.add(word)

    # count the occurrence of each symbol
    occurrences = Counter(symbols)

    return occurrences, posts


def send_message(message):
    """
    Sends a return text to the underlying number

    :param message:

    :return response:
    """
    # Start our TwiML response
    resp = MessagingResponse()
    # Add a message
    resp.message(message)

    return str(resp)


@app.route("/wallstreettexts", methods=["GET"])
def sms_reply():
    """Responds to incoming texts with a simple text message."""

    body = request.values.get("Body", None)

    words = body.split(" ")

    tickers = set(get_tickers())

    occurrences, posts = count_occurrences(tickers)

    message = (
        "Bad message. Examples of proper messages include: \n"
        "-> 'AMC posts' (returns all AMC posts in past 24 hrs if applicable) \n"
        "-> '50' (returns top 50 mentioned symbols) \n"
    )

    if len(words) == 2 and "POSTS" == words[1].upper():

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

                post = symbol_posts[number]

                seen.add(number)

                if (
                    len(message + (str(post.title) + "\n" + str(post.full_link) + "\n"))
                    > 1300
                ):
                    break

                message = message + (
                    str(post.title) + "\n" + str(post.full_link) + "\n"
                )
                count += 1

            return send_message(message)

        else:
            message = "No data for ticker."
            return send_message(message)
    else:
        try:
            amount = int(words[0])

            formatted = []

            # format the data
            for symbol in occurrences.most_common():
                formatted.append([symbol[0], "(" + str(symbol[1]) + " Posts)"])

            # text message body
            message = f"Top {amount} tickers in the last 24 hours: \n"

            # add the top symbols to the message body
            # twilio sms messages must be less than 1600 characters
            for symbol in formatted:
                if amount == 0 or len(message) > 1300:
                    break

                message = message + (" ".join(symbol) + "\n")
                amount -= 1

            return send_message(message)

        except:

            message = (
                "Thanks for using WallStreetTexts! Please see available requests below: \n"
                "-> 'SYMBOL posts' (returns posts mentioning said symbol in past 24 hrs if applicable, ie 'AMC posts') \n"
                "-> 'NUMBER' (returns top NUMBER mentioned symbols, ie '50') \n"
            )

            return send_message(message)

    return send_message(message)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6969)
