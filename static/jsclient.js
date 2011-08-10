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
	    this.setActivities(viewModel, date);
	    this.setRecentActivities(viewModel, date);
	},
	getProjectName: function(id) {
	    return this._projects[id];
	},
	setActivities: function(viewModel, day) {
	    var callback = function(data) {
		viewModel.activities(data);
	    };
	    this.getActivities(day, callback);
	},
	setRecentActivities: function(viewModel, currentDate) {
	    var callback = function(data) {
		viewModel.recentActivities(data);
	    };
	    var day = previousDayFromString(currentDate);
	    this.getActivities(day, callback);
	},
	getActivities: function(day, callback) {
	    var self = this;
	    if (self._activitiesByDay.hasOwnProperty(day)) {
		callback(self._activitiesByDay[day]);
	    } else {
		if (self._promise && !(self._promise.isResolved() || self._promise.isRejected())) {
		    self._promise.complete(function() {
			self.getActivities(day, callback);
		    });
		} else {
		    self._promise = $.getJSON(getActivitiesUrl(day), function(data) {
			$.extend(self._activitiesByDay, data.activities);
			callback(self._activitiesByDay[day]);
		    });
		}
	    }
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
