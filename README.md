# WallStreetTexts
Want to see what stocks are trending on r/WallStreetBets? Give (226) 243-1518 a text.

![](WallStreetTexts.gif)

## Usage

There are currently two supported requests that you can text to (226) 243-1518:

1) Text '\<number>' (ie '25'), which returns top <number> mentioned symbols in the past 24 hours.
2) Text '\<symbol> posts' (ie 'AMC posts'), which returns random posts mentioning said symbol in past 24 hours, if available.

## How Things Work

This application has two main services:

1) Periodic scraping of r/WallStreetBets, which then determines how many times a symbol was mentioned in the title of a post.
2) A Flask service interfacing with the Twilio API to handle SMS messages and return the info to the user.

### r/WallStreetBets Scraping + Data Processing

Originally planned to utilize the Reddit API, I quickly realized that there is a limit of 1000 posts that can be returned by each request. 
This would require pagination of requests to get all the posts in the past 24 hours, or to monitor the number of new posts and to scrape the data every 1000 posts.
After doing some research, I came across the Pushshift API. It provides enhanced scraping functionality, mainly being that it returns all posts within a specified scrape period! So, using Pushshift over Reddit was the clear choice.

As for the data processing, ie counting of occurences for each symbol, we have to extract stock symbols out of each post's title. 
Since symbols follow a pattern, this is fairly straight forward. Any words over 5 characters can be disregarded (we use 5 characters as the cut off as the biggest a ticker can be is $XXXX). Also, any words that are not alpha (only consisting of letters) ie "B2B" or any words that start with "$" not followed by an alpha word ie "$200" can also be safely ignored.

After this basic filtering, we need to validate if the word is even a symbol or not. This is achieved by having a ready set of actively-traded symbols across the three major NA exchanges (NASDAQ, NYSE, AMEX) on hand, which is gathered from https://www.nasdaq.com/market-activity/stocks/screener .

With this information, we can achieve a constant lookup for each filtered word to determine if it is a stock symbol. 
One issue, is that there are some words such as "A", "FOR", "HOW" etc. that are also legitimate symbols which would get picked up by the scraper. 
This is why there is a blacklist, as it is highly likely that these stocks are not actually being talked about on r/WallStreetBets.

Once we are confident that a word is a symbol, we can safely count it as an occurence. One thing to note, is that this service ignores duplicate symbols in the same title, for example a title of "WISH WISH WISH! TO THE MOON!" would only cause the count of "WISH" to go up by one.

#### CSVs + Data Storage

The data service described above runs periodically every 5 minutes and stores the computed results to two CSV files. 
This means the Flask application can just read the values from the spreadsheets without having to do any intensive computations.

There are two CSV files:

1) occurences.csv -> Effectively an ordered dictionary (or a Counter object) stored as a spreadsheet, where the first column is the symbol and the second column is the number of occurences.

![image](https://user-images.githubusercontent.com/53923200/125656194-83d4084f-8c4d-4081-9007-1d9e4b0d198e.png)

2) posts.csv -> A dictionary where the first column is the symbol, and the rest being individual pair objects holding the (title, url) of each post mentioning said symbol.

![image](https://user-images.githubusercontent.com/53923200/125656346-48e3ff94-b9c0-45fb-a912-169ac7ef18fb.png)

### Handling of SMS Messages

By utilizing the Twilio API, once a user texts the number associated to the process, the Flask service (`handle_sms.py`) will handle the request. 
Depending on their message, the proper operation takes place, and the requested data is returned.
 
The script reads the requested info from the applicable CSV file, formats the message, and immediately sends said message to the user.


