
const add_req_form = (e) => {
    let modal = e.closest('.modal-body')

    let reqForm = modal.querySelector('.requestTaxInvoice')

    if (e.value == 'closed') {
        reqForm.style.display = 'block'
    } else {
        reqForm.style.display = 'None' 
    }

    e.addEventListener('change', function() {
        if (e.value == 'closed') {
            reqForm.style.display = 'block'
        } else {
            reqForm.style.display = 'None' 
        }
    })
}

const add_process_form = (e) => {
    let modal = e.closest('.modal-body')

    let processForm = modal.querySelector('.processForm')

    if (e.checked) {
        processForm.style.display = 'block'
    } else {
        processForm.style.display = 'None' 
    }

    e.addEventListener('change', function() {
        if (e.checked) {
            processForm.style.display = 'block'
        } else {
            processForm.style.display = 'None' 
        }
    })
}



const add_PayForm = (e) =>{
    let item = document.createElement("div");

    let item_classess = "row g-3 mt-1 paymentForm";
    item.setAttribute("class", item_classess);

    let new_id = "payment-list" + document.querySelectorAll(".paymentForm").length;
    item.setAttribute("id", new_id);

    item.innerHTML = e.innerHTML

    let orderProcess = e.closest('.requestTaxInvoice')
    orderProcess.appendChild(item)

    let remove_btn = item.querySelector("#addPayBtn");
    remove_btn.setAttribute("id", "removePayBtn");
    remove_btn.innerHTML = '<i class="ti ti-minus"></i>'

    remove_btn.parentElement.onclick = (e) => {
        e.preventDefault();
        item.remove();
    };
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
const processChecks = document.querySelectorAll('#is-process')

statusBtns.forEach(statusBtn => {
    add_req_form(statusBtn)
});

processChecks.forEach(processCheck => {
    add_process_form(processCheck)
})

let addItemBtns = document.querySelectorAll('#add-order')

addItemBtns.forEach(addItemBtn => {
    let addOrderItem = addItemBtn.closest('#process-list0')
    addItemBtn.onclick = (e) =>{
        e.preventDefault()
        add_order(addOrderItem)
    }
});

// let savePaymentForms = document.querySelectorAll('.requestTaxInvoice')

// savePaymentForms.forEach(savePaymentForm => {
//     let addPayDtlBtn = savePaymentForm.querySelector('#addPayBtn')
//     let addPayItem = savePaymentForm.querySelector('.paymentForm')
//     addPayDtlBtn.onclick = (e) =>{
//         let removePay = savePaymentForm.querySelectorAll('.paymentForm').length
//         e.preventDefault()
//         if (removePay<3) {
//             add_PayForm(addPayItem)
//             console.log(removePay)
//         } else {
//             Swal.fire({
//                 title: 'Error!',
//                 text: 'You can accept payment in a maximum of 3 installments.',
//                 icon: 'error',
//             })
//         }
//     } 
// });

