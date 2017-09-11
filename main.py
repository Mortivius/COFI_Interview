# Peter Stewart
# COFI Interview RESTful App
import requests
import sys
import json

endpoint = "https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json?"
api_key = "s-GMZ_xkw6CrkGYUWs1p" # not ideal to store this here, would never do this in a production app
securities = ["GOOGL", "MSFT", "COF"]
output_dict = {}
start_date = "20170101"
end_date = "20170630"

wants_busy_days = False
wants_biggest_loser = False
wants_max_daily_profit = False

bad_days = {}

if "--help" in sys.argv:
    print "Flags:"
    print "--max-daily-profit: Day in data set that would provide the highest amount of profit for each security if purchased at the day's low and sold at the day's high."
    print "--busy-day: Days with unusally high activity (> 10% more than average volume) for each security."
    print "--biggest-loser: Security with the most days where closing price was lower than the opening price."
    print "Output is written to output.txt."
if "--max-daily-profit" in sys.argv:
    wants_max_daily_profit = True
if "--busy-day" in sys.argv:
    wants_busy_days = True
if "--biggest-loser" in sys.argv:
    wants_biggest_loser = True

for security in securities:
    url = endpoint + "ticker=" + security + "&qopts.columns=ticker,date,open,close,volume&date.gte=" + start_date + "&date.lte=" + end_date + "&api_key=" + api_key

    myResponse = requests.get(url)
    if(myResponse.ok):
        jData = json.loads(myResponse.content)
        datatable = jData['datatable'] # dict
        data = datatable['data'] # list of lists

        # we know the API uses YYYYMMDD format
        year = start_date[:4]
        start_month = int(start_date[4:6])
        end_month = int(end_date[4:6])

        output_dict[security] = {}
        output_dict[security]["monthly_averages"] = []

        # calculate monthly averages for opens and closes
        for i in range(start_month, end_month+1):
            dict = {}

            if i < 10:
                month_string = year + "-0" + str(i)
            else:
                month_string = year + "-" + str(i)

            dict["month"] = month_string

            # we know d[1] is the full date string based on our request
            sum_opens = sum(d[2] for d in data if month_string in d[1])
            sum_closes = sum(d[3] for d in data if month_string in d[1])
            num_trading_days = len([d for d in data if month_string in d[1]])

            dict["average_open"] = sum_opens / num_trading_days
            dict["average_close"] = sum_closes / num_trading_days

            output_dict[security]["monthly_averages"].append(dict)

        # optional check 1 for busy days
        if wants_busy_days:
            avg_vol = sum(d[4] for d in data) / len(data)
            output_dict[security]["average_volume"] = avg_vol

            busy_days = [d[1:5:3] for d in data if d[4] >= 1.1 * avg_vol]
            output_dict[security]["busy_days"] = busy_days

        # create list of deltas which are used to find max daily profit and biggest loser
        deltas = [[d[1], d[3] - d[2]] for d in data]
        bad_days[security] = len([x[1] for x in deltas if x[1] < 0])

        # optional check 2 for max daily profit
        if wants_max_daily_profit:
            max_profit = max([x[1:] for x in deltas])
            vals = [x for x in deltas if x[1] == max_profit[0]]

            dict = {}
            dict["date"] = vals[0][0]
            dict["profit"] = vals[0][1]
            output_dict[security]["max_daily_profit"] = dict

    else: # response code is not ok (200), so print http error code with description
        myResponse.raise_for_status()

# optional check 3 for biggest loser
if wants_biggest_loser:
    most_losses = max(bad_days.values())
    for k, v in bad_days.iteritems():
        output_dict[k]["days_with_losses"] = bad_days[k]
        if v == most_losses:
            output_dict[k]["is_biggest_loser"] = True
        else:
            output_dict[k]["is_biggest_loser"] = False

f = open('output.txt', 'w')
f.write(json.dumps(output_dict, indent=4, sort_keys=True))
