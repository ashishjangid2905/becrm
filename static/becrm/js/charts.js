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
      let team_members = []
      let teamsales = 0;
      let usersale = 0;

      data.forEach((pi) => {
        const team_member = pi.team_member

        const pi_date = new Date(pi.pi_date);
        const month = pi_date.toLocaleString("en-US", {
          month: "short",
          year: "2-digit",
        });

        if (!months.includes(month)) {
          months.push(month);
          team_members[month] = {};
        }

        if (!team_members[month][team_member]) {
          team_members[month][team_member] = {
            "total_sales": 0,
            "online_sale": 0,
            "offline_sale": 0,
            "domestic_sale": 0,
            "closed": 0,
            "open": 0,
            "lost": 0
          };
        }

        if (pi.closed_at) {
          const piDate = new Date(pi.closed_at);
          const month = piDate.toLocaleString("en-US", {
            month: "short",
            year: "2-digit",
          });

          const team_member = pi.team_member
          const piStatus = pi.pi_status.toLocaleString("default");

          if (!months.includes(month)) {
            months.push(month);
            totalSales[month] = 0;
            userSales[month] = 0;
            team_members[month] = {};
          }

          if (!team_members[month][team_member]) {
            team_members[month][team_member] = {
              "total_sales": 0,
              "online_sale": 0,
              "offline_sale": 0,
              "domestic_sale": 0,
              "closed": 0,
              "open": 0,
              "lost": 0
            };
          }

          if (pi.pi_status === "closed") {
            totalSales[month] += pi.totalValue;
            team_members[month][team_member].total_sales += pi.totalValue
            team_members[month][team_member].online_sale += pi.sales_category.online_sale
            team_members[month][team_member].offline_sale += pi.sales_category.offline_sale
            team_members[month][team_member].domestic_sale += pi.sales_category.domestic_sale
            teamsales += pi.totalValue;
            team_members[month][team_member].closed += 1

            if (pi.pi_user === USER_DETAILS.user_id) {
              userSales[month] += pi.totalValue;
              usersale += pi.totalValue;
            }
          }
        }

        // not depends on Closed_Date
        const piStatus = pi.pi_status.toLocaleString("default");

        if (pi.pi_status === "open") {
          team_members[month][team_member].open += 1
        } else if (pi.pi_status === "lost") {
          team_members[month][team_member].lost += 1
        }

        if (!status[piStatus]) {
          status[piStatus] = 0;
        }

        if (pi.pi_user === USER_DETAILS.user_id) {
          status[piStatus] += 1;
        }

      });

      months.sort((a, b) => new Date("1 " + a) - new Date("1 " + b));

      let numFormat = new Intl.NumberFormat("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
        style: "currency",
        currency: "INR",
      });

      // Value to show in dashboard
      const currentDate = new Date();
      let currentMonth = currentDate.toLocaleString("en-US", {
        month: "short",
        year: "2-digit",
      });

      let selected_month = document.querySelector('#month_filter')

      currentMonth = "Nov 24"

      const num_format = (number) => {
        new_number = new Intl.NumberFormat("en-GB", {
          style: "decimal",
          minimumFractionDigits: 0,
          notation: "compact",
          compactDisplay: "short",
        }).format(number)
        return new_number
      }

      const get_percent = (base, final) =>{
        ratio = base/final
        percent = new Intl.NumberFormat("en-IN", {
          style: "percent",
          minimumFractionDigits: 0,
        }).format(ratio);
        return percent
      }

      console.log(get_percent)

      const team_sales = document.querySelector("#team-sales");
      const user_sales = document.querySelector("#user-sales");
      const closedPi = document.querySelector("#closed-pi");
      const monthSaleTable = document.querySelector("#monthSaleTable");
      team_sales.innerHTML = num_format(teamsales);
      user_sales.innerHTML = num_format(usersale);
      closedPi.innerHTML = status["closed"];

      const tableBody = monthSaleTable.querySelector("tbody");
      let serialNumber = 1
      Object.keys(team_members[currentMonth]).sort().forEach((member) => {
        const data = team_members[currentMonth][member];

        const row = `
          <tr>
            <td class="text-center">${serialNumber++}</td>
            <td>${member}</td>
            <td class="text-center"><i class="ti ti-currency-rupee"></i>${num_format(data.online_sale)}</td>
            <td class="text-center"><i class="ti ti-currency-rupee"></i>${num_format(data.offline_sale)}</td>
            <td class="text-center"><i class="ti ti-currency-rupee"></i>${num_format(data.domestic_sale)}</td>
            <td class="text-center"><i class="ti ti-currency-rupee"></i> ${num_format(data.total_sales)}</td>
            <td class="text-center">${get_percent(data.total_sales, totalSales[currentMonth])}</td>
            </tr>
            `;
            // <td class="text-center">${parseFloat((data.total_sales / totalSales[currentMonth]) * 100).toFixed(2) + '%'}</td>
        tableBody.insertAdjacentHTML("beforeend", row);
      });

      console.log(team_members)
      console.log(usersale)

      // testing New amCharts

      am5.ready(function () {

        // Create root element
        // https://www.amcharts.com/docs/v5/getting-started/#Root_element
        const root = am5.Root.new("saleschart");


        // Set themes
        // https://www.amcharts.com/docs/v5/concepts/themes/
        root.setThemes([
          am5themes_Animated.new(root)
        ]);


        // Create chart
        // https://www.amcharts.com/docs/v5/charts/xy-chart/
        const chart = root.container.children.push(am5xy.XYChart.new(root, {
          panX: false,
          panY: false,
          paddingLeft: 0,
          wheelX: "panX",
          wheelY: "zoomX",
          layout: root.verticalLayout
        }));


        // Add legend
        // https://www.amcharts.com/docs/v5/charts/xy-chart/legend-xy-series/
        const legend = chart.children.push(
          am5.Legend.new(root, {
            centerX: am5.p50,
            x: am5.p50
          })
        );

        const saledata = []
        const teamMembersSet = new Set()

        if (USER_DETAILS.role === 'admin') {
          Object.keys(team_members).forEach((month) => {
            const month_data = { month: month };

            Object.keys(team_members[month]).sort().forEach((team_member) => {
              month_data[team_member] = team_members[month][team_member].total_sales || 0;
              teamMembersSet.add(team_member)
            })
            saledata.push(month_data)
          })

        } else {
          Object.keys(team_members).forEach((month) => {
            const month_data = { month: month };

            Object.keys(team_members[month]).sort().forEach((team_member) => {
              month_data[team_member] = team_members[month][team_member].total_sales || 0;
              teamMembersSet.add(team_member)
            })
            saledata.push(month_data)
          })
        };

        saledata.sort((a, b) => {
          const monthA = new Date(`${a.month} 1`); // Convert to Date object for sorting
          const monthB = new Date(`${b.month} 1`);
          return monthA - monthB; // Ascending order
        });


        // Create axes
        // https://www.amcharts.com/docs/v5/charts/xy-chart/axes/
        const xRenderer = am5xy.AxisRendererX.new(root, {
          cellStartLocation: 0.1,
          cellEndLocation: 0.9,
          minorGridEnabled: true
        })

        const xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
          categoryField: "month",
          renderer: xRenderer,
          tooltip: am5.Tooltip.new(root, {})
        }));

        xRenderer.grid.template.setAll({
          location: 1
        })

        xAxis.data.setAll(saledata);

        const yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
          renderer: am5xy.AxisRendererY.new(root, {
            strokeOpacity: 0.1
          }),
          numberFormat: "#a"
        }));


        chart.topAxesContainer.children.push(am5.Label.new(root, {
          text: "Sales by Team Members",
          fontFamily: "Nunito", 
          fontSize: 20,
          fontWeight: "400",
          x: am5.p50,
          centerX: am5.p50,
          paddingBottom: 20,
        }));


        // Add series
        // https://www.amcharts.com/docs/v5/charts/xy-chart/series/

        teamMembersSet.forEach(teamMember => {
          const series = chart.series.push(am5xy.ColumnSeries.new(root, {
            name: teamMember,
            xAxis: xAxis,
            yAxis: yAxis,
            valueYField: teamMember,
            categoryXField: "month"
          }))
          series.columns.template.setAll({
            tooltipText: "{name}: {valueY}",
            width: am5.percent(90),
            tooltipY: 0,
            strokeOpacity: 0,
          });

          series.data.setAll(saledata);

          // Make stuff animate on load
          // https://www.amcharts.com/docs/v5/concepts/animations/
          series.appear();

          series.bullets.push(function () {
            return am5.Bullet.new(root, {
              locationY: 0,
              sprite: am5.Label.new(root, {
                text: "{valueY}",
                fill: root.interfaceColors.get("alternativeText"),
                centerY: 0,
                centerX: am5.p50,
                populateText: true
              })
            });
          });

          legend.data.push(series);
        });

        // Make stuff animate on load
        // https://www.amcharts.com/docs/v5/concepts/animations/
        chart.appear(1000, 100);

      }); // end am5.ready()



      am5.ready(function() {

        // Create root element
        // https://www.amcharts.com/docs/v5/getting-started/#Root_element
        const root = am5.Root.new("salesPiChart");
        
        
        // Set themes
        // https://www.amcharts.com/docs/v5/concepts/themes/
        root.setThemes([
          am5themes_Animated.new(root)
        ]);
        
        
        // Create chart
        // https://www.amcharts.com/docs/v5/charts/percent-charts/pie-chart/
        const chart = root.container.children.push(am5percent.PieChart.new(root, {
          layout: root.horizontalLayout,
          innerRadius: am5.percent(60),
        }));
        
        
        // Create series
        // https://www.amcharts.com/docs/v5/charts/percent-charts/pie-chart/#Series
        const series = chart.series.push(am5percent.PieSeries.new(root, {
          valueField: "value",
          categoryField: "category",
          alignLabels: false,
          legendValueText: "",
        }));
        
        series.labels.template.setAll({
          fontFamily: "Nunito",
          text: "",
          textType: "circular",
          centerX: 0,
          centerY: 0,
        });
        
        
        data = []

        currentMonth = 'Nov 24'

        data.push({
          value: team_members[currentMonth][USER_DETAILS.team_member].online_sale,
          category: 'online_sale'
        })
        data.push({
          value: team_members[currentMonth][USER_DETAILS.team_member].offline_sale,
          category: 'offline_sale'
        })
        data.push({
          value: team_members[currentMonth][USER_DETAILS.team_member].domestic_sale,
          category: 'domestic_sale'
        })

        console.log(data)

        // Set data
        // https://www.amcharts.com/docs/v5/charts/percent-charts/pie-chart/#Setting_data
        series.data.setAll(data);
        
        
        // Create legend
        // https://www.amcharts.com/docs/v5/charts/percent-charts/legend-percent-series/
        const legend = chart.children.push(am5.Legend.new(root, {
          centerY: am5.percent(50),
          y: am5.percent(50),
          marginTop: 15,
          marginBottom: 15,
          layout: root.verticalLayout
        }));

        legend.data.setAll(series.dataItems);
        
        
        // Play initial series animation
        // https://www.amcharts.com/docs/v5/concepts/animations/#Animation_of_series
        series.appear(1000, 100);
        
        }); // end am5.ready()


      // testing code end New amCharts


      const sales = document.querySelector("#sales-chart").getContext("2d");
      const pi = document.querySelector("#pi-pieChart").getContext("2d");

      sales_datasets = []
      backgroundColor = [
        'rgba(255, 99, 132, 0.2)',
        'rgba(255, 159, 64, 0.2)',
        'rgba(255, 205, 86, 0.2)',
        'rgba(75, 192, 192, 0.2)',
        'rgba(54, 162, 235, 0.2)',
        'rgba(153, 102, 255, 0.2)',
        'rgba(201, 203, 207, 0.2)'
      ]

      borderColor = [
        'rgb(255, 99, 132)',
        'rgb(255, 159, 64)',
        'rgb(255, 205, 86)',
        'rgb(75, 192, 192)',
        'rgb(54, 162, 235)',
        'rgb(153, 102, 255)',
        'rgb(201, 203, 207)'
      ]

      sales_datasets.push({
          label: "Total Sales",
          data: months.map((month) => totalSales[month]),
          backgroundColor: "rgba(255, 99, 132, 0.2)",
          borderColor: "rgba(255, 99, 132, 0.5)",
          borderWidth: 1,
        },
          {
            label: USER_DETAILS.team_member,
            data: months.map((month) => userSales[month]),
            backgroundColor: "rgba(54, 162, 235, 0.2)",
            borderColor: "rgba(54, 162, 235, 0.5)",
            borderWidth: 1,
          })


      // console.log(team_members)
      // console.log(sales_datasets)

      // Sales comparison chart monthwise
      const salesChart = new Chart(sales, {
        type: "bar",
        data: {
          labels: months,
          datasets: sales_datasets,
        },
        options: {
          responsive: true,
          layout: {
            padding: 10,
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                callback: function (value, index, values) {
                  return "₹" + value / 1000 + "K";
                },
                font: {
                  size: 12,
                  family: "Nunito",
                  style: "italic",
                },
              },
            },
          },
          plugins: {
            legend: {
              display: false,
              position: "top",
              align: "center",
            },
            title: {
              display: true,
              text: "MONTH-WISE SALES",
              align: "center",
              font: {
                family: "Nunito",
                size: 20,
              },
              color: "rgb(49, 134, 153)",
              padding: {
                top: 10,
                bottom: 25,
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
                "rgba(120, 206, 134, 0.8)",
                "rgba(234, 192, 13, 0.8)",
                "rgba(175, 83, 126, 0.8)",
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
                  family: "Nunito", // Font family
                  style: "italic", // Font style
                },
              },
              padding: {
                left: 30,
              },
            },
            title: {
              display: true,
              text: "PI SUMMARY",
              align: "start",
              font: {
                family: "Nunito",
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
