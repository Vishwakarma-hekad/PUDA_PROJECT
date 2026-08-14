// ===========================================
// pdf_report.js
// Clean Version - Part 1
// ===========================================

let reportData = [];

// ------------------------------------------
// Page Load
// ------------------------------------------
document.addEventListener("DOMContentLoaded", () => {

    const refId = document.getElementById("refId")?.value;

    if (!refId) {
        console.error("Reference ID not found.");
        return;
    }

    loadReport(refId);

});

// ------------------------------------------
// Load Report
// ------------------------------------------
async function loadReport(refId) {

    try {

        showLoader(true);

        const response = await fetch(`/applications/json-report/${refId}`);

        if (!response.ok)
            throw new Error("Unable to load report.");

        reportData = await response.json();

        renderReport(reportData);

    }
    catch (err) {

        document.getElementById("requestSummaryTable").innerHTML = `

            <div class="alert alert-danger">

                ${err.message}

            </div>

        `;

    }
    finally {

        showLoader(false);

    }

}

// ------------------------------------------
// Loader
// ------------------------------------------
function showLoader(show) {

    const loader = document.getElementById("loading");

    if (!loader)
        return;

    loader.style.display = show ? "block" : "none";

}

// ------------------------------------------
// Beautify Text
// ------------------------------------------
function beautify(text) {

    if (!text)
        return "";

    return text
        .replace(/_/g, " ")
        .replace(/\./g, " ")
        .replace(/\b\w/g, c => c.toUpperCase());

}

// ------------------------------------------
// Escape HTML
// ------------------------------------------
function escapeHtml(value) {

    if (value == null)
        return "";

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

}

// ------------------------------------------
// Format Cell
// ------------------------------------------
function renderValue(value) {

    if (value === null || value === undefined)
        return "-";

    if (typeof value === "boolean")
        return value ? "Yes" : "No";

    const text = String(value).trim().toUpperCase();

    if (text === "OK")
        return `<span class="badge bg-success">OK</span>`;

    if (text === "NOT OK")
        return `<span class="badge bg-danger">NOT OK</span>`;

    if (text === "PASS")
        return `<span class="badge bg-success">PASS</span>`;

    if (text === "FAIL")
        return `<span class="badge bg-danger">FAIL</span>`;

    return escapeHtml(value);

}

// ------------------------------------------
// Render Report
// ------------------------------------------
function renderReport(report) {

    if (!Array.isArray(report)) {

        document.getElementById("requestSummaryTable").innerHTML = `

            <div class="alert alert-danger">

                Invalid Report Format

            </div>

        `;

        return;

    }

    const requestSummary = report.find(item => item.REQUEST_SUMMARY);

    if (!requestSummary) {

        document.getElementById("requestSummaryTable").innerHTML = `

            <div class="alert alert-warning">

                REQUEST_SUMMARY not found.

            </div>

        `;

        return;

    }


    renderRequestSummary(requestSummary.REQUEST_SUMMARY);

    const projectSummary = report.find(item => item.Project_Summary);

    if (projectSummary) {
        renderProjectSummary(projectSummary.Project_Summary);
    }

    const proposedWork = report.find(item => item.ProposedWorkDimensions);

    if (proposedWork) {

    renderProposedWork(proposedWork.ProposedWorkDimensions);
    }

    const parkingSummary = report.find(item => item.PARKING_SUMMARY);

    if (parkingSummary) {

        renderParkingSummary(parkingSummary.PARKING_SUMMARY);

    }

    const roomInfo = report.find(item => item.ROOM_INFORMATION);

    if (roomInfo) {

        renderRoomInformation(roomInfo.ROOM_INFORMATION);

    }

    const netArea = report.find(item => item.NET_BUILT_UP_AREA_DETAILS_NEW);

    if (netArea) {

        renderNetBuiltupArea(netArea.NET_BUILT_UP_AREA_DETAILS_NEW);

    }

    const roomventiInfoTable = report.find(item => item.ROOM_VENTILATION_INFORMATION);

    if (roomventiInfoTable) {

        renderRoomVentilationInfo(roomventiInfoTable.ROOM_VENTILATION_INFORMATION);

    }

    const LifttoStairInfoTable = report.find(item => item.LIFT_STAIRS_INFO);

    if (LifttoStairInfoTable) {

        renderLifttoStairInfo(LifttoStairInfoTable.LIFT_STAIRS_INFO);

    }

    const BuildingtoBuildingInfoTable = report.find(item => item.BUILDING_TO_BUILDING_DISTANCES);

    if (BuildingtoBuildingInfoTable) {

        renderBuildingtoBuildingInfo(BuildingtoBuildingInfoTable.BUILDING_TO_BUILDING_DISTANCES);

    }

}

