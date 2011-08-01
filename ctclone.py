#!/usr/bin/env python

from ct.apis import RangeAPI
import ConfigParser
import datetime
import pickle
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-u", "--username", dest="username",
    help="The username")
parser.add_option("-p", "--password",
    dest="password",
    help="The password")




if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read(["config.ini.sample", "config.ini"])
    server = config.get("server", "ct_url")
    ct = RangeAPI(server)

    (options, args) = parser.parse_args()

    if not options.username or not options.password:
        parser.error("Both username and password is needed.")

    if not "bouvet\\" in options.username:
        options.username = "bouvet\\" + options.username

    logged_in = ct.login(options.username, options.password)

    if not logged_in:
        print "Could not log in"
        exit(-1)

    ct_list = []
    projects = ct.get_projects()
    #activities = ct.get_activities(datetime.date(2011, 1, 1), datetime.date(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day))
    activities = {}
    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month
    for month in range(1, current_month+1):
        print "month: ", month
        activities[(current_year, month)] = ct._ct.get_activities(current_year, month)

    print "Activities: ", activities

    ct_list.append(projects)
    ct_list.append(activities)

    pickle.dump(ct_list, open("pickled_ct.dat", "w+"))
