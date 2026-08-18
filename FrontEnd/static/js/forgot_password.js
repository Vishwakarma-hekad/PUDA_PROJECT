document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("forgotPasswordForm");
    const emailInput = document.getElementById("email");

    const resetButton = document.getElementById("resetButton");
    const buttonText = document.getElementById("buttonText");
    const buttonSpinner = document.getElementById("buttonSpinner");

    const message = document.getElementById("message");


    // ==========================================
    // Email validation
    // ==========================================

    function isValidEmail(email) {

        const emailPattern =
            /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        return emailPattern.test(email);
    }


    // ==========================================
    // Form Submit
    // ==========================================

    form.addEventListener("submit", async function (event) {

        event.preventDefault();

        const email = emailInput.value.trim();


        // ==========================================
        // Check empty email
        // ==========================================

        if (!email) {

            message.innerHTML = `
                <div class="alert alert-danger">
                    Please enter your email address.
                </div>
            `;

            return;
        }


        // ==========================================
        // Validate email
        // ==========================================

        if (!isValidEmail(email)) {

            emailInput.classList.add("is-invalid");

            message.innerHTML = `
                <div class="alert alert-danger">
                    Please enter a valid email address.
                </div>
            `;

            emailInput.focus();

            return;
        }


        // Remove previous validation
        emailInput.classList.remove("is-invalid");

        // Clear previous message
        message.innerHTML = "";


        // ==========================================
        // Loading state
        // ==========================================

        resetButton.disabled = true;

        buttonText.textContent = "Sending...";

        buttonSpinner.classList.remove("d-none");


        // ==========================================
        // Create FormData
        // ==========================================

        const formData = new FormData();

        formData.append("email", email);


        try {

            // ==========================================
            // Call FastAPI
            // ==========================================

            const response = await fetch(
                "/forgot-password",
                {
                    method: "POST",
                    body: formData
                }
            );


            // ==========================================
            // Read response
            // ==========================================

            const data = await response.json();


            // ==========================================
            // SUCCESS
            // ==========================================

            if (response.ok) {

                message.innerHTML = `
                    <div class="alert alert-success">
                        ${data.message || "OTP sent successfully."}
                    </div>
                `;


                buttonText.textContent = "OTP Sent";


                // ==========================================
                // Redirect to Verify OTP page
                // ==========================================

                setTimeout(function () {

                    window.location.href = "/verify-otp";

                }, 1000);

            }


            // ==========================================
            // ERROR
            // ==========================================

            else {

                message.innerHTML = `
                    <div class="alert alert-danger">
                        ${data.detail || "Unable to send OTP."}
                    </div>
                `;


                resetButton.disabled = false;

                buttonText.textContent = "Send OTP";

                buttonSpinner.classList.add("d-none");
            }


        } catch (error) {

            console.error(
                "Forgot Password Error:",
                error
            );


            message.innerHTML = `
                <div class="alert alert-danger">
                    Unable to send OTP.
                    Please try again.
                </div>
            `;


            resetButton.disabled = false;

            buttonText.textContent = "Send OTP";

            buttonSpinner.classList.add("d-none");
        }

    });


    // ==========================================
    // Remove invalid state while typing
    // ==========================================

    emailInput.addEventListener("input", function () {

        const email = emailInput.value.trim();

        if (isValidEmail(email)) {

            emailInput.classList.remove("is-invalid");

        }

    });


    // ==========================================
    // Hide server messages after 5 seconds
    // ==========================================

    setTimeout(function () {

        const serverError =
            document.getElementById("serverError");

        const serverSuccess =
            document.getElementById("serverSuccess");


        if (serverError) {

            serverError.style.display = "none";

        }


        if (serverSuccess) {

            serverSuccess.style.display = "none";

        }

    }, 5000);

});