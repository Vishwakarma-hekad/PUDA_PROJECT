// ===========================================
// pdf_report.js
// Professional Drawing Scrutiny Report
// ===========================================

let reportData = [];


// ===========================================
// PAGE LOAD
// ===========================================

document.addEventListener("DOMContentLoaded", () => {

    const refId = document.getElementById("refId")?.value;

    if (!refId) {
        console.error("Reference ID not found.");
        return;
    }

    loadReport(refId);

});


// ===========================================
// LOAD REPORT
// ===========================================

async function loadReport(refId) {

    try {

        showLoader(true);

        const response =
            await fetch(`/applications/json-report/${refId}`);

        if (!response.ok)
            throw new Error("Unable to load report.");

        reportData = await response.json();

        renderReport(reportData);

    }

    catch (err) {

        const container =
            document.getElementById("requestSummaryTable");

        if (container) {

            container.innerHTML = `
                <div class="alert alert-danger">
                    ${escapeHtml(err.message)}
                </div>
            `;

        }

    }

    finally {

        showLoader(false);

    }

}


// ===========================================
// LOADER
// ===========================================

function showLoader(show) {

    const loader =
        document.getElementById("loading");

    if (!loader)
        return;

    loader.style.display =
        show ? "block" : "none";

}


// ===========================================
// BEAUTIFY TEXT
// ===========================================

function beautify(text) {

    if (!text)
        return "";

    return String(text)
        .replace(/_/g, " ")
        .replace(/\./g, " ")
        .replace(/\b\w/g, c => c.toUpperCase());

}


// ===========================================
// ESCAPE HTML
// ===========================================

function escapeHtml(value) {

    if (value == null)
        return "";

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}


// ===========================================
// RENDER VALUE
// ===========================================

function renderValue(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return "-";

    }


    if (typeof value === "boolean") {

        return value
            ? `<span class="status-ok">Yes</span>`
            : `<span class="status-not-ok">No</span>`;

    }


    const text =
        String(value).trim().toUpperCase();


    if (text === "OK") {

        return `
            <span class="status-ok">
                OK
            </span>
        `;

    }


    if (text === "NOT OK") {

        return `
            <span class="status-not-ok">
                NOT OK
            </span>
        `;

    }


    if (text === "PASS") {

        return `
            <span class="status-ok">
                PASS
            </span>
        `;

    }


    if (text === "FAIL") {

        return `
            <span class="status-not-ok">
                FAIL
            </span>
        `;

    }


    return escapeHtml(value);

}


// ===========================================
// RENDER REPORT
// ===========================================

function renderReport(report) {

    if (!Array.isArray(report)) {

        document.getElementById(
            "requestSummaryTable"
        ).innerHTML = `

            <div class="alert alert-danger">

                Invalid Report Format

            </div>

        `;

        return;

    }


    // REQUEST SUMMARY

    const requestSummary =
        report.find(
            item => item.REQUEST_SUMMARY
        );


    if (!requestSummary) {

        document.getElementById(
            "requestSummaryTable"
        ).innerHTML = `

            <div class="alert alert-warning">

                REQUEST_SUMMARY not found.

            </div>

        `;

        return;

    }


    renderRequestSummary(
        requestSummary.REQUEST_SUMMARY
    );


    // PROJECT SUMMARY

    const projectSummary =
        report.find(
            item => item.Project_Summary
        );


    if (projectSummary) {

        renderProjectSummary(
            projectSummary.Project_Summary
        );

    }


    // PROPOSED WORK

    const proposedWork =
        report.find(
            item => item.ProposedWorkDimensions
        );


    if (proposedWork) {

        renderProposedWork(
            proposedWork.ProposedWorkDimensions
        );

    }


    // PARKING

    const parkingSummary =
        report.find(
            item => item.PARKING_SUMMARY
        );


    if (parkingSummary) {

        renderParkingSummary(
            parkingSummary.PARKING_SUMMARY
        );

    }


    // ROOM INFORMATION

    const roomInfo =
        report.find(
            item => item.ROOM_INFORMATION
        );


    if (roomInfo) {

        renderRoomInformation(
            roomInfo.ROOM_INFORMATION
        );

    }


    // NET BUILT UP AREA

    const netArea =
        report.find(
            item => item.NET_BUILT_UP_AREA_DETAILS_NEW
        );


    if (netArea) {

        renderNetBuiltupArea(
            netArea.NET_BUILT_UP_AREA_DETAILS_NEW
        );

    }


    // ROOM VENTILATION

    const roomventiInfoTable =
        report.find(
            item => item.ROOM_VENTILATION_INFORMATION
        );


    if (roomventiInfoTable) {

        renderRoomVentilationInfo(
            roomventiInfoTable
                .ROOM_VENTILATION_INFORMATION
        );

    }


    // LIFT / STAIR

    const LifttoStairInfoTable =
        report.find(
            item => item.LIFT_STAIRS_INFO
        );


    if (LifttoStairInfoTable) {

        renderLifttoStairInfo(
            LifttoStairInfoTable
                .LIFT_STAIRS_INFO
        );

    }


    // BUILDING TO BUILDING

    const BuildingtoBuildingInfoTable =
        report.find(
            item => item.BUILDING_TO_BUILDING_DISTANCES
        );


    if (BuildingtoBuildingInfoTable) {

        renderBuildingtoBuildingInfo(
            BuildingtoBuildingInfoTable
                .BUILDING_TO_BUILDING_DISTANCES
        );

    }

}


