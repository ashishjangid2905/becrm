document.addEventListener("DOMContentLoaded", () => {
    let default_url = "/dashboard/"

    const select_user = document.querySelector("#select_user")
    const select_month = document.querySelector("#select_month")

    // using Url params to updateURL
    const updateURLParams = (param, value) => {
        const url = new URL(default_url, window.location.origin)
        const params = url.searchParams

        if (value) {
            params.set(param, value)
        } else {
            params.delete(param)
        }

        default_url = url.toString()
        return default_url
    }


    if (select_user) {
        select_user.addEventListener("change", (e) => {
            const USER_ID = e.target.value
            const updatedURL = updateURLParams("select_user", USER_ID)
            macro_data(updatedURL)
        })
    }
    if (select_month) {
        select_month.addEventListener("change", (e) => {
            const month = e.target.value
            const updatedURL = updateURLParams("select_month", month)
            const updatedURL1 = `http://192.168.3.98:8000/dashboard/?select_month=${month}`
            macro_data(updatedURL)
            monthlyTable(updatedURL1)
        })
    }


    const fetchData = async (url) => {
        try {
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`)
            }

            const data = await response.json()
            // console.log("Fetched Data:", data);
            return data

        } catch (error) {
            console.error("Error fetching data:", error);
        }
    }

    const num_format = (number) => {
        new_number = new Intl.NumberFormat("en-GB", {
            style: "decimal",
            minimumFractionDigits: 0,
            notation: "compact",
            compactDisplay: "short",
        }).format(number)
        return new_number
    }

    const get_percent = (base, final) => {
        ratio = base / final
        percent = new Intl.NumberFormat("en-IN", {
            style: "percent",
            minimumFractionDigits: 0,
        }).format(ratio);
        return percent
    }

    const macro_data = async (url) => {
        const data = await fetchData(url)

        let teamsales = 0;
        let usersale = 0;
        let closed_pi = 0;
        const team_sales = document.querySelector("#team-sales");
        const user_sales = document.querySelector("#user-sales");
        const closedPi = document.querySelector("#closed-pi");

        data.forEach((pi) => {
            if (pi.pi_status === 'closed') {
                teamsales += pi.totalValue
                if (pi.pi_user === USER_DETAILS.user_id) {
                    usersale += pi.totalValue
                    closed_pi += 1
                }
            }
        });

        if (team_sales) team_sales.textContent = num_format(teamsales)
        if (user_sales) user_sales.textContent = num_format(usersale)
        if (closedPi) closedPi.textContent = closed_pi

    }


    // Show monthly lead Board 
    const leadBoard = async (url) => {
        const data = await fetchData(url)
        let leadBoardData = []

        data.forEach((pi) => {
            const team_member = pi.team_member
            let pi_date

            if (pi.pi_status === 'closed') {
                pi_date = new Date(pi.closed_at);
            } else {
                pi_date = new Date(pi.pi_date);
            }
            const month = pi_date.toLocaleString("en-US", {
                month: "short",
                year: "2-digit",
            });

            if (!leadBoardData[month]) {
                leadBoardData[month] = {
                    totalSales: 0,
                    team_member: {}
                };
            }

            if (!leadBoardData[month].team_member[team_member]) {
                leadBoardData[month].team_member[team_member] = {
                    "total_sales": 0,
                    "online_sale": 0,
                    "offline_sale": 0,
                    "domestic_sale": 0,
                    "closed": 0,
                    "open": 0,
                    "lost": 0
                };
            }

            if (pi.pi_status === 'closed') {
                leadBoardData[month].totalSales += pi.totalValue
                leadBoardData[month].team_member[team_member].total_sales += pi.totalValue
                leadBoardData[month].team_member[team_member].online_sale += pi.sales_category.online_sale
                leadBoardData[month].team_member[team_member].offline_sale += pi.sales_category.offline_sale
                leadBoardData[month].team_member[team_member].domestic_sale += pi.sales_category.domestic_sale
                leadBoardData[month].team_member[team_member].closed += 1
            }

            if (pi.pi_status === "open") {
                leadBoardData[month].team_member[team_member].open += 1
            } else if (pi.pi_status === "lost") {
                leadBoardData[month].team_member[team_member].lost += 1
            }


        });

        return leadBoardData;
    }

    const monthlyTable = async (url) => {

        const leadBoardData = await leadBoard(url)

        // console.log(leadBoardData)

        const url1 = new URL(url, window.location.origin);
        const select_month = url1.searchParams.get("select_month");
        let selected_month
        if (select_month) {
            const parseDate = new Date(select_month)
            selected_month = parseDate.toLocaleString("en-US", {
                month: "short",
                year: "2-digit",
            })
        } else {
            const parseDate = new Date()
            selected_month = parseDate.toLocaleString("en-US", {
                month: "short",
                year: "2-digit",
            })
        }

        const monthSaleTable = document.querySelector("#monthSaleTable");
        const tableBody = monthSaleTable.querySelector("tbody");
        tableBody.innerHTML = ""; // Clear existing rows

        if (!leadBoardData[selected_month]) {
            console.warn("No data available for the selected month.");
            return;
        }

        const tableHead = document.querySelector("#th_month")
        tableHead.innerHTML = selected_month

        let serialNumber = 1

        const fragment = document.createDocumentFragment();
        
        Object.keys(leadBoardData[selected_month].team_member).sort().forEach((member) => {
            const data = leadBoardData[selected_month].team_member[member];
            const row = document.createElement("tr");
            row.innerHTML = `
                <td class="text-center">${serialNumber++}</td>
                <td>${member}</td>
                <td class="text-center"><i class="ti ti-currency-rupee"></i>${num_format(data.online_sale)}</td>
                <td class="text-center"><i class="ti ti-currency-rupee"></i>${num_format(data.offline_sale)}</td>
                <td class="text-center"><i class="ti ti-currency-rupee"></i>${num_format(data.domestic_sale)}</td>
                <td class="text-center"><i class="ti ti-currency-rupee"></i> ${num_format(data.total_sales)}</td>
                <td class="text-center">${get_percent(data.total_sales, leadBoardData[selected_month].totalSales)}</td>
            `;
            fragment.appendChild(row)
        });
        tableBody.appendChild(fragment);
    }


    // Sale Bar Chart

    am5.ready(async () => {

        // create root element
        const root = am5.Root.new("saleschart")

        // Set Theme
        root.setThemes([
            am5themes_Animated.new(root)
        ]);

        // Create Chart
        const chart = root.container.children.push(am5xy.XYChart.new(root, {
            panX: false,
            panY: false,
            paddingLeft: 0,
            wheelX: "panX",
            wheelY: "zoomX",
            layout: root.verticalLayout
        }))


        // Add Legends
        const Legend = chart.children.push(am5.Legend.new(root, {
            centerX: am5.p50,
            x: am5.p50
        }))

        data = await leadBoard(default_url)

        let salesData = []

        let membersSet = new Set()

        Object.keys(data).forEach((month) => {
            let monthData = { month }
            Object.keys(data[month].team_member).forEach((member) => {
                monthData[member] = data[month].team_member[member].total_sales
                membersSet.add(member)
            })
            salesData.push(monthData)
        })

        console.log("salesData", data)

        // Create Axes
        const xRenderer = am5xy.AxisRendererX.new(root, {
            cellStartLocation: 0.1,
            cellEndLocation: 0.9,
            minorGridEnabled: true
        })

        const xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
            categoryField: "month",
            renderer: xRenderer,
            tooltip: am5.Tooltip.new(root, {})
        }))


        xRenderer.grid.template.setAll({
            location: 1
        })

        xAxis.data.setAll(salesData)

        const yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
            renderer: am5xy.AxisRendererY.new(root, {
                strokeOpacity: 0.1
            }),
            numberFormat: "#a"
        }))

        chart.topAxesContainer.children.push(am5.Label.new(root, {
            text: "Sales by Team Members",
            fontFamily: "Nunito",
            fontSize: 20,
            fontWeight: "400",
            x: am5.p50,
            centerX: am5.p50,
            paddingBottom: 20,
        }));

        // Add Series
        membersSet.forEach(member => {
            const series = chart.series.push(am5xy.ColumnSeries.new(root, {
                name: member,
                xAxis: xAxis,
                yAxis: yAxis,
                valueYField: member,
                categoryXField: "month"
            }))
            series.columns.template.setAll({
                tooltipText: "{name}: {valueY}",
                width: am5.percent(90),
                tooltipY: 0,
                strokeOpacity: 0,
            });

            series.data.setAll(salesData);

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

            Legend.data.push(series)
        });
    })  // Sales bar chart end here


    // Pi Chart for Sales on the basis of category

    const piChart = (select_month) => {

        am5.ready(async () => {


            // Create root element
            const root = am5.Root.new("salesPiChart");


            // Set themes
            // https://www.amcharts.com/docs/v5/concepts/themes/
            root.setThemes([
                am5themes_Animated.new(root)
            ]);


            // Create chart
            // https://www.amcharts.com/docs/v5/charts/percent-charts/pie-chart/
            const chart = root.container.children.push(am5percent.PieChart.new(root, {
                layout: root.verticalLayout,
                innerRadius: am5.percent(60)
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

            let data = await leadBoard(default_url)
            if (select_month) {
                const parseDate = new Date(select_month)
                selected_month = parseDate.toLocaleString("en-US", {
                    month: "short",
                    year: "2-digit",
                })
            } else {
                const parseDate = new Date()
                selected_month = parseDate.toLocaleString("en-US", {
                    month: "short",
                    year: "2-digit",
                })
            }

            let chartData = []

            Object.keys(data[selected_month].team_member).forEach((member) => {

                if (member === USER_DETAILS.team_member) {

                    chartData.push({
                        value: data[selected_month].team_member[member].online_sale,
                        category: 'Online Sales'
                    })
                    chartData.push({
                        value: data[selected_month].team_member[member].offline_sale,
                        category: 'Offline Sales'
                    })
                    chartData.push({
                        value: data[selected_month].team_member[member].domestic_sale,
                        category: 'Domestic Sales'
                    })
                }
            })

            console.log(chartData)
            // Set data
            // https://www.amcharts.com/docs/v5/charts/percent-charts/pie-chart/#Setting_data
            series.data.setAll(chartData);


            // Create legend
            const legend = chart.children.push(am5.Legend.new(root, {
                centerX: am5.percent(50),
                x: am5.percent(50),
                marginTop: 15,
                marginBottom: 15,
            }));

            legend.data.setAll(series.dataItems);


            // Play initial series animation
            series.appear(1000, 100);

        });
    }


    document.addEventListener("DOMContentLoaded", () => {
        fetchData(default_url);
        macro_data(default_url);
        monthlyTable(default_url)
        piChart();
    });
    
    fetchData(default_url)
    macro_data(default_url)
    monthlyTable(default_url)
    piChart()
})