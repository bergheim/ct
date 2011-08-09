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

    var populateProjects = function(viewModel) {
	$.getJSON('/api/projects', function(data) {
	    viewModel.projects(data.projects);
	});
    };

    var populateActivities = function(viewModel) {
	$.getJSON('/api/activities/2011/8', function(data) {
	    viewModel.activitiesByDay(data.activities);
	});
    };
	
    $(document).bind("ready", function() {
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

	ko.applyBindings(viewModel);
	// $('.databound').each(function() { $(this).page() });
    });
}());