// ===========================================
// GENERIC TABLE
// ===========================================

function renderDynamicTable(
    containerId,
    rows
) {

    const container =
        document.getElementById(containerId);


    if (!container)
        return;


    if (
        !Array.isArray(rows) ||
        rows.length === 0
    ) {

        container.innerHTML = `

            <div class="no-data">

                No Data Available

            </div>

        `;

        return;

    }


    // Get all unique headers

    const headers = [];


    rows.forEach(row => {

        if (
            row &&
            typeof row === "object" &&
            !Array.isArray(row)
        ) {

            Object.keys(row).forEach(key => {

                if (!headers.includes(key)) {

                    headers.push(key);

                }

            });

        }

    });


    let html = `

        <div class="table-responsive">

            <table class="table report-table">

                <thead>

                    <tr>

                        <th class="serial-column">
                            #
                        </th>

    `;


    headers.forEach(header => {

        html += `

            <th>
                ${beautify(header)}
            </th>

        `;

    });


    html += `

                    </tr>

                </thead>

                <tbody>

    `;


    rows.forEach((row, index) => {

        html += `

            <tr>

                <td class="serial-number">
                    ${index + 1}
                </td>

        `;


        headers.forEach(header => {

            html += `

                <td>

                    ${renderValue(row?.[header])}

                </td>

            `;

        });


        html += `

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


// ===========================================
// REQUEST SUMMARY
// ===========================================

function renderRequestSummary(data) {

    const container =
        document.getElementById(
            "requestSummaryTable"
        );


    if (!container)
        return;


    if (
        !data ||
        typeof data !== "object"
    ) {

        container.innerHTML = `

            <div class="no-data">

                No Request Summary Available

            </div>

        `;

        return;

    }


    let html = `

        <div class="table-responsive">

            <table class="table report-table">

                <thead>

                    <tr>

                        <th style="width:35%">
                            Field
                        </th>

                        <th>
                            Value
                        </th>

                    </tr>

                </thead>

                <tbody>

    `;


    Object.entries(data).forEach(
        ([key, value]) => {

            html += `

                <tr>

                    <td>
                        <strong>
                            ${beautify(key)}
                        </strong>
                    </td>

                    <td>
                        ${renderValue(value)}
                    </td>

                </tr>

            `;

        }
    );


    html += `

                </tbody>

            </table>

        </div>

    `;


    container.innerHTML = html;

}


// ===========================================
// PROJECT SUMMARY
// ===========================================

function renderProjectSummary(data) {

    const container =
        document.getElementById(
            "projectSummaryTable"
        );


    if (!container)
        return;


    if (
        !data ||
        typeof data !== "object"
    ) {

        container.innerHTML = `

            <div class="no-data">

                No Project Summary Available

            </div>

        `;

        return;

    }


    let html = `

        <div class="table-responsive">

            <table class="table report-table">

                <thead>

                    <tr>

                        <th style="width:35%">
                            Field
                        </th>

                        <th>
                            Value
                        </th>

                    </tr>

                </thead>

                <tbody>

    `;


    Object.entries(data).forEach(
        ([key, value]) => {

            html += `

                <tr>

                    <td>

                        <strong>
                            ${beautify(key)}
                        </strong>

                    </td>

                    <td>
                        ${renderValue(value)}
                    </td>

                </tr>

            `;

        }
    );


    html += `

                </tbody>

            </table>

        </div>

    `;


    container.innerHTML = html;

}


// ===========================================
// PROPOSED WORK
// ===========================================

function renderProposedWork(data) {

    const container =
        document.getElementById(
            "proposedWorkTable"
        );


    if (!container)
        return;


    if (
        !data ||
        typeof data !== "object"
    ) {

        container.innerHTML = `

            <div class="no-data">

                No Proposed Work Data Available

            </div>

        `;

        return;

    }


    let html = `

        <div class="table-responsive">

            <table class="table report-table">

                <thead>

                    <tr>

                        <th style="width:35%">
                            Field
                        </th>

                        <th>
                            Value
                        </th>

                    </tr>

                </thead>

                <tbody>

    `;


    Object.entries(data).forEach(
        ([key, value]) => {

            html += `

                <tr>

                    <td>

                        <strong>
                            ${beautify(key)}
                        </strong>

                    </td>

                    <td>
                        ${renderValue(value)}
                    </td>

                </tr>

            `;

        }
    );


    html += `

                </tbody>

            </table>

        </div>

    `;


    container.innerHTML = html;

}


// ===========================================
// PARKING SUMMARY
// ===========================================

function renderParkingSummary(rows) {

    const container =
        document.getElementById(
            "parkingSummaryTable"
        );


    if (!container)
        return;


    if (
        !Array.isArray(rows) ||
        rows.length === 0
    ) {

        container.innerHTML = `

            <div class="no-data">

                No Parking Data Available

            </div>

        `;

        return;

    }


    // Collect all unique headers

    const headers = [];


    rows.forEach(row => {

        Object.keys(row).forEach(key => {

            if (!headers.includes(key)) {

                headers.push(key);

            }

        });

    });


    let html = `

        <div class="table-responsive">

            <table class="table report-table">

                <thead>

                    <tr>

                        <th class="serial-column">
                            #
                        </th>

    `;


    headers.forEach(header => {

        html += `

            <th>
                ${beautify(header)}
            </th>

        `;

    });


    html += `

                    </tr>

                </thead>

                <tbody>

    `;


    rows.forEach((row, index) => {

        html += `

            <tr>

                <td class="serial-number">
                    ${index + 1}
                </td>

        `;


        headers.forEach(header => {

            html += `

                <td>
                    ${renderValue(row[header])}
                </td>

            `;

        });


        html += `

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


// ===========================================
// ROOM INFORMATION
// ===========================================

function renderRoomInformation(rows) {

    const container =
        document.getElementById(
            "roomInformationTable"
        );


    if (!container)
        return;


    if (
        !Array.isArray(rows) ||
        rows.length === 0
    ) {

        container.innerHTML = `

            <div class="no-data">

                No Room Information Available

            </div>

        `;

        return;

    }


    const headers = [];


    rows.forEach(row => {

        Object.keys(row).forEach(key => {

            if (!headers.includes(key)) {

                headers.push(key);

            }

        });

    });


    let html = `

        <div class="table-responsive">

            <table class="table report-table">

                <thead>

                    <tr>

                        <th class="serial-column">
                            #
                        </th>

    `;


    headers.forEach(header => {

        html += `

            <th>
                ${beautify(header)}
            </th>

        `;

    });


    html += `

                    </tr>

                </thead>

                <tbody>

    `;


    rows.forEach((row, index) => {

        html += `

            <tr>

                <td class="serial-number">
                    ${index + 1}
                </td>

        `;


        headers.forEach(header => {

            html += `

                <td>
                    ${renderValue(row[header])}
                </td>

            `;

        });


        html += `

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


// ===========================================
// NET BUILT UP AREA
// ===========================================

function renderNetBuiltupArea(rows) {

    renderDynamicTable(
        "netBuiltupAreaTable",
        rows
    );

}


// ===========================================
// ROOM VENTILATION
// ===========================================

function renderRoomVentilationInfo(rows) {

    renderDynamicTable(
        "roomventiInfo",
        rows
    );

}


// ===========================================
// LIFT TO STAIR
// ===========================================

function renderLifttoStairInfo(rows) {

    renderDynamicTable(
        "LifttoStairInfo",
        rows
    );

}


// ===========================================
// BUILDING TO BUILDING
// ===========================================

function renderBuildingtoBuildingInfo(rows) {

    renderDynamicTable(
        "BuildingtoBuildingInfo",
        rows
    );

}


// ===========================================
// RELOAD REPORT
// ===========================================

function reloadReport() {

    const refId =
        document.getElementById("refId")?.value;


    if (refId) {

        loadReport(refId);

    }

}


// ===========================================
// PRINT REPORT
// ===========================================

function printReport() {

    window.print();

}


// ===========================================
// DOWNLOAD PDF
// ===========================================

function downloadPDF() {

    /*
       Your HTML uses:

       <div id="reportContent">

       Therefore use reportContent here.
    */

    const element =
        document.getElementById(
            "reportContent"
        );


    if (!element) {

        alert("Report not found.");

        return;

    }


    const refId =
        document.getElementById("refId")?.value
        || "Report";


    const options = {

        margin: 0.35,

        filename:
            `Drawing_Report_${refId}.pdf`,

        image: {

            type: "jpeg",

            quality: 0.98

        },

        html2canvas: {

            scale: 2,

            useCORS: true,

            backgroundColor: "#ffffff",

            logging: false

        },

        jsPDF: {

            unit: "in",

            format: "a4",

            orientation: "portrait"

        },

        pagebreak: {

            mode: [
                "avoid-all",
                "css",
                "legacy"
            ]

        }

    };


    html2pdf()
        .set(options)
        .from(element)
        .save();

}


// ===========================================
// DOWNLOAD EXCEL
// ===========================================

function downloadExcel() {

    const tables =
        document.querySelectorAll(
            "#reportContent table"
        );


    if (!tables.length) {

        alert("No report tables found.");

        return;

    }


    const wb =
        XLSX.utils.book_new();


    /*
       Add every report section
       as a separate Excel sheet.
    */

    tables.forEach((table, index) => {

        const ws =
            XLSX.utils.table_to_sheet(
                table
            );


        let sheetName =
            `Report_${index + 1}`;


        const parent =
            table.closest(".card");


        if (parent) {

            const title =
                parent.querySelector(
                    ".card-header h5"
                );


            if (title) {

                sheetName =
                    title.innerText
                        .trim()
                        .substring(0, 31);

            }

        }


        XLSX.utils.book_append_sheet(
            wb,
            ws,
            sheetName
        );

    });


    const refId =
        document.getElementById("refId")?.value
        || "Report";


    XLSX.writeFile(
        wb,
        `Drawing_Report_${refId}.xlsx`
    );

}


// ===========================================
// COPY JSON
// ===========================================

async function copyJson() {

    try {

        await navigator.clipboard.writeText(
            JSON.stringify(
                reportData,
                null,
                2
            )
        );


        alert(
            "JSON copied successfully."
        );

    }

    catch (error) {

        console.error(
            "Unable to copy JSON:",
            error
        );


        /*
           Fallback for older browsers
        */

        const textarea =
            document.createElement("textarea");


        textarea.value =
            JSON.stringify(
                reportData,
                null,
                2
            );


        document.body.appendChild(
            textarea
        );


        textarea.select();

        document.execCommand("copy");

        textarea.remove();


        alert(
            "JSON copied successfully."
        );

    }

}


// ===========================================
// DOWNLOAD JSON
// ===========================================

function downloadJson() {

    const blob =
        new Blob(
            [
                JSON.stringify(
                    reportData,
                    null,
                    2
                )
            ],
            {
                type: "application/json"
            }
        );


    const url =
        URL.createObjectURL(blob);


    const a =
        document.createElement("a");


    a.href = url;

    a.download =
        "report.json";


    document.body.appendChild(a);

    a.click();

    a.remove();


    URL.revokeObjectURL(url);

}


// ===========================================
// EXPAND ALL SECTIONS
// ===========================================

function expandAllSections() {

    document
        .querySelectorAll(
            "#reportContent .card-body"
        )
        .forEach(body => {

            body.style.display = "block";

        });

}


// ===========================================
// COLLAPSE ALL SECTIONS
// ===========================================

function collapseAllSections() {

    document
        .querySelectorAll(
            "#reportContent .card-body"
        )
        .forEach(body => {

            body.style.display = "none";

        });

}


// ===========================================
// REPORT SEARCH
// ===========================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const search =
            document.getElementById(
                "searchText"
            );


        if (!search)
            return;


        search.addEventListener(
            "input",
            function () {

                const keyword =
                    this.value
                        .trim()
                        .toLowerCase();


                const rows =
                    document.querySelectorAll(
                        "#reportContent table tbody tr"
                    );


                rows.forEach(row => {

                    const text =
                        row.innerText
                            .toLowerCase();


                    row.style.display =
                        !keyword ||
                        text.includes(keyword)
                            ? ""
                            : "none";

                });

            }
        );

    }
);


// ===========================================
// FINAL MESSAGE
// ===========================================

console.log(
    "Professional Drawing Report Loaded Successfully."
);