(function() {
    var dayViewUrl = "#/day";
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
	    return getNextDayUrl(this.date());
	}, viewModel);
	viewModel.prev = ko.dependentObservable(function() {
	    return getPreviousDayUrl(this.date());
	}, viewModel);
	return viewModel;
    }

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

    var setActivityUrl = function(s) { 
	var d = getDateFromString(s);
	return "/api/activities/" + d.toString("yyyy/MM/dd");
    };

    var currentDate = function() {
	return getStringFromDate(Date.today());
    };

    var CurrentTime = function() {
	this._isFetchingActivities = false;
	this._projects = [];
	this._activitiesByDay = [];
	this.DayView.Model = createDayViewModel();

	var self = this;
	$.getJSON('/api/projects', function(data) {
	    self._projects = data.projects;
	});
    };

    CurrentTime.prototype = {
	clear: function() {
	    this._activitiesByDay = [];
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
	getActivities: function(day) {
	    return _.map(this._activitiesByDay[day], function(activity) {
		return _.clone(activity);
	    });
	},
	hasData: function(day) {
	    return this._activitiesByDay.hasOwnProperty(day);
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

    CurrentTime.prototype.DayView = {
	populate: function() {
	    var date = getSelectedDate();
	    var title = getTitleFromString(date);
	    this.Model.date(date);
	    this.Model.title(title);
	    this.updateActivities(date);
	    this.updateRecentActivities(date);
	},
	updateActivities: function(currentDate) {
	    var viewModel = this.Model;
	    if (viewModel.date() != currentDate) {
		return;
	    }

	    viewModel.activities.removeAll();

	    if (ct.hasData(currentDate)) {
		var data = ct.getActivities(currentDate);
		viewModel.activities(data);
		$.mobile.pageLoading(true);
	    } else {
		var self = this;
		$.mobile.pageLoading();
		ct.fetchActivities(currentDate, function() {
		    self.updateActivities(currentDate);
		});
	    };
	},
	updateRecentActivities: function(currentDate) {
	    var viewModel = this.Model;
	    if (viewModel.date() != currentDate) {
		return;
	    }

	    viewModel.recentActivities.removeAll();

	    var day = previousDayFromString(currentDate);
	    var activities = [];
	    var excluded_ids = _.pluck(viewModel.activities(), 'id');

      var earliestDateLimit = getDateFromString(currentDate).add(-30).day();
      var dayDate = getDateFromString(day).day();
	    
	    while (viewModel.recentActivities().length < 5 && dayDate > earliestDateLimit) {
		if (!ct.hasData(day)) {
		    var self = this;
		    ct.fetchActivities(day, function() {
			self.updateRecentActivities(currentDate);
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
		day = previousDayFromString(day);
      dayDate = getDateFromString(day).day();
	    }
	},
	addRecentActivity: function(recentActivity) {
	    var activity = _.clone(recentActivity);
	    activity.day = this.Model.date();
	    activity.comment = "";
	    this.addActivity(activity);
	},
	addActivity: function(activity) {
	    var current = _.detect(this.Model.activities(), function(a) {
		return (a.id == activity.id);
	    });

	    if (current) {
		this.Model.activities.remove(current);
	    }

	    var myActivity = myActivity || _.clone(activity);
	    myActivity.day = this.Model.date();
	    this.Model.activities.push(myActivity);
	    this.updateRecentActivities(myActivity.day);
	},
	removeActivity: function(activity) {
	    var date = this.Model.date();
	    this.Model.activities.remove(activity);
	    this.updateRecentActivities(date);
	},
	saveActivities: function() {
	    var date = this.date();
	    ct.postActivities(
		date, this.activities(), function(result) {
		    ct.DayView.updateActivities(date);
		    ct.DayView.updateRecentActivities(date);
		});
	}
    };

    
    $(document).bind("pagebeforecreate", function() {
	var ct = window.ct = new CurrentTime();

	$.address.change(function(event) {
	    ct.DayView.populate();
	});

	ko.applyBindings(ct.DayView.Model);
    });

    $(document).bind("mobileinit", function() {
	$.mobile.ajaxEnabled = false;
	$.mobile.hashListeningEnabled = false;
    });

    // Fixes bug in jQuery Mobile. Without this, the ui-btn-active
    // isn't removed when we click the navigation links.
    $('a').live("vclick", function() {});
}());
