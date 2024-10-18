// Function to Add Items and Remove Items

const add_lut_form = (el) => {
  let item = document.createElement("div");
  let item_class = "col-md-4";
  item.setAttribute("class", item_class);
  item.setAttribute("id", "lut-no");

  item.innerHTML =
    '<label>LUT No.</label><input class="form-control form-control-sm" type="text" name="lut_no" />';

  el.closest(".col-md-4").after(item);
};

let is_sez = document.querySelector("#is-sez");

is_sez.addEventListener("change", () => {
  if (is_sez.checked == true) {
    add_lut_form(is_sez);
  } else {
    let lut_no = document.querySelector("#lut-no");
    lut_no.remove();
  }
});

const add_item = (el) => {
  let item = document.createElement("div");

  let item_classess = "col-lg-10 order-list my-2";
  item.setAttribute("class", item_classess);

  let new_id = "order-item" + document.querySelectorAll(".order-list").length;
  item.setAttribute("id", new_id);

  item.innerHTML = el.innerHTML;
  let lumsum_check = item.querySelector("input[type=checkbox]")
  let category = item.querySelector("#category")
  let reportType = item.querySelector("#report-type")
  let product = item.querySelector("#product")
  let fromMonth = item.querySelector("#from-month")
  let toMonth = item.querySelector("#to-month")
  let unitPrice = item.querySelector("#unit-price")
  let totalPrice = item.querySelector("#total-price")
  let lumpsumAmt = item.querySelector("#lumpsum-amt")
  lumsum_check.checked=false
  category.value=0
  reportType.value=0
  product.value=0
  fromMonth.value=0
  toMonth.value=0
  unitPrice.value=0
  totalPrice.value=0
  lumpsumAmt.value=0

  let orderContainer = el.closest('.orders-container')
  orderContainer.appendChild(item);

  let remove_btn = item.querySelector("button>i");
  remove_btn.setAttribute("class", "ti ti-minus");

  remove_btn.parentElement.onclick = (e) => {
    e.preventDefault();
    item.remove();
  };

  let lumpsum_check = item.querySelector("#is-lumpsum");
  handleLumpsumCheck(lumpsum_check)

  lumpsum_check.addEventListener("change", () =>
    handleLumpsumCheck(lumpsum_check)
  );
  
};

let new_item = document.querySelector("#order-item"); // selected order item form need to repeat
let add_btn = document.querySelectorAll("#add-items"); // selected add button

// Adding Click event on Button
if (add_btn.length > 0) {
  add_btn[0].onclick = (e) => {
    e.preventDefault();
    //   console.log("add item");
    return add_item(new_item);
  };
}

for (let i = 1; i < add_btn.length; i++) {
  add_btn[i].innerHTML = "<i class='ti ti-minus'></i>";
  add_btn[i].onclick = (e) => {
    e.preventDefault();
    let itemToRemove = add_btn[i].closest(".order-list");
    if (itemToRemove) {
      itemToRemove.remove();
    }
  };
}

// Function to Replace unit price input to Lumpsum input

const handleLumpsumCheck = (e) => {
  let parentDiv = e.closest(".order-list");
  let itemPrice = parentDiv.querySelector("#item-price");
  let lumpsumPrice = parentDiv.querySelector("#lumpsum-price");

  let unitPrice = parentDiv.querySelector("#unit-price");
  let totalPrice = parentDiv.querySelector("#total-price");
  let lumpsumAmt = parentDiv.querySelector("#lumpsum-amt");

  if (e.checked) {
    itemPrice.style.display = "none";
    unitPrice.value = 0;
    totalPrice.value = 0;
    lumpsumPrice.style.display = "flex";
    e.value = "on"
  } else if (!e.checked) {
    itemPrice.style.display = "flex";
    lumpsumPrice.style.display = "none";
    lumpsumAmt.value = 0;
    e.value="off"
  }
};

let lumpsum_checks = document.querySelectorAll("#is-lumpsum");

lumpsum_checks.forEach((lumpsum_check) => {
  handleLumpsumCheck(lumpsum_check);
  lumpsum_check.addEventListener("change", () =>
    handleLumpsumCheck(lumpsum_check)
  );
});


document.addEventListener('DOMContentLoaded', function() {
  let fybtn = document.querySelector('#fychoise');
  let form = document.querySelector('#selectFy');

  fybtn.addEventListener('change', function() {
      // Automatically submit the form when the fiscal year is changed
      form.submit();
  });
});


