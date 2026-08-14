const steps = [
    "Drawing Submitted",
    "DWG Conversion",
    "Reading Layers",
    "Extracting Report Data",
    "Generating Report",
    "Generating PDF",
    "Completed"
];

let polling = null;


// =========================================================
// PAGE LOAD
// =========================================================

window.onload = function () {

    // Get Reference ID from hidden input
    const refElement =
        document.getElementById("hiddenRefId");

    if (!refElement) {

        console.error(
            "hiddenRefId element not found"
        );

        return;
    }

    const refId =
        refElement.value.trim();

    if (!refId) {

        console.log(
            "No Reference ID found"
        );

        return;
    }

    console.log(
        "Reference ID:",
        refId
    );


    // Load status immediately
    loadStatus(refId);


    // Poll every 3 seconds
    polling = setInterval(function () {

        loadStatus(refId);

    }, 3000);
};


// =========================================================
// LOAD STATUS
// =========================================================

async function loadStatus(refId) {

    try {

        const url =
            `/processing/status/${encodeURIComponent(refId)}`;

        console.log(
            "Fetching:",
            url
        );


        const response =
            await fetch(url);


        console.log(
            "Response status:",
            response.status
        );


        if (!response.ok) {

            console.error(
                "Unable to fetch status:",
                response.status
            );

            return;
        }


        const data =
            await response.json();


        console.log(
            "Processing Status:",
            data
        );


        // Backend returned error
        if (data.msg) {

            console.error(
                "Backend:",
                data.msg
            );

            return;
        }


        updateStatus(data);

    }
    catch (err) {

        console.error(
            "Status request error:",
            err
        );

    }
}


// =========================================================
// UPDATE STATUS
// =========================================================

function updateStatus(data) {


    // =====================================================
    // REPORT STATUS
    // =====================================================

    const reportBadge =
        document.getElementById(
            "reportstatusBadge"
        );


    const status =
        (data.status || "")
            .toLowerCase()
            .trim();


    if (reportBadge) {

        reportBadge.textContent =
            data.status || "-";


        reportBadge.className =
            "badge fs-6";


        switch (status) {

            case "submitted":

                reportBadge.classList.add(
                    "bg-info"
                );

                break;


            case "processing":

                reportBadge.classList.add(
                    "bg-warning",
                    "text-dark"
                );

                break;


            case "completed":

                reportBadge.classList.add(
                    "bg-success"
                );

                break;


            case "failed":

                reportBadge.classList.add(
                    "bg-danger"
                );

                break;


            default:

                reportBadge.classList.add(
                    "bg-secondary"
                );

                break;
        }
    }


    // =====================================================
    // PDF STATUS
    // Keep empty as requested
    // =====================================================

    const pdfBadge =
        document.getElementById(
            "pdfstatusBadge"
        );


    if (pdfBadge) {

        pdfBadge.textContent = "";

    }


    // =====================================================
    // SCRUTINY STATUS
    // Keep empty as requested
    // =====================================================

    const scrutinyBadge =
        document.getElementById(
            "scrutinystatusBadge"
        );


    if (scrutinyBadge) {

        scrutinyBadge.textContent = "";

    }


    // =====================================================
    // CURRENT STEP
    // Keep empty as requested
    // =====================================================

    const currentStep =
        document.getElementById(
            "currentStep"
        );


    if (currentStep) {

        currentStep.textContent = "";

    }


    // =====================================================
    // ESTIMATED TIME
    // Keep empty as requested
    // =====================================================

    const estimatedTime =
        document.getElementById(
            "estimatedTime"
        );


    if (estimatedTime) {

        estimatedTime.textContent = "";

    }


    // =====================================================
    // EXECUTED TIME
    // Keep empty as requested
    // =====================================================

    const executedTime =
        document.getElementById(
            "executedTime"
        );


    if (executedTime) {

        executedTime.textContent = "";

    }


    // =====================================================
    // PROGRESS
    // =====================================================

    let percent =
        Number(data.progress || 0);


    percent =
        Math.max(
            0,
            Math.min(
                100,
                percent
            )
        );


    const progress =
        document.getElementById(
            "overallProgress"
        );


    if (progress) {

        progress.style.width =
            percent + "%";


        progress.textContent =
            percent + "%";


        progress.setAttribute(
            "aria-valuenow",
            percent
        );

    }


    // =====================================================
    // TIMELINE
    // =====================================================

    const timeline =
        document.getElementById(
            "timelineList"
        );


    if (!timeline) {

        return;

    }


    const currentStepNo =
        Number(
            data.step_no || 1
        );


    let html = "";


    // =====================================================
    // REPORT COMPLETED
    // =====================================================

    /*
     * IMPORTANT:
     *
     * If report_status/status is "completed",
     * ALL 7 STEPS become GREEN with check marks.
     */

    if (status === "completed") {

        steps.forEach(function (step) {

            html += `
                <li class="list-group-item text-success">

                    <i class="bi bi-check-circle-fill me-2"></i>

                    ${step}

                </li>
            `;

        });

    }


    // =====================================================
    // REPORT FAILED
    // =====================================================

    else if (status === "failed") {

        steps.forEach(function (step, index) {


            // Previous steps = completed
            if (index < currentStepNo - 1) {

                html += `
                    <li class="list-group-item text-success">

                        <i class="bi bi-check-circle-fill me-2"></i>

                        ${step}

                    </li>
                `;

            }


            // Current step = failed
            else if (index === currentStepNo - 1) {

                html += `
                    <li class="list-group-item text-danger fw-bold">

                        <i class="bi bi-x-circle-fill me-2"></i>

                        ${step}

                    </li>
                `;

            }


            // Remaining steps = pending
            else {

                html += `
                    <li class="list-group-item text-secondary">

                        <i class="bi bi-circle me-2"></i>

                        ${step}

                    </li>
                `;

            }

        });

    }


    // =====================================================
    // SUBMITTED / PROCESSING
    // =====================================================

    else {

        steps.forEach(function (step, index) {


            // Completed steps
            if (index < currentStepNo - 1) {

                html += `
                    <li class="list-group-item text-success">

                        <i class="bi bi-check-circle-fill me-2"></i>

                        ${step}

                    </li>
                `;

            }


            // Current step
            else if (index === currentStepNo - 1) {

                html += `
                    <li class="list-group-item text-primary fw-bold">

                        <i class="bi bi-arrow-right-circle-fill me-2"></i>

                        ${step}

                    </li>
                `;

            }


            // Pending steps
            else {

                html += `
                    <li class="list-group-item text-secondary">

                        <i class="bi bi-circle me-2"></i>

                        ${step}

                    </li>
                `;

            }

        });

    }


    // Put timeline into HTML
    timeline.innerHTML =
        html;


    // =====================================================
    // STOP POLLING
    // =====================================================

    if (
        status === "completed" ||
        status === "failed"
    ) {

        if (polling) {

            clearInterval(
                polling
            );

            polling = null;

        }


        console.log(
            "Polling stopped:",
            status
        );

    }

}