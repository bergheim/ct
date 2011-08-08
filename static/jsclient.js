var allActivities;
var activities, availableActivities, projects;

$(document).bind("ready", function() {
        $.getJSON('/api/projects', function(data) {
            projects = data.projects;
        });

        $.getJSON('/api/activities/2011/8', function(data) {
            allActivities = data.activities;
            activities = allActivities['2011-08-08']
            availableActivities = allActivities['2011-08-06']

            var viewModel = {
            }
            ko.applyBindings(viewModel);
            $('.databound').each(function() { $(this).page() });
        });
});
