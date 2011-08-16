(function() {
     /**
     * Backported version of getWeek from date.js SVN since the Alpha-1 version is broken.
     */
    Date.prototype.getWeek = function () {
        var a, b, c, d, e, f, g, n, s, w;
        
        var $y = this.getFullYear();
        var $m = this.getMonth() + 1;
        var $d = this.getDate();

        if ($m <= 2) {
            a = $y - 1;
            b = (a / 4 | 0) - (a / 100 | 0) + (a / 400 | 0);
            c = ((a - 1) / 4 | 0) - ((a - 1) / 100 | 0) + ((a - 1) / 400 | 0);
            s = b - c;
            e = 0;
            f = $d - 1 + (31 * ($m - 1));
        } else {
            a = $y;
            b = (a / 4 | 0) - (a / 100 | 0) + (a / 400 | 0);
            c = ((a - 1) / 4 | 0) - ((a - 1) / 100 | 0) + ((a - 1) / 400 | 0);
            s = b - c;
            e = s + 1;
            f = $d + ((153 * ($m - 3) + 2) / 5) + 58 + s;
        }
        
        g = (a + b) % 7;
        d = (f + g - e) % 7;
        n = (f + 3 - d) | 0;

        if (n < 0) {
            w = 53 - ((g - s) / 5 | 0);
        } else if (n > 364 + s) {
            w = 1;
        } else {
            w = (n / 7 | 0) + 1;
        }
        
        $y = $m = $d = null;
        
        return w;
    };

    var dayViewUrl = "#/day";
    var monthViewUrl = "#/month";
    var createActivityViewModel = function() {
	var viewModel = {
	    title: ko.observable(""),
	    date: ko.observable(""),
	    projects: ko.observableArray([]),
	    project_id: ko.observable(""),
	    duration: ko.observable(""),
	    comment: ko.observable(""),
	    add: function() {
		ct.addActivity(this.date(),
			       {
				   comment: this.comment(),
				   duration: this.duration(),
				   id: this.project_id(),
				   day: this.date()
			       });
		window.history.back();
	    },
	};

	viewModel.project_id.subscribe(function(newValue) {
	    // jQuery Mobile adds some elements that need to be updated
	    // Delay this so the other handlers can run first
	    window.setTimeout(function() {
		$('#edit div.ui-btn select[name=project]').selectmenu('refresh', true);
	    }, 1);
	});

	return viewModel;
    };

    var createDayViewModel = function() {
	var viewModel = {
	    home: dayViewUrl,
	    date: ko.observable(""),
	    title: ko.observable(""),
	    activities: ko.observableArray([]),
	    recentActivities: ko.observableArray([]),
	    reload: function() {
		ct.clear();
		ct.DayView.populate();
	    },
	    postProcess: function(elements) {
		elements.find("input, textarea").each(function() { $(this).textinput(); });
		elements.find("[data-role=button]").each(function() { $(this).button(); });
	    }
	};

	viewModel.next = ko.dependentObservable(function() {
	    return getNextDayUrl(this.date() || currentDayString());
	}, viewModel);
	viewModel.prev = ko.dependentObservable(function() {
	    return getPreviousDayUrl(this.date() || currentDayString());
	}, viewModel);

	return viewModel;
    }

    var createMonthViewModel = function() {
	var viewModel = {
	    home: monthViewUrl,
	    date: ko.observable(""),
	    title: ko.observable(""),
	    weeks: ko.observableArray([]),
	    reload: function() {
		ct.clear();
		ct.MonthView.populate();
	    },
	};

	viewModel.next = ko.dependentObservable(function() {
	    return getNextMonthUrl(this.date() || currentMonthString());
	}, viewModel);
	viewModel.prev = ko.dependentObservable(function() {
	    return getPreviousMonthUrl(this.date() || currentMonthString());
	}, viewModel);

	return viewModel;
    }

    var isValidDayString = function(s) {
	var date = getDateFromDayString(s);
	return date != null;
    };

    var isValidMonthString = function(s) {
	var date = getDateFromMonthString(s);
	return date != null;
    };

    var getDateFromDayString = function(s) {
	return Date.parseExact(s, "yyyy-MM-dd");
    };

    var getDateFromMonthString = function(s) {
	return Date.parseExact(s, "yyyy-MM");
    };

    var getDayStringFromDate = function(d) {
	return d.toString("yyyy-MM-dd");
    };

    var getMonthStringFromDate = function(d) {
	return d.toString("yyyy-MM");
    };

    var getTitleFromDayString = function(s) {
	var d = getDateFromDayString(s);
	return d.toString("dddd d. MMMM yyyy").toLowerCase();
    };

    var getTitleFromMonthString = function(s) {
	var d = getDateFromMonthString(s);
	return d.toString("MMMM yyyy").toLowerCase();
    };

    var nextDayFromDayString = function(s) {
	var d = getDateFromDayString(s).add(1).day();
	return getDayStringFromDate(d);
    };

    var previousDayFromDayString = function(s) {
	var d = getDateFromDayString(s).add(-1).day();
	return getDayStringFromDate(d);
    };

    var nextMonthFromMonthString = function(s) {
	var d = getDateFromMonthString(s).add(1).month();
	return getMonthStringFromDate(d);
    };

    var previousMonthFromMonthString = function(s) {
	var d = getDateFromMonthString(s).add(-1).month();
	return getMonthStringFromDate(d);
    };

    var getArgumentsFromUrl = function() {
	var url = $.address.value();
	var parts = url.split("/");
	return parts[2];
    };

    var getDayViewUrl = function(s) {
	return dayViewUrl + "/" + s;
    };

    var getMonthViewUrl = function(s) {
	return monthViewUrl + "/" + s;
    };

    var getNextDayUrl = function(s) {
	var dayString = nextDayFromDayString(s);
	return getDayViewUrl(dayString);
    };

    var getPreviousDayUrl = function(s) {
	var dayString = previousDayFromDayString(s);
	return getDayViewUrl(dayString);
    };

    var getNextMonthUrl = function(s) {
	var monthString = nextMonthFromMonthString(s);
	return getMonthViewUrl(monthString);
    };

    var getPreviousMonthUrl = function(s) {
	var monthString = previousMonthFromMonthString(s);
	return getMonthViewUrl(monthString);
    };

    var getActivitiesUrlFromDayString = function(s) { 
	var d = getDateFromDayString(s);
	return "/api/activities/" + d.toString("yyyy/MM");
    };

    var setActivityUrl = function(s) { 
	var d = getDateFromDayString(s);
	return "/api/activities/" + d.toString("yyyy/MM/dd");
    };

    var currentDayString = function() {
	return getDayStringFromDate(Date.today());
    };

    var currentMonthString = function() {
	return getMonthStringFromDate(Date.today());
    };

    var CurrentTime = function() {
	this._isFetchingActivities = false;
	this._projects = [];
	this._activitiesByDay = [];
	this.DayView.Model = createDayViewModel();
	this.MonthView.Model = createMonthViewModel();
	this.ActivityView.Model = createActivityViewModel();

	var self = this;
	$.getJSON('/api/projects', function(data) {
	    self._projects = data.projects;
	});
    };

    CurrentTime.prototype = {
	clear: function() {
	    this._activitiesByDay = [];
	},
	getProjects: function() {
	    return _.sortBy(_.values(this._projects),
			    function(p) {
				return p.name;
			    });
	},
	getProjectShortName: function(id) {
	    var p = this._projects[id];
	    return p.activity_name || p.subtask_name;
	},
	getProjectLongName: function(id) {
	    return this._projects[id].name;
	},
	extendActivitiesByDay: function(activitiesByDay) {
	    var self = this;
	    _.map(activitiesByDay, function(activities, day) {
		self._activitiesByDay[day] = activities;
	    });
	},
	addActivity: function(day, activity) {
	    var existing = this.getActivity(day, activity.id);
	    if (existing) {
		this.removeActivity(day, existing);
	    }


	    this._activitiesByDay[day].push(activity);
	},
	removeActivity: function(day, activity) {
	    this._activitiesByDay[day] = _.without(this._activitiesByDay[day], activity);
	},
	getActivity: function(day, id) {
	    return _.detect(this._activitiesByDay[day], function(a) {
		return (a.id == id);
	    });
	},
	getActivities: function(day) {
	    return this._activitiesByDay[day];
	},
	hasData: function(day) {
	    return this._activitiesByDay.hasOwnProperty(day);
	},
	fetchActivities: function(dayString, callback) {
	    var self = this;
	    if (!self._isFetchingActivities) {
		self._isFetchingActivities = true;
		self._promise = $.getJSON(getActivitiesUrlFromDayString(dayString), function(data) {
		    self.extendActivitiesByDay(data.activities);
		    self._isFetchingActivities = false;
		});
	    }
	    self._promise.done(callback);
	},
	postActivities: function(day, activities, callback) {
	    var url = setActivityUrl(day);
	    var data = { activities: activities };
	    var self = this;
	    $.ajax({
		type: "post",
		url: url,
		data: JSON.stringify(data),
		dataType: "json",
		contentType: "application/json; charset=utf-8",
		success: function(result) {
		    self.extendActivitiesByDay(result.activities);
		    callback(result);
		}
	    });
	}
    };

    CurrentTime.prototype.ActivityView = {
	populate: function(activity) {
	    this.Model.projects(ct.getProjects());
	    if (activity) {
		this.Model.title("Rediger aktivitet");
		this.Model.date(activity.day);
		this.Model.project_id(activity.id);
		this.Model.duration(activity.duration);
		this.Model.comment(activity.comment);
	    } else {
		this.Model.title("Legg til aktivitet");
		this.Model.date(currentDayString());
		this.Model.project_id(undefined);
		this.Model.duration("");
		this.Model.comment("");
	    }
	}
    }

    CurrentTime.prototype.DayView = {
	getSelectedDateString: function() {
	   var dayString = getArgumentsFromUrl();
	   if (!isValidDayString(dayString)) {
	       return currentDayString();
	   }
	   return dayString;
        },
	populate: function() {
	    var dayString = this.getSelectedDateString();
	    var title = getTitleFromDayString(dayString);
	    this.Model.date(dayString);
	    this.Model.title(title);
	    this.updateActivities(dayString);
	    this.updateRecentActivities(dayString);
	},
	updateActivities: function(dayString) {
	    var viewModel = this.Model;
	    if (viewModel.date() != dayString) {
		return;
	    }

	    viewModel.activities.removeAll();

	    if (ct.hasData(dayString)) {
		var data = ct.getActivities(dayString);
		viewModel.activities(data);
		$.mobile.pageLoading(true);
	    } else {
		var self = this;
		$.mobile.pageLoading();
		ct.fetchActivities(dayString, function() {
		    self.updateActivities(dayString);
		});
	    };
	},
	updateRecentActivities: function(dayString) {
	    var viewModel = this.Model;
	    if (viewModel.date() != dayString) {
		return;
	    }

	    viewModel.recentActivities.removeAll();

	    var day = previousDayFromDayString(dayString);
	    var activities = [];
	    var excluded_ids = _.pluck(viewModel.activities(), 'id');

            var earliestDateLimit = getDateFromDayString(dayString).add(-30).day();
            var dayDate = getDateFromDayString(day).day();
	    
	    while (viewModel.recentActivities().length < 5 && dayDate > earliestDateLimit) {
		if (!ct.hasData(day)) {
		    var self = this;
		    ct.fetchActivities(day, function() {
			self.updateRecentActivities(dayString);
		    });
		    return;
		}

		var data = ct.getActivities(day);
		var include = _.select(data, function(activity) {
		    return !_.contains(excluded_ids, activity.id);
		});

		activities = activities.concat(include);
		excluded_ids = excluded_ids.concat(_.pluck(include, 'id'));
		viewModel.recentActivities(activities);
		day = previousDayFromDayString(day);
                dayDate = getDateFromDayString(day).day();
	    }
	},
	addRecentActivity: function(recentActivity) {
	    var date = this.Model.date();
	    var activity = _.clone(recentActivity);
	    activity.day = date;
	    activity.comment = "";
	    ct.addActivity(date, activity);

	    this.updateActivities(date);
	    this.updateRecentActivities(date);
	},
	removeActivity: function(activity) {
	    var date = this.Model.date();
	    ct.removeActivity(date, activity);

	    this.updateActivities(date);
	    this.updateRecentActivities(date);
	},
	saveActivities: function() {
	    var date = this.date();
	    ct.postActivities(
		date, this.activities(), function(result) {
		    ct.DayView.updateActivities(date);
		    ct.DayView.updateRecentActivities(date);
		});
	},
	getEditUrl: function(id) {
	    var date = this.Model.date();
	    var activity = ct.getActivity(date, id);
	    var index = this.Model.activities.indexOf(activity);
	    return "/#/edit/" + index;
	},
    };

    CurrentTime.prototype.MonthView = {
	getSelectedDateString: function() {
	   var monthString = getArgumentsFromUrl();
	   if (!isValidMonthString(monthString)) {
	       return currentMonthString();
	   }
	   return monthString;
        },
	populate: function() {
	    var monthString = this.getSelectedDateString();
	    var title = getTitleFromMonthString(monthString);
	    this.Model.date(monthString);
	    this.Model.title(title);
	    this.updateWeeks(monthString);
	},
	updateWeeks: function(monthString) {
	    var viewModel = this.Model;
	    if (viewModel.date() != monthString) {
		return;
	    }

	    viewModel.weeks.removeAll();

	    var d = getDateFromMonthString(monthString);
	    var weeks = {};
	    for (var month = d.getMonth(); d.getMonth() == month; d.add(1).day()) {
		var dayString = getDayStringFromDate(d);
		if (!ct.hasData(dayString)) {
		    var self = this;
		    $.mobile.pageLoading();
		    ct.fetchActivities(dayString, function() {
			self.updateWeeks(monthString);
		    });
		    return;
		}
		$.mobile.pageLoading(true);

		var weekNumber = d.getWeek(0);
		var dayNumber = "day" + d.getDay();
		var week = weeks[weekNumber];
		if (typeof week === "undefined") {
		    week =  {};
		    week["weekNumber"] = weekNumber; 
		    week["hours"] = {};
		    for (var i = 0; i <= 6 ; i++) {
			week["day" + i] = "";
		    }

		    weeks[weekNumber] = week;
		}

		var activities = ct.getActivities(dayString);
		var sum = _.reduce(activities, function(memo, activity) { 
		    return memo + Number(activity.duration);
		}, 0);

		week["hours"][dayNumber] = sum;
	    }
            for (week in weeks) {
	        var sum = _.reduce(weeks[week]["hours"], function(memo, hours) {
	            return memo + hours;
	        }, 0);
                weeks[week]["totalHours"] = sum;
            }


	    viewModel.weeks(_.values(weeks));
	}
    };

    var ct = window.ct = new CurrentTime();

    $(document).bind("mobileinit", function() {
        $.mobile.ajaxEnabled = false;
        $.mobile.hashListeningEnabled = false;
    });

    $(document).bind("pagebeforecreate", function() {
	$.address.change(function(event) {
	    var parts = event.value.split("/");
	    var page = parts[1] || "day";
	    var args = _.rest(parts, 2);
	    var activePage = $.mobile.activePage[0].id;

	    if (page.match(/^add/)) {
		if (activePage != "edit") {
		    $.mobile.changePage("#edit",
					{ role: "dialog", transition: "pop", changeHash: false});
		}
		ct.ActivityView.populate();
	    }

	    if (page.match(/^edit/)) {
		if (activePage != "edit") {
		    $.mobile.changePage("#edit",
					{ role: "dialog", transition: "pop", changeHash: false});
		}
		var index = Number(args[0]);
		var activities = ct.getActivities(ct.DayView.Model.date());
		var activity = activities[index];
		ct.ActivityView.populate(activity);
	    }

	    if (page.match(/^day/)) {
		if (activePage != "day") {
		    $.mobile.changePage("#day",
					{ reverse: true, transition: "pop", changeHash: false});
		}
		ct.DayView.populate();
	    }

	    if (page.match(/^week/)) {
		if (activePage != "week") {
		    $.mobile.changePage("#week",
					{ reverse: true, transition: "pop", changeHash: false});
		}
	    }

	    if (page.match(/^month/)) {
		if (activePage != "month") {
		    $.mobile.changePage("#month",
					{ reverse: true, transition: "slide", changeHash: false});
		}
		ct.MonthView.populate();
	    }
	});

	ko.applyBindings(ct.DayView.Model, document.getElementById('day'));
	ko.applyBindings(ct.MonthView.Model, document.getElementById('month'));
	ko.applyBindings(ct.ActivityView.Model, document.getElementById('edit'));
    });

    // Fixes bug in jQuery Mobile. Without this, the ui-btn-active
    // isn't removed when we click the navigation links.
    $('a').live("vclick", function() {});
}());
