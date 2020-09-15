**Newsroom**

This application is intended for educational purposes only.


Scrapes entire blogs, then summarizes, translates their articles to English and produces a list of keywords. 
The articles are categorized by topics. The user can create topics and assign sources to each for the Newsroom to
scrape.


Newsroom hides itself by changing its user agent on random intervals, then scrapes the blogs hidden behind the TOR
network which changes its IP address every 10 minutes. This is done only for educational purposes, please respect the request limits of every blog.


Uses: TOR, Gensim, BeautifulSoup, Newspaper, IBM's Watson API and the myMemory API.


***CONFIGURATION:***

    ***IBM Watson API**
        Look at the settings.py for the watson settings.
        Go to [IBM Watson translator](https://www.ibm.com/cloud/watson-language-translator) to create a free account
        and get an IAM secret key.

    ***Tor***
        $ sudo apt-get install tor
        Then run tor:
        $ tor
        When you run the scripts if you get this error:
            requests.exceptions.InvalidSchema: Missing dependencies for SOCKS support.
        Then install SOCKS: pip install 'requests[socks]'
    
    If you're having any trouble setting it up then Google is your best friend. I hope you find this project
    insightful.
