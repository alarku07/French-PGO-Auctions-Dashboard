# Specify
I would like you to build a simple website to visualize the auction results from French Power Guarantees of Origin website
https://www.eex.com/en/markets/energy-certificates/french-auctions-power
The goal is to provide the user interested in following the auctions to get statistics and upcoming auctions to see trends and plan on joining an auction. Keep in mind that this website is intended for people working in energy industry
and with Guarantees of origin. Get context for this from Wikipedia https://en.wikipedia.org/wiki/Guarantee_of_origin.
Download and keep local database of auctions calendar and results. The auctions website whows last auction results on web page and previous years can be downloaded as zip files containing Excel files by month.
Simple dashboard must show the auctions that have already happened and upcoming auctions. The dashboard must also show an inteactive graphs visualizing the data like prices over the years per region, how much the volumes have changed and basic general total statistics
A periodic script should also check if the calendar on the auctions site has been updated and download new data and results to the db. The dashboard must show the date when local DB was synced from auctions site. The auctions happen once a month.
The website is read-only and doesn't need any login.
Use the same color and text scheme as on the web page.

# ToDo
- Flask requirement
- explicit utf-8 encoding
- tests to correct directories

# Choices
- Spec Kit https://github.com/github/spec-kit
  - Light-weight
  - Python

# Future
* Push notifications or email alerts when new auctions are published.
* User-facing data export (e.g., CSV download from the dashboard).
* Multi-language support beyond English.