function renderDynamicTable(containerId, rows, headerClass = "table-primary") {

    const container = document.getElementById(containerId);

    if (!container)
        return;

    if (!Array.isArray(rows) || rows.length === 0) {

        container.innerHTML =
            "<div class='alert alert-warning'>No Data Available</div>";

        return;
    }

    // Get all unique column names
    const headers = [];

    rows.forEach(row => {
        Object.keys(row).forEach(key => {
            if (!headers.includes(key))
                headers.push(key);
        });
    });

    let html = `
    <div class="table-responsive">

    <table class="table table-bordered table-striped table-hover">

        <thead class="${headerClass}">

            <tr>

                <th>#</th>
    `;

    headers.forEach(header => {
        html += `<th>${beautify(header)}</th>`;
    });

    html += `
            </tr>

        </thead>

        <tbody>
    `;

    rows.forEach((row, index) => {

        html += `<tr>`;

        html += `<td>${index + 1}</td>`;

        headers.forEach(header => {

            html += `<td>${renderValue(row[header])}</td>`;

        });

        html += `</tr>`;

    });

    html += `
        </tbody>

    </table>

    </div>
    `;

    container.innerHTML = html;

}

// ===========================================
// Render REQUEST_SUMMARY
// ===========================================
function renderRequestSummary(data) {

    const container = document.getElementById("requestSummaryTable");

    if (!container)
        return;

    let html = `
        <div class="table-responsive">
            <table class="table table-bordered table-striped table-hover">

                <thead class="table-primary">
                    <tr>
                        <th style="width:35%">Field</th>
                        <th>Value</th>
                    </tr>
                </thead>

                <tbody>
    `;

    Object.entries(data).forEach(([key, value]) => {

        html += `
            <tr>
                <td>
                    <strong>${beautify(key)}</strong>
                </td>
                <td>
                    ${renderValue(value)}
                </td>
            </tr>
        `;

    });

    html += `
                </tbody>

            </table>
        </div>
    `;

    container.innerHTML = html;

}

function renderProjectSummary(data) {

    const container = document.getElementById("projectSummaryTable");

    if (!container)
        return;

    let html = `
        <div class="table-responsive">

        <table class="table table-bordered table-hover table-striped">

            <thead class="table-success">

                <tr>

                    <th style="width:35%">Field</th>

                    <th>Value</th>

                </tr>

            </thead>

            <tbody>
    `;

    Object.entries(data).forEach(([key, value]) => {

        html += `

        <tr>

            <td>

                <strong>${beautify(key)}</strong>

            </td>

            <td>

                ${renderValue(value)}

            </td>

        </tr>

        `;

    });

    html += `

            </tbody>

        </table>

        </div>
    `;

    container.innerHTML = html;

}

function renderProposedWork(data) {

    const container = document.getElementById("proposedWorkTable");

    if (!container)
        return;

    let html = `

    <div class="table-responsive">

    <table class="table table-bordered table-hover table-striped">

        <thead class="table-warning">

            <tr>

                <th style="width:35%">Field</th>

                <th>Value</th>

            </tr>

        </thead>

        <tbody>

    `;

    Object.entries(data).forEach(([key,value])=>{

        html += `

        <tr>

            <td><strong>${beautify(key)}</strong></td>

            <td>${renderValue(value)}</td>

        </tr>

        `;

    });

    html += "</tbody></table></div>";

    container.innerHTML = html;

}

