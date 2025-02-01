
const add_req_form = (e) => {
    let modal = e.closest('.modal-body')

    let reqForm = modal.querySelector('.requestTaxInvoice')
    let payDate = reqForm.querySelector('input[type=date]')

    if (e.value == 'closed') {
        reqForm.style.display = 'block'
        payDate.setAttribute('required', 'true')
    } else {
        reqForm.style.display = 'None'
        payDate.removeAttribute('required')
    }

    e.addEventListener('change', function() {
        if (e.value == 'closed') {
            reqForm.style.display = 'block'
            payDate.setAttribute('required', 'true')
        } else {
            reqForm.style.display = 'None'
            payDate.removeAttribute('required')
        }
    })
}


const add_order = (e) =>{
    let item = document.createElement("div");

    let item_classess = "row g-3 mt-2 order-process";
    item.setAttribute("class", item_classess);

    let new_id = "process-list" + document.querySelectorAll(".process-list").length;
    item.setAttribute("id", new_id);

    item.innerHTML = e.innerHTML

    let orderProcess = e.closest('.processForm')
    orderProcess.appendChild(item)

    let remove_btn = item.querySelector("#add-order");
    remove_btn.setAttribute("id", "remove-order");
    remove_btn.innerHTML = '<i class="ti ti-minus"></i>'

    remove_btn.parentElement.onclick = (e) => {
        e.preventDefault();
        item.remove();
    };
}


const statusBtns = document.querySelectorAll('#pi-status-choice')

statusBtns.forEach(statusBtn => {
    add_req_form(statusBtn)
});

let addItemBtns = document.querySelectorAll('#add-order')

addItemBtns.forEach(addItemBtn => {
    let addOrderItem = addItemBtn.closest('#process-list0')
    addItemBtn.onclick = (e) =>{
        e.preventDefault()
        add_order(addOrderItem)
    }
});


const pi_feedback = document.querySelectorAll(".feedback")

console.log(pi_feedback)

if (pi_feedback) {
    pi_feedback.forEach((pi, index) => {
        pi.addEventListener("change", (e) => {
            const modal = pi.closest(".modal-footer")
            if (modal) {
                const submit_btn = modal.querySelector(".submit-btn");
                if (submit_btn) { // Ensure the submit button exists
                    if (e.target.value.length != 0) {
                        submit_btn.setAttribute("class", "btn btn-warning submit-btn")
                        submit_btn.innerHTML = "Not Approve"; // Update the button value
                        console.log(`Submit button updated for feedback index ${index}`);
                    } else {
                        submit_btn.setAttribute("class", "btn btn-primary submit-btn")
                        submit_btn.innerHTML = "Approve"; // Update the button value
                        console.error("Submit button not found in the modal-footer");
                    }
                } else {
                    console.error("Modal-footer not found for this feedback element");
                }
            }
        })
    })
}

