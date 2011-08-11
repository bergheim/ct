(function() {
    var dayViewUrl = "#/day";

    var getDateFromString = function(s) {
	return Date.parseExact(s, "yyyy-MM-dd") || Date.today();
    };

    var getTitleFromString = function(s) {
	var d = getDateFromString(s);
	return d.toString("dddd d. MMMM yyyy").toLowerCase();
    };

    var nextDayFromString = function(s) {
	var d = getDateFromString(s).add(1).day();
	return getStringFromDate(d);
    };

    var previousDayFromString = function(s) {
	var d = getDateFromString(s).add(-1).day();
	return getStringFromDate(d);
    };

    var getStringFromDate = function(d) {
	var date = d || Date.today();
	return d.toString("yyyy-MM-dd");
    };

    var getSelectedDate = function() {
	var url = $.address.value();
	var parts = url.split("/");
	return parts[2] || currentDate();
    };

    var getDayViewUrl = function(s) {
	return dayViewUrl + "/" + s;
    };

    var getNextDayUrl = function(s) {
	var day = nextDayFromString(s);
	return getDayViewUrl(day);
    };

    var getPreviousDayUrl = function(s) {
	var day = previousDayFromString(s);
	return getDayViewUrl(day);
    };

    var getActivitiesUrl = function(s) { 
	var d = getDateFromString(s);
	return "/api/activities/" + d.toString("yyyy/MM");
    };

    var currentDate = function() {
	return getStringFromDate(Date.today());
    };

    var CurrentTime = function() {
	this._isFetchingActivities = false;
	this._projects = [];
	this._activitiesByDay = [];

	var self = this;
	$.getJSON('/api/projects', function(data) {
	    self._projects = data.projects;
	});
    };

    CurrentTime.prototype = {
	clear: function() {
	    this._activitiesByDay = [];
	},
	populateDayView: function(viewModel) {
	    var date = getSelectedDate();
	    viewModel.date(date);
	    viewModel.title(getTitleFromString(date));
	    this.updateActivities(viewModel, date);
	    this.updateRecentActivities(viewModel, date);
	},
	getProjectName: function(id) {
	    return this._projects[id];
	},
	extendActivitiesByDay: function(activitiesByDay) {
	    var self = this;
	    _.map(activitiesByDay, function(activities, day) {
		var withDuration = _.select(activities, function(activity) {
		    return activity.duration > 0;
		});

		self._activitiesByDay[day] = withDuration;
	    });
	},
	getActivities: function(day) {
	    return this._activitiesByDay[day];
	},
	hasData: function(day) {
	    return this._activitiesByDay.hasOwnProperty(day);
	},
	updateActivities: function(viewModel, day) {
	    if (this.hasData(day)) {
		if (viewModel.date() != day) {
		    return;
		}

		var data = this.getActivities(day);
		viewModel.activities(data);
		$.mobile.pageLoading(true);
	    } else {
		var self = this;
		$.mobile.pageLoading();
		self.fetchActivities(day, function() {
		    self.updateActivities(viewModel, day);
		});
	    };
	},
	updateRecentActivities: function(viewModel, currentDate) {
	    var day = previousDayFromString(currentDate);
	    var activities = [];
	    var excluded_ids = _.pluck(viewModel.activities(), 'id');
	    
	    // Quickly remove activities that exist for the selected day
	    var recent = viewModel.recentActivities();
	    _.each(recent, function(activity) {
		if (_.contains(excluded_ids, activity.id)) {
		    viewModel.recentActivities.remove(activity);
		}
	    });

	    while (true) {
		if (this.hasData(day)) {
		    var data = this.getActivities(day);
		    var include = _.select(data, function(activity) {
			return !_.contains(excluded_ids, activity.id);
		    });

		    activities = activities.concat(include);
		    excluded_ids = excluded_ids.concat(_.pluck(include, 'id'));

		    if (activities.length >= 5) {
			viewModel.recentActivities(activities);
			return;
		    }
		} else {
		    var self = this;
		    self.fetchActivities(day, function() {
			self.updateRecentActivities(viewModel, currentDate);
		    });
		    return;
		}
		day = previousDayFromString(day);
	    }
	},
	fetchActivities: function(day, callback) {
	    var self = this;
	    if (!self._isFetchingActivities) {
		self._isFetchingActivities = true;
		self._promise = $.getJSON(getActivitiesUrl(day), function(data) {
		    self.extendActivitiesByDay(data.activities);
		    self._isFetchingActivities = false;
		});
	    }
	    self._promise.always(callback);
	}
    };
    
    $(document).bind("pagebeforecreate", function() {
	var ct = window.ct = new CurrentTime();
	var dayViewModel = {
	    home: dayViewUrl,
	    date: ko.observable(""),
	    title: ko.observable(""),
	    activities: ko.observableArray([]),
	    recentActivities: ko.observableArray([]),
	    addRecentActivity: function(recentActivity) {
		var activity = _.clone(recentActivity);
		activity.day = this.date;
		activity.comment = "";
		this.activities.push(activity);
		this.recentActivities.remove(recentActivity);
	    },
	    removeActivity: function(activity) {
		this.activities.remove(activity);
	    },
	    reload: function() {
		ct.clear();
		ct.populateDayView(this);
	    },
	    postProcess: function(elements) {
		elements.find("input, textarea").each(function() { $(this).textinput(); });
		elements.find("[data-role=button]").each(function() { $(this).button(); });
	    }
	};
	dayViewModel.next = ko.dependentObservable(function() {
	    return getNextDayUrl(this.date());
	}, dayViewModel);
	dayViewModel.prev = ko.dependentObservable(function() {
	    return getPreviousDayUrl(this.date());
	}, dayViewModel);

        $.address.change(function(event) {
	    ct.populateDayView(dayViewModel);
	});

	ko.applyBindings(dayViewModel);
    });

    $(document).bind("mobileinit", function() {
	$.mobile.ajaxEnabled = false;
	$.mobile.hashListeningEnabled = false;
    });

    // Fixes bug in jQuery Mobile. Without this, the ui-btn-active
    // isn't removed when we click the navigation links.
    $('a').live("vclick", function() {});
}());
