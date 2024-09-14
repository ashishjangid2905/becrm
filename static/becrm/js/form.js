// Function to Add Items and Remove Items

const add_lut_form = (el) => {
  let item = document.createElement("div");
  let item_class = "col-md-4";
  item.setAttribute("class", item_class);
  item.setAttribute("id", "lut-no");

  item.innerHTML =
    '<label>LUT No.</label><input class="form-control form-control-sm" type="text" name="lut_no" required />';

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

  let item_classess = "col-lg-10 order-list";
  item.setAttribute("class", item_classess);

  let new_id = "order-item" + document.querySelectorAll(".order-list").length;
  item.setAttribute("id", new_id);

  item.innerHTML = el.innerHTML;
  el.after(item);

  let remove_btn = item.querySelector("button>i");
  remove_btn.setAttribute("class", "ti ti-minus");

  remove_btn.parentElement.onclick = (e) => {
    e.preventDefault();
    item.remove();
  };

  let lumpsum_check = item.querySelector("#is-lumpsum");
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

const ls_check = (el) => {
  let parentDiv = el.closest(".order-list");
  let lumpsumPrice = parentDiv.querySelector("#item-price");

  let newDiv = document.createElement("div");
  newDiv.setAttribute("class", "col-md-5");

  newDiv.innerHTML =
    "<div class='col-md-5'><label>Lumpsum Price</label><input class='form-control form-control-sm' type='text' name='lumpsum_amt' required /></div>";

  lumpsumPrice.innerHTML = newDiv.innerHTML;
  lumpsumPrice.setAttribute("id", "lumpsum-price");
};

const handleLumpsumCheck = (e) => {
  let parentDiv = e.closest(".order-list");
  let ls_div = parentDiv.querySelector("#lumpsum-price");

  if (e.checked && !ls_div) {
    ls_check(e);
  } else if (!e.checked && ls_div) {
    let item = `<div class='col-md-5'><label>Unit Price</label><input class='form-control form-control-sm' type='text' name='unit_price' required /></div><div class='col-md-5'><label>Total Price</label><input  class='form-control form-control-sm'  type='text'  name='total_price'  required/></div>`;
    ls_div.innerHTML = item;
    ls_div.setAttribute("id", "item-price");
  }
};

let lumpsum_checks = document.querySelectorAll("#is-lumpsum");

lumpsum_checks.forEach((lumpsum_check) => {
  handleLumpsumCheck(lumpsum_check);
  lumpsum_check.addEventListener("change", () =>
    handleLumpsumCheck(lumpsum_check)
  );
});
