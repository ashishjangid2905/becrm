$(document).ready(function () {
  // alert hide automatic after 2sec
  setTimeout(function () {
    $("#myAlert").hide();
  }, 2000);

  // to show and hide password
  $("#show_password").change(function () {
    var passwordField = $("#createPass, #confirmPass");
    var passwordFieldType = passwordField.attr("type");
    if (passwordFieldType === "password") {
      passwordField.attr("type", "text");
    } else {
      passwordField.attr("type", "password");
    }
  });

  $.ajax({
    url: "/sample-chart/",
    type: "GET",
    dataType: "json",
    success: function (data) {
      var month_labels = data.month_labels;
      var sample_counts = data.sample_counts;

      var rejected_sample = data.rejected_sample;
      var received_sample = data.received_sample;
      var pending_sample = data.pending_sample;

      var bar = $("#sample_chart");
      var doughnut = $("#sample_status_chart");
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
          labels: ["rejected", "received", "pending"],
          datasets: [
            {
              label: "Dataset 1",
              data: [rejected_sample, received_sample, pending_sample],
              backgroundColor: ["#FF4069", "#22CFCF", "#FFC337"],
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
              text: "Chart.js Doughnut Chart",
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
