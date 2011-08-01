import cPickle as pickle
from ct.apis import RangeAPI
import datetime
import ConfigParser

class RangeAPICache(RangeAPI):

    def __init__(self, server, cache_file):
        (self.projects, self.activities) = pickle.load(open(cache_file))

        super( RangeAPICache, self ).__init__(server)

    def get_activities(self, from_date, to_date):
        activities = []
        for year, month in self._get_months_in_range(from_date, to_date):
            for activity in self.activities[(year, month)]:
                if from_date <= activity.day and activity.day <= to_date and activity.has_activity():
                    activities.append(activity)

        return activities

    def get_projects(self):
        return self.projects

    def valid_session(self):
        return True



if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read(["config.ini.sample", "config.ini"])
    server = config.get("server", "ct_url")
    test = RangeAPICache(server, "pickled_ct.dat")

    start = datetime.date(2011,5,1)
    end = datetime.date(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)
    print "Activities: ", test.get_activities(start, end)
    print "Projects: ", test.get_projects()
