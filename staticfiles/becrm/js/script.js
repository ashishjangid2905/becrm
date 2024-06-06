$(document).ready(function () {
  // alert hide automatic after 2sec
  setTimeout(function () {
    $("#myAlert").hide();
  }, 2000);

  // to show and hide password
  $("#show_password").change(function () {
    var passwordField = $(
      "#createPass, #confirmPass, #confirm_password, #new_password"
    );
    var passwordFieldType = passwordField.attr("type");
    if (passwordFieldType === "password") {
      passwordField.attr("type", "text");
    } else {
      passwordField.attr("type", "password");
    }
  });

  // Multiple port selection

  $(function () {
    $("#multiPort").multipleSelect({
      selectAll: false,
      showClear: true,
      filter: true,
    });
  });

  // default Month and Year selection

  var date = new Date();
  var default_year = date.getFullYear();
  var default_month = date.getMonth() + 1 - 2;

  if (default_month == 0) {
    $("#month").val(12);
    $("#year").val(default_year - 1);
  } else if (default_month < 0) {
    $("#month").val(11);
    $("#year").val(default_year - 1);
  } else {
    $("#month").val(default_month);
    $("#year").val(default_year);
  }

  // Change Month choices once change the year

  $("#year").change(function () {
    var selectedyear = $(this).val();
    var current_year = date.getFullYear();
    var current_month = date.getMonth() + 1;

    var month = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ];

    $("#month").empty();

    for (let i = 1; i <= 12; i++) {
      if (selectedyear == current_year && i > current_month - 1) {
        break;
      }

      $("#month").append(
        $("<option>", {
          value: i,
          text: month[i - 1],
        })
      );
    }
  });

  // Fetch the sample data

  $.ajax({
    url: "/sample-chart/",
    type: "GET",
    dataType: "json",
    success: function (data) {
      var month_labels = data.month_labels;
      var sample_counts = data.sample_counts;

      // var rejected_sample = data.rejected_sample;
      // var received_sample = data.received_sample;
      // var pending_sample = data.pending_sample;

      var per_day = Object.keys(data.per_day_count);
      var per_day_count = Object.values(data.per_day_count);

      var status = Object.keys(data.doughnut_data);
      var status_counts = Object.values(data.doughnut_data);

      var line = $("#sample_per_day_chart");
      var bar = $("#sample_chart");
      var doughnut = $("#sample_status_chart");

      var sample_perday_chart = new Chart(line, {
        type: "bar",
        data: {
          labels: per_day,
          datasets: [
            {
              label: "per_day",
              data: per_day_count,
              backgroundColor: "rgba(241, 131, 13, 0.6)",
              borderColor: "rgba(255, 99, 132, 1)",
              borderWidth: 0.1,
            },
          ],
        },
        options: {
          scales: {
            x: {
              title: {
                display: true,
                text: "Date",
              },
            },
            y: {
              title: {
                display: true,
                text: "Sample Requests",
              },
              beginAtZero: true, // Ensures the y-axis starts from zero
            },
          },
          plugins: {
            tooltip: {
              callbacks: {
                label: function (tooltipItem) {
                  return "Sample requests: " + tooltipItem.raw;
                },
              },
            },
          },
        },
      });

      var sample_chart = new Chart(bar, {
        type: "bar",
        data: {
          labels: month_labels,
          datasets: [
            {
              label: month_labels,
              data: sample_counts,
              backgroundColor: "rgba(241, 131, 13, 0.6)",
              borderColor: "rgba(255, 99, 132, 1)",
              borderWidth: 1,
            },
          ],
        },
        options: {
          scales: {
            y: {
              beginAtZero: true,
            },
          },
        },
      });

      var sample_status_chart = new Chart(doughnut, {
        type: "doughnut",
        data: {
          labels: status,
          datasets: [
            {
              label: "Sample Status",
              data: status_counts,
              backgroundColor: ["#FFC337", "#22CFCF", "#FF4069"],
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: "top",
            },
            title: {
              display: true,
              text: "Sample Status",
            },
          },
        },
      });
    },

    error: function (error) {
      console.log("Error fetching chart data:", error);
    },
  });
});
