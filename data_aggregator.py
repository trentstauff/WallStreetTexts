from collections import Counter
from psaw import PushshiftAPI
from datetime import timedelta, datetime
import string
from get_tickers import get_tickers
import csv
import time
import operator

if __name__ == "__main__":
    while True:
        """
        Scrapes posts on r/WallStreetBets and counts the number
        of times a post talks about a symbol (in the past 24hrs)
        """

        # puts tickers in set for constant lookup
        tickers = set(get_tickers())

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
                    symbol_posts.append(f"{post.title}<-^->{post.full_link}")
                    posts[word[1:]] = symbol_posts

                    covered_symbols.add(word[1:])

                # case where word does not start with $
                elif word.isalpha() and 1 < len(word) < 6 and word not in covered_symbols:

                    # if the word is a known ticker, process it
                    if word in tickers:
                        symbols.append(word)
                        symbol_posts = posts.get(word, [])
                        symbol_posts.append(f"{post.title}<-^->{post.full_link}")
                        posts[word] = symbol_posts

                        covered_symbols.add(word)

        # count the occurrence of each symbol
        occurrences = Counter(symbols)

        sorted_d = dict(sorted(occurrences.items(), key=operator.itemgetter(1), reverse=True))

        with open('occurrences.csv', 'w+') as csvfile:
            fieldnames = ['symbol', 'posts']
            writer = csv.writer(csvfile)
            writer.writerow(fieldnames)
            for key in sorted_d.keys():
                writer.writerow([key, occurrences[key]])

        with open('posts.csv', 'w+', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            for key, values in posts.items():
                row = [key] + values
                writer.writerow(row)

        time.sleep(300)
