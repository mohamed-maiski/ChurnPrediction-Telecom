document.addEventListener("DOMContentLoaded", function () {
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => {
    form.addEventListener("submit", function (event) {
      event.preventDefault(); // Prevent page reload

      const formData = new FormData(form);

      fetch("/predict", {
        method: "POST",
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.mode === "table") {
            document.getElementById("container-table").innerHTML =
              data.prediction;
            document.querySelector(".dropdown").style.display = "inline-block";
            styleTableRows();
            document.querySelector(".operation-table").style.display = "flex";
          } else {
            document.getElementById("prediction-container").innerHTML =
              data.prediction;
          }
        })
        .catch((error) => {
          console.error("Error:", error);
        });
    });
  });
});
document.querySelector(".close-about").onclick = () => {
  document.querySelector(".about-us").classList.add("close");
}
document.querySelector(".show-about").onclick = () => {
  document.querySelector(".about-us").classList.add("show");
  // document.querySelector(".about-us").style.height = "100% !important";
}
// download table data
function downloadCSV() {
  var csv = [];
  var rows = document.querySelectorAll("table tr");

  for (var i = 0; i < rows.length; i++) {
    var row = [],
      cols = rows[i].querySelectorAll("td, th");

    for (var j = 0; j < cols.length; j++) row.push(cols[j].innerText);

    csv.push(row.join(","));
  }

  // Create a link and trigger the download
  var csvFile = new Blob([csv.join("\n")], { type: "text/csv" });
  var downloadLink = document.createElement("a");
  downloadLink.download = "Table_Prediction_Customer.csv";
  downloadLink.href = window.URL.createObjectURL(csvFile);
  downloadLink.style.display = "none";
  document.body.appendChild(downloadLink);
  downloadLink.click();
  document.body.removeChild(downloadLink);
}

function downloadExcel() {
  let table = document.getElementById("exampleTable");
  let wb = XLSX.utils.table_to_book(table, { sheet: "Sheet1" });
  XLSX.writeFile(wb, "Table_Prediction_Customer.xlsx");
}

//

function toggleSections(showId, hideId) {
  // Show section
  let showElement = document.getElementById(showId);
  showElement.style.display = "block";
  showElement.classList.add("visible");

  // Hide section
  let hideElement = document.getElementById(hideId);
  hideElement.classList.remove("visible");
  hideElement.style.display = "none";
}
// Add event listeners for toggling sections
document
  .getElementById("singleCustomerButton")
  .addEventListener("click", showSingleCustomer);
document
  .getElementById("csvExcelButton")
  .addEventListener("click", showCSVExcel);
function showSingleCustomer() {
  toggleSections("Predict_Single_Customer", "Predict_from_CSVExcel");
}
function showCSVExcel() {
  toggleSections("Predict_from_CSVExcel", "Predict_Single_Customer");
}

// Style table rows based on churn prediction
function styleTableRows() {
  var tdElements = document.getElementsByTagName("td");
  for (var i = 0; i < tdElements.length; i++) {
    var td = tdElements[i];
    if (td.innerHTML.trim() === "Not Churn") {
      td.style.color = "green";
      td.style.fontWeight = "bold";
    } else if (td.innerHTML.trim() === "Churn") {
      td.style.color = "red";
      td.style.fontWeight = "bold";
    }
  }
}
 
// document.addEventListener("DOMContentLoaded", function () {
//   doc
//   form.addEventListener("click", function () {});
//   filter_with='churn';
//   fetch("/filter", {
//     method: "GET",
//     body: filter_with,
//   }).then((response) => response.json())
//     .then((data) => {
//       if (data.mode === "table") {
//         document.getElementById("container-table").innerHTML = data.prediction;
//         document.querySelector(".dropdown").style.display = "inline-block";
//         styleTableRows();
//       }
//     })
//     .catch((error) => {
//       console.error("Error:", error);
//     });
// });

// // Handle file upload button
const fileBtn = document.getElementById("file_csv");
const customBtn = document.getElementById("upload-button");
const customTxt = document.getElementById("custom-msg");

customBtn.addEventListener("click", function () {
  fileBtn.click();
});

fileBtn.addEventListener("change", function () {
  if (fileBtn.value) {
    customTxt.innerHTML = fileBtn.value.match(/[\/\\]([\w\d\s\.\~\(\)]+)$/)[1];
  } else {
    customTxt.innerHTML = "No file chosen, yet.";
  }
});