function renderParkingSummary(rows) {

    const container = document.getElementById("parkingSummaryTable");

    if (!container)
        return;

    if (!Array.isArray(rows) || rows.length === 0) {

        container.innerHTML = "<div class='alert alert-warning'>No Parking Data</div>";

        return;

    }

    const headers = Object.keys(rows[0]);

    let html = `
        <div class="table-responsive">

        <table class="table table-bordered table-striped table-hover">

            <thead class="table-dark">

                <tr>

                    <th>#</th>
    `;

    headers.forEach(h => {

        html += `<th>${beautify(h)}</th>`;

    });

    html += `
                </tr>

            </thead>

            <tbody>
    `;

    rows.forEach((row,index)=>{

        html += "<tr>";

        html += `<td>${index+1}</td>`;

        headers.forEach(col=>{

            html += `
                <td>

                    ${renderValue(row[col])}

                </td>
            `;

        });

        html += "</tr>";

    });

    html += `
            </tbody>

        </table>

        </div>
    `;

    container.innerHTML = html;

}

function renderRoomInformation(rows) {

    const container = document.getElementById("roomInformationTable");

    if (!container)
        return;

    if (!Array.isArray(rows) || rows.length === 0) {

        container.innerHTML = "<div class='alert alert-warning'>No Room Information</div>";

        return;

    }

    const headers = Object.keys(rows[0]);

    let html = `
        <div class="table-responsive">

        <table class="table table-bordered table-striped table-hover">

            <thead class="table-primary">

                <tr>

                    <th>#</th>
    `;

    headers.forEach(h => {

        html += `<th>${beautify(h)}</th>`;

    });

    html += `
                </tr>

            </thead>

            <tbody>
    `;

    rows.forEach((row,index)=>{

        html += "<tr>";

        html += `<td>${index+1}</td>`;

        headers.forEach(col=>{

            html += `
                <td>

                    ${renderValue(row[col])}

                </td>
            `;

        });

        html += "</tr>";

    });

    html += `
            </tbody>

        </table>

        </div>
    `;

    container.innerHTML = html;

}

function renderNetBuiltupArea(rows) {

    renderDynamicTable(
        "netBuiltupAreaTable",
        rows,
        "table-success"
    );

}

function renderRoomVentilationInfo(rows) {

    renderDynamicTable(
        "roomventiInfo",
        rows,
        "table-success"
    );

}

function renderLifttoStairInfo(rows) {

    renderDynamicTable(
        "LifttoStairInfo",
        rows,
        "table-success"
    );

}

function renderBuildingtoBuildingInfo(rows) {

    renderDynamicTable(
        "BuildingtoBuildingInfo",
        rows,
        "table-success"
    );

}

// ===========================================
// Reload Report
// ===========================================
function reloadReport() {

    const refId = document.getElementById("refId")?.value;

    if (refId) {

        loadReport(refId);

    }

}



// ===========================================
// Print
// ===========================================
function printReport() {

    window.print();

}



// ===========================================
// Download PDF
// ===========================================
function downloadPDF() {

    const element = document.getElementById("reportContainer");

    if (!element) {

        alert("Report not found.");

        return;

    }

    html2pdf().set({

        margin: 0.4,

        filename: "Drawing_Report.pdf",

        image: {

            type: "jpeg",

            quality: 1

        },

        html2canvas: {

            scale: 2

        },

        jsPDF: {

            unit: "in",

            format: "a4",

            orientation: "portrait"

        }

    }).from(element).save();

}



// ===========================================
// Download Excel
// ===========================================
function downloadExcel() {

    const table = document.querySelector("#requestSummaryTable table");

    if (!table) {

        alert("Table not found.");

        return;

    }

    const wb = XLSX.utils.book_new();

    const ws = XLSX.utils.table_to_sheet(table);

    XLSX.utils.book_append_sheet(

        wb,

        ws,

        "REQUEST_SUMMARY"

    );

    XLSX.writeFile(

        wb,

        "Drawing_Report.xlsx"

    );

}



// ===========================================
// Copy JSON
// ===========================================
function copyJson() {

    navigator.clipboard.writeText(

        JSON.stringify(reportData, null, 2)

    );

    alert("JSON copied successfully.");

}



// ===========================================
// Download JSON
// ===========================================
function downloadJson() {

    const blob = new Blob(

        [JSON.stringify(reportData, null, 2)],

        {

            type: "application/json"

        }

    );

    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");

    a.href = url;

    a.download = "report.json";

    a.click();

    URL.revokeObjectURL(url);

}



console.log("REQUEST_SUMMARY Viewer Loaded Successfully.");