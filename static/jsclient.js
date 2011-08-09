(function() {
    var formatDate = function(d) {
	return d.toString("yyyy-MM-dd");
    };

    var currentDay = function() {
	return formatDate(Date.today());
    };

    var nextDayFromString = function(s) {
	var d = new Date(s).add(1).day();
	return formatDate(d);
    };

    var previousDayFromString = function(s) {
	var d = new Date(s).add(-1).day();
	return formatDate(d);
    };

    var populateFromCache = function(viewModel) {
	// Fetch cached values
	var storage = localStorage || [];
	var projects = localStorage['projects'];
	if (projects) {
	    var parsed = JSON.parse(projects);
	    viewModel.projects(parsed);
	}

	var activities = localStorage['activities'];
	if (activities) {
	    var parsed = JSON.parse(activities);
	    viewModel.activitiesByDay(parsed);
	}
    };

    var populate = function(viewModel) {
	populateFromCache(viewModel);
	populateActivities(viewModel);
	populateProjects(viewModel);
    };

    var populateProjects = function(viewModel) {
	$.getJSON('/api/projects', function(data) {
	    viewModel.projects(data.projects);
	    if (localStorage !== undefined) {
		localStorage['projects'] = JSON.stringify(data.projects);
	    }
	});
    };

    var populateActivities = function(viewModel) {
	$.getJSON('/api/activities/2011/8', function(data) {
	    viewModel.activitiesByDay(data.activities);

	    if (localStorage !== undefined) {
		localStorage['activitiesByDay'] = JSON.stringify(data.activities);
	    }

	});
    };
	
    $(document).bind("pagebeforecreate", function() {
	var viewModel = {
	    // Data
	    projects: ko.observable([]),
	    activitiesByDay: ko.observable({}),
	    selectedDay: ko.observable(currentDay()),

	    // Behaviours
	    gotoToday: function() {
		this.selectedDay(currentDay());
	    },

	    gotoNextDay: function () { 
		var day = this.selectedDay();
		this.selectedDay(nextDayFromString(day));
	    },

	    gotoPreviousDay: function () { 
		var day = this.selectedDay();
		this.selectedDay(previousDayFromString(day));
	    },

	    reloadData: function() {
		populateProjects(this);
		populateActivities(this);
	    },

	    getProjectName: function(projectId) {
		return this.projects()[projectId];
	    }
	};

	viewModel.currentActivities = ko.dependentObservable(function() {
	    return this.activitiesByDay()[this.selectedDay()] || [];
	}, viewModel);

	viewModel.recentActivities = ko.dependentObservable(function() {
	    var day = previousDayFromString(this.selectedDay());
	    return this.activitiesByDay()[day] || [];
	}, viewModel);

	viewModel.selectedDayString = ko.dependentObservable(function() {
	    var d = new Date(this.selectedDay());
	    return d.toString("dddd d. MMMM yyyy").toLowerCase();
	}, viewModel);

	viewModel.postProcess = function(elements) {
	    elements.find("input, textarea").each(function() { $(this).textinput(); });
	    elements.find("[data-role=button]").each(function() { $(this).button(); });
	};

	ko.applyBindings(viewModel);
	populate(viewModel);
    });
}());
