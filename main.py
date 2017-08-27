from urllib.request import urlopen
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import os, re, json
import pandas
import matplotlib
from ggplot import *
import pydot
import itertools
import csv
import time
import urllib

#global dictionary of dictionaries
full_dict = dict()

#Input: None
#Output: None, but modifies a global dictionary of dictionaries
#Function: Accesses the California API website to get yearly reports for each county, filters by high school, and finds
#average API for each county of every year from a range and adds it into a global variable
def get_site_api():
    req = Request(
        'http://api.cde.ca.gov/reports/page2.asp?subject=API&level=County&submit1=submit',
        headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, 'lxml')
    options = soup.find_all('option')
    #get store counties in a list
    county_list = []
    for county in options:
        county_list.append(','.join(county.text.split()))

    # EXAMPLE URL for years >= 2010
    # http: // api.cde.ca.gov / Acnt2013 / 2012
    # Base_Co.aspx?cYear = & cSelect = 35, SAN, BENITO
    #

    # EXAMPLE URL for years < 2010
    # http: // api.cde.ca.gov / AcntRpt2008 / 2007
    # Base_Co.aspx?cYear = & cSelect = 01, ALAMEDA
    year = 2007
    hs_list = []
    hs_info = []
    hs_api = []

    while year <= 2012:
        print(year)
        for county in county_list:
            county_new = county.replace(',', ' ')[3:]
            print(county_new.title())

            #There is a different request if year is under 2010
            #Accesses the county's page
            # STEP A
            if year < 2010:
                req = Request(
                    'http://api.cde.ca.gov/AcntRpt'+ str(year+1) + '/' + str(year) + 'Base_Co.aspx?cYear=&cSelect=' + county,
                    headers={'User-Agent': 'Mozilla/5.0'}r
            else:
                req = Request(
                    'http://api.cde.ca.gov/Acnt' + str(year + 1) + '/' + str(year) + 'Base_Co.aspx?cYear=&cSelect=' + county,
                    headers={'User-Agent': 'Mozilla/5.0'})
            page = urlopen(req).read()
            soup = BeautifulSoup(page, 'lxml')
            under_high_school = False
            #Find only high school APIs
            #STEP B
            for row in soup.find_all('tr'):
                #check it is heading tag, then if under_high_school is true
                #if it's not a heading tag and under_high_school = true, then take the data otherwise skip
                #if it is heading then check if it is High Schools and set boolean accordingly
                if row.find('b'):
                    if row.b.text == 'High Schools':
                        under_high_school = True
                    else:
                        under_high_school = False
                else:
                    #strip all html formatting and only taking the high school name and values associated with it
                    if under_high_school:
                        for info in row.find_all('td', class_ = ["medium_left", "medium_center"]):
                            info_formatted = info.text.replace(u'\xa0', u' ').strip().splitlines()
                            hs_info += info_formatted
                        hs_list.append(hs_info)
                        hs_info = []
            #append the high school name and api to a list
            #STEP C
            for hs in hs_list:
                try:
                    hs_api.append((hs[0], int(hs[2])))
                except:
                    continue
            #STEP D
            avg_api = sum(n for _, n in hs_api)/len(hs_api)
            #add to global dictionary
            try:
                full_dict[county_new.title()][str(year)].append(avg_api)
            except:
                continue
            print('Avg API for '+ county_new + ' County: ' + str(avg_api))
        year += 1

#Input: filename to read from
#Output: dictionary of dictionaries
#Function: Reads in the given excel file and appends the row if state is in California, also calls another function,
# find_avg() from within
def read_log(filename):

    median_houses = []
    with open(filename, 'r', newline='') as input_file:
        log_data_reader = csv.DictReader(input_file, delimiter=',', quotechar='"', skipinitialspace=True)
        for row in log_data_reader:
            if row['State'] == 'CA':
                median_houses.append(row)

    #finds the average for each year of each county for a given range
    new_median_houses = find_avg(median_houses, 2007, 2012)
    return new_median_houses

#Input: list of dictionaries that contain median house values for each county, start and end year to loop through
#Output: dictionary of dictionaries
#Function: Finds the average median house value for each year and data into global list of dictionaries
def find_avg(median_houses, start_year, end_year):
    dict_avg_median = {}
    row_num = 0
    for row in median_houses:
        cols = list(row.keys())
        full_dict[row['RegionName']] = {}
        #go through each year within the given range
        for cur_year in range(start_year, end_year+1):
            sum = 0
            #go through each column for each row
            for col in cols:
                #matches column with format of "year"-"month" to get the sum median house value of that year
                keys_numbers = re.match(r"^" + str(cur_year) + r"-\d\d",col)
                if keys_numbers is not None:
                    try:
                        sum += int(median_houses[row_num][col])
                    except:
                        continue

            avg = round(sum/12,2)
            row[str(cur_year)] = avg
            #putting into full dictionary
            #STEP 2
            avg_list = list()
            avg_list.append(avg)
            full_dict[row['RegionName']][str(cur_year)] = avg_list

        row_num += 1
    return (full_dict)

#Input: name of the file to write to, list of dictionaries to read from
#Output: excel file and a list of dictionaries to be used for ggplot
#Function: Write out values in the form "county, year, Avg API, Median House Value" as well as create a new list of dictionaries
def write_log_entries(filename, list_of_rows_to_write):
    row_counter = 0
    lod = []
    with open(filename, 'w+', newline='') as f:
        row_writer = csv.DictWriter(f, delimiter='\t', quotechar='"', extrasaction='ignore', fieldnames= ['County', 'Year'
                                                                                                          ,'Avg API', 'Median House Value'])
        row_writer.writeheader()
        for county, years in list_of_rows_to_write.items():
            for year in years:
                temp_dict = {}
                if years[year][0] == 0:
                    continue
                else:
                    temp_dict['Avg API'] = years[year][1]

                temp_dict['County'] = county
                temp_dict['Year'] = int(year)
                temp_dict['Median House Value'] = years[year][0]

                lod.append(temp_dict)
                row_writer.writerow(temp_dict)
                row_counter += 1

    print("Wrote {} rows to {}".format(row_counter, filename))
    return(lod)

#Input: list of dictionaries
#Output: 4 different ggplot graphs
#Function: Converts a list of dictionaries into something that ggplot could be used to plot graphs
def plot_graph(lod):
    df = pandas.DataFrame(lod)

    #Change Year to string to work
    # g = ggplot(df, aes(x='Avg API', y='Median House Value', color = 'Year')) + \
    #     labs(x = "Avg API (Academic Performance Index)", y = "Median Home Value Per Sq Ft ($)") + geom_point()

    g2 = ggplot(df, aes(x='Avg API', y='Median House Value')) + geom_point() + facet_wrap('County') +\
    scale_x_continuous(breaks = (675, 705, 735)) + scale_y_continuous(breaks=(0, 250, 450, 650)) + \
         labs(x="Avg API (Academic Performance Index)", y="Median Home Value Per Sq Ft ($)")

    g3 = ggplot(df, aes(x='Year', y='Median House Value')) + geom_line() + facet_wrap('County') + \
        scale_y_continuous(breaks=(0,250, 450, 650)) + \
         labs(x="Year", y="Median Home Value Per Sq Ft ($)")

    g4 = ggplot(df, aes(x='Year', y='Avg API')) + geom_line() + facet_wrap('County') + \
        scale_y_continuous(breaks = (675, 705, 735)) + facet_wrap('County') + \
         labs(x="Year", y="Avg API (Academic Performance Index)")


    # print(g)
    print(g2)
    print(g3)
    print(g4)

def main():
    entries = read_log("county_median_value.csv")
    get_site_api()
    lod = write_log_entries('combined_data_output.txt', entries)
    plot_graph(lod)



if __name__ == '__main__':
    main()
