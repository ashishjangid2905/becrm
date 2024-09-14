// Wait for the DOM to fully load before running the script
document.addEventListener("DOMContentLoaded", function () {
  // Fetch data from Django View

  fetch("/dashboard/")
    .then((response) => response.json())
    .then((data) => {
      let months = [];
      let status = {};
      let totalSales = [];
      let userSales = {};
      let teamsales = 0;
      let usersale = 0;

      data.forEach((pi) => {
        if (pi.closed_at) {
          const piDate = new Date(pi.closed_at);
          const month = piDate.toLocaleString("en-US", {
            month: "short",
            year: "2-digit",
          });

          if (!months.includes(month)) {
            months.push(month);
            totalSales[month] = 0;
            userSales[month] = 0;
          }

          pi.order_list.forEach((order) => {
            if (pi.pi_status === "closed") {
              totalSales[month] += order.total_price;
              teamsales += order.total_price;

              if (pi.pi_user === USER_ID) {
                userSales[month] += order.total_price;
                usersale += order.total_price;
              }
            }
          });
        }

        // not depends on Closed_Date
        const piStatus = pi.pi_status.toLocaleString("default");

        if (status[piStatus]) {
          status[piStatus] += 1;
        } else {
          status[piStatus] = 1; // Initialize count if first occurrence
        }
      });

      months.sort((a, b) => new Date("1 " + a) - new Date("1 " + b));

      console.log(totalSales);
      console.log(teamsales);

      let numFormat = new Intl.NumberFormat("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
        style: "currency",
        currency: "INR",
      });

      // Value to show in dashboard
      const team_sales = document.querySelector("#team-sales");
      const user_sales = document.querySelector("#user-sales");
      const closedPi = document.querySelector("#closed-pi");
      team_sales.innerHTML = numFormat.format(teamsales / 1000) + "K";
      user_sales.innerHTML = numFormat.format(usersale / 1000) + "K";
      closedPi.innerHTML = status["closed"];

      const sales = document.querySelector("#sample-chart").getContext("2d");
      const pi = document.querySelector("#pi-pieChart").getContext("2d");

      // Sales comparison chart monthwise
      const salesChart = new Chart(sales, {
        type: "bar",
        data: {
          labels: months,
          datasets: [
            {
              label: "Total Sales",
              data: months.map((month) => totalSales[month]),
              backgroundColor: "rgba(255, 99, 132, 0.2)",
              borderColor: "rgba(255, 99, 132, 0.5)",
              borderWidth: 1,
            },
            {
              label: "User Sales",
              data: months.map((month) => userSales[month]),
              backgroundColor: "rgba(54, 162, 235, 0.2)",
              borderColor: "rgba(54, 162, 235, 0.5)",
              borderWidth: 1,
            },
          ],
        },
        options: {
          layout: {
            padding: 10,
          },
          responsive: true,
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                callback: function (value, index, values) {
                  return "₹" + value / 1000 + "K";
                },
                font: {
                  size: 12,
                  family: "sans-serif",
                  style: "italic",
                },
              },
            },
          },
          plugins: {
            legend: {
              position: "top",
              labels: {
                usePointStyle: true,
                pointStyle: "circle",
                color: "rgb(75, 171, 198)",
                font: {
                  size: 12,
                  family: "sans-serif", // Font family
                  style: "italic", // Font style
                },
              },
            },
            title: {
              display: true,
              text: "MONTH-WISE SALES",
              align: "start",
              font: {
                size: 20,
              },
              color: "rgb(13, 130, 188)",
              padding: {
                top: 10,
                bottom: 5,
              },
            },
          },
        },
      });

      // pi status pie chart

      const piStatusChart = new Chart(pi, {
        type: "doughnut",
        data: {
          labels: Object.keys(status),
          datasets: [
            {
              label: "PI Status Ratio",
              data: Object.values(status),
              backgroundColor: [
                "rgba(103, 175, 144)",
                "rgba(246, 206, 150)",
                "rgba(251, 153, 163)",
              ],
              borderColor: [
                "rgba(25, 135, 84, 0.5)",
                "rgba(240, 145, 19, 0.5)",
                "rgba(220, 53, 69, 0.5)",
              ],
              borderWidth: 1,
            },
          ],
        },
        options: {
          plugins: {
            legend: {
              display: true,
              position: "right",
              labels: {
                usePointStyle: true,
                pointStyle: "circle",
                align: "end",
                color: "rgb(75, 171, 198)",
                font: {
                  size: 12,
                  family: "Arial", // Font family
                  style: "italic", // Font style
                },
              },
              padding: {
                left: 30,
              },
            },
            title: {
              display: true,
              text: "PI SUMMERY",
              align: "start",
              font: {
                size: 20,
              },
              color: "rgb(13, 130, 188)",
              padding: {
                top: 10,
                bottom: 30,
              },
            },
          },
        },
      });
    });
});
