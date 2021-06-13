# Data comes from Johns Hopkins University
# https://github.com/CSSEGISandData/COVID-19
# https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv
# Thanks to them for making this data set public.
# You can find data beyond cumulative cases there!


import csv
import matplotlib.pyplot as plt
import wget
import os
from countryinfo import CountryInfo

COUNTRY_PATH = 'archive/countries/'
START_DATE = '22-01-2020'
WINDOW = 7  # used for the moving average calc
URL_GL = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
URL_US = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv'
GL_CSV_NAME = "covid19_confirmed_global.csv"
US_CSV_NAME = "covid19_confirmed_US.csv"
LIMIT = -20000   # cut-off value for showing effects of post adjustments in the graph
SCALE = 1000000  # cases per SCALE people


def main():

    country_list = get_countries()  # takes input from the user re searched countries
    gl_datafile, us_datafile = download_data()  # downloads file from Jones Hopkins' Github
    filtered_data = filter_data(country_list, gl_datafile, us_datafile)  # selects the necessary data into a list of dictionaries
    plot_graph(filtered_data)
    remove_datafiles()


def get_countries():
    country_list = []

    while True:
        answer = input("Enter the country, you can finish by pressing enter: ")

        if answer == "":
            print("you asked for these countries: ", end='')
            for i in range(len(country_list)):
                if i == len(country_list) - 1:  # the last element does not need a coma
                    print(country_list[i])
                else:
                    print(country_list[i] + ", ", end='')

            return country_list

        else:
            country_list.append(answer)


def download_data():
    gl_datafile = wget.download(URL_GL, GL_CSV_NAME)
    us_datafile = wget.download(URL_US, US_CSV_NAME) #the USA data are in a separate file
    return gl_datafile, us_datafile


def filter_data(country_list, gl_datafile, us_datafile):  # this function puts together a dictionary for each country incl. daily cases, mov. average, covid days
    filtered_data = []

    for i in range(len(country_list)):
        country = country_list[i]

        if country == "United States" or country == "United States of America":
            # the us datafile has a different structure, therefore it needs a different helping function to load the data
            cases_list = load_values_aggregate_us(us_datafile)
            # print(cases_list)


        else:
            cases_list = load_values_aggregate_gl(country, gl_datafile)  # collects data from datafile

        # else:
            # cases_list = load_values(country, gl_datafile)  # collects data from datafile
            # print("cases list: ", cases_list)

        covid_days = count_covid_period(cases_list)
        daily_cases_pc = count_new_daily_cases_pc(country, cases_list)  # calculates the new daily cases per capita
        moving_avg_pc = calc_moving_avg_pc(daily_cases_pc) # calculates a moving average per capita and puts them into a list


        # puts these into a dictionary:
        country_data = {
            'name': country,
            'daily_new_cases_per_capita': daily_cases_pc,
            'moving_average_per_capita': moving_avg_pc,
            'nr of covid days': covid_days,
        }

        filtered_data.append(country_data)
    return filtered_data


def load_values_aggregate_gl(country, datafile):
    with open(datafile) as f:   # ennél biztosan van jobb megoldás, mint csak azért megnyitni a fájlt, h megnézzem az első sor hosszát
        reader = csv.reader(f)
        for line in reader:
            cases_list = [0] * (len(line)-4)  # creates a list of zeros as many as days in the datafile

    with open(datafile) as f:
        reader = csv.reader(f)
        for line in reader:
            if line[1] == country:
                for i in range(len(line)-4):  # the indexes 0-3 cover region, state, longitude & latitude, the daily case
                    # data are from index 4.
                    cases_list[i] = cases_list[i] + int(line[i+4])  # this adds the value of a region to the existing list
                #print("load values lines: ", line)
    return cases_list


def load_values_aggregate_us(us_datafile):
    with open(us_datafile) as f:
        reader = csv.reader(f)
        for line in reader:
            cases_list = [0] * (len(line)-11)  # ennél biztosan van jobb megoldás, mint csak azért megnyitni a fájlt, h megnézzem az első sor hosszát

    with open(us_datafile) as f:
        reader = csv.reader(f)
        next(f)
        for line in reader:
            for i in range(len(line)-11):  # in the us file, the indexes 0-10 cover region, state, longitude & latitude, the daily case
                # data are from index 1.
                cases_list[i] = cases_list[i] + int(line[i+11])  # this adds the value of a region to the existing list
    return cases_list


def count_covid_period(cases_list):  # counts non-zero elements
    covid_day = 0
    free_day = 0
    for daily_case in cases_list:
        if daily_case != 0:
            covid_day += 1
        else:
            free_day += 1
    return covid_day


def count_new_daily_cases_pc(country, cases_list):
    daily_cases_pc = []
    population = CountryInfo(country).population()
    # print("population is in average: " + country)
    # print(population)

    for i in range(len(cases_list)):
        if i == 0:  # the first day does not have a preceding data
            daily_cases_pc.append(cases_list[i]/population * SCALE)
        else:
            daily_nr = max((cases_list[i] - cases_list[i - 1])/population * SCALE, LIMIT/population * SCALE)  # to limit post adjustment effects
            daily_cases_pc.append(daily_nr)

    # print(daily_cases_pc)
    return daily_cases_pc


def calc_moving_avg_pc(daily_cases_pc):

    moving_avg = []

    for i in range(len(daily_cases_pc)):
        tmp_sum = 0
        counter = 0

        window_start = max(i - WINDOW + 1,
                           0)  # this is the first index which should be included in the window of the moving avg
        window_length = i - window_start + 1
        for j in range(window_start, i + 1):  # i+1 not included
            tmp_sum += daily_cases_pc[j]
            counter += 1

        mvg_avg = tmp_sum / counter
        # if counter != window_length:  # checks whether there might any error in calculation
            # print("error: i, counter, window_length", i, counter, window_length)

        moving_avg.append(mvg_avg)
    return moving_avg


def plot_graph(filtered_data):
    #plt.style.use('fivethirtyeight')  #for plot style
    for i in range(len(filtered_data)):  # moving average numbers should have an own label, daily new numbers need one label for all the countries.
        days = [[j] for j in range(len(filtered_data[i]['daily_new_cases_per_capita']))]
        # naming label for th graph, only the average needs a label
        label_avg = filtered_data[i]['name'] + " (average)"

        if i == len(filtered_data)-1:  # the label "daily new cases" will be shown only at end of the legend, as
            # all countries' daily cases are shown in the same lightgrey colour
            label_daily = 'daily new cases'
        else:
            label_daily = ''

        plt.plot(days, filtered_data[i]['moving_average_per_capita'], label=label_avg)
        plt.plot(days, filtered_data[i]['daily_new_cases_per_capita'], label=label_daily, color='lightgrey', linestyle='dotted')

    plt.legend()

    plt.title('New daily covid cases ' + str(WINDOW) + " days average per 1 million people")
    plt.grid(True)
    plt.xlabel('Days since ' + START_DATE)
    plt.ylabel('Cases')

    plt.savefig("infection_graph.png")
    plt.show()


def remove_datafiles():
    os.remove(GL_CSV_NAME)  # deletes datafiles
    os.remove(US_CSV_NAME)


if __name__ == '__main__':
    main()
