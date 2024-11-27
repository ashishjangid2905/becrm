function updateMonthConstraints(from_month_inputs, to_month_inputs) {
    from_month_inputs = Array.from(from_month_inputs)
    to_month_inputs = Array.from(to_month_inputs)
  
    from_month_inputs.forEach((from_month_input, index) => {
        from_month_input.addEventListener("change", () =>{
            let from_month = from_month_input.value
  
            to_month_inputs[index].setAttribute("min", from_month)
        })
    });
  
    to_month_inputs.forEach((to_month_input, index) => {
        to_month_input.addEventListener("change", () =>{
            let to_month = to_month_input.value
  
            from_month_inputs[index].setAttribute("max", to_month)
        })
    });
  }