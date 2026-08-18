document
    .getElementById("otpForm")
    .addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();

            const otp =
                document
                    .getElementById("otp")
                    .value
                    .trim();

            const button =
                document
                    .getElementById("verifyButton");

            const message =
                document
                    .getElementById("message");


            // Validate OTP

            if (!/^\d{6}$/.test(otp)) {

                message.innerHTML = `
                    <div class="alert alert-danger">
                        Please enter a valid 6-digit OTP.
                    </div>
                `;

                return;
            }


            button.disabled = true;

            button.textContent =
                "Verifying...";


            try {

                const formData =
                    new FormData();

                formData.append(
                    "otp",
                    otp
                );


                const response =
                    await fetch(
                        "/verify-otp",
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                const data =
                    await response.json();


                if (response.ok) {

                    message.innerHTML = `
                        <div class="alert alert-success">
                            OTP verified successfully.
                        </div>
                    `;


                    setTimeout(
                        function() {

                            window.location.href =
                                "/reset-password";

                        },
                        800
                    );

                }

                else {

                    message.innerHTML = `
                        <div class="alert alert-danger">
                            ${data.detail ||
                            "Invalid OTP."}
                        </div>
                    `;

                }

            }

            catch (error) {

                console.error(error);

                message.innerHTML = `
                    <div class="alert alert-danger">
                        Something went wrong.
                        Please try again.
                    </div>
                `;

            }

            finally {

                button.disabled = false;

                button.textContent =
                    "Verify OTP";

            }

        }
    );