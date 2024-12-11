$(document).ready(function () {
  // alert hide automatic after 2sec
  setTimeout(function () {
    $("#myAlert").hide();
  }, 4000);

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

  let multiselectinputs = document.querySelectorAll(".multiple-select")

  multiselectinputs.forEach(multiselectinput => {
    $(multiselectinput).multipleSelect({
      selectAll: false,
      showClear: true,
      filter: true,
      dropWidth: 250
    });
  });

  // $(function () {
  //   $("#multiPort").multipleSelect({
  //     selectAll: false,
  //     showClear: true,
  //     filter: true,
  //   });
  // });


  // $(function () {
  //   $("#multiCountries").multipleSelect({
  //     selectAll: false,
  //     showClear: true,
  //     filter: true,
  //   });
  // });

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


  


  // loader implimentation

  $("form").on("submit", function () {
    $("#loader").show();
    $(":submit").prop('disabled', true);
  });

})
