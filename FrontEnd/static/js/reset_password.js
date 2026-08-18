document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("resetPasswordForm");

    const passwordInput =
        document.getElementById("password");

    const confirmPasswordInput =
        document.getElementById("confirmPassword");

    const passwordError =
        document.getElementById("passwordError");

    const message =
        document.getElementById("message");

    const resetButton =
        document.getElementById("resetButton");


    form.addEventListener("submit", async function (event) {

        event.preventDefault();

        message.innerHTML = "";
        passwordError.innerHTML = "";


        const password =
            passwordInput.value;

        const confirmPassword =
            confirmPasswordInput.value;


        // --------------------------------
        // Password validation
        // --------------------------------

        if (password.length < 8) {

            passwordError.textContent =
                "Password must contain at least 8 characters.";

            passwordInput.focus();

            return;
        }


        // --------------------------------
        // Confirm password validation
        // --------------------------------

        if (password !== confirmPassword) {

            passwordError.textContent =
                "Passwords do not match.";

            confirmPasswordInput.focus();

            return;
        }


        // --------------------------------
        // Disable button
        // --------------------------------

        resetButton.disabled = true;

        resetButton.textContent =
            "Resetting...";


        // --------------------------------
        // FormData
        // --------------------------------

        const formData = new FormData();

        formData.append(
            "new_password",
            password
        );

        formData.append(
            "confirm_password",
            confirmPassword
        );


        try {

            const response = await fetch(
                "/reset-password",
                {
                    method: "POST",
                    body: formData
                }
            );


            const data = await response.json();

            console.log(
                "Reset password response:",
                data
            );


            // --------------------------------
            // Error
            // --------------------------------

            if (!response.ok) {

                let errorMessage =
                    "Unable to reset password.";


                if (typeof data.detail === "string") {

                    errorMessage = data.detail;

                }
                else if (Array.isArray(data.detail)) {

                    errorMessage = data.detail
                        .map(error => {

                            if (typeof error === "string") {
                                return error;
                            }

                            return error.msg ||
                                   "Invalid input.";

                        })
                        .join("<br>");

                }
                else if (data.message) {

                    errorMessage = data.message;
                }


                message.innerHTML = `
                    <div class="alert alert-danger">
                        ${errorMessage}
                    </div>
                `;


                resetButton.disabled = false;

                resetButton.textContent =
                    "Reset Password";

                return;
            }


            // --------------------------------
            // Success
            // --------------------------------

            message.innerHTML = `
                <div class="alert alert-success">
                    ${data.message ||
                    "Password reset successfully."}
                </div>
            `;


            resetButton.disabled = true;


            // --------------------------------
            // Redirect to login
            // --------------------------------

            setTimeout(function () {

                window.location.href = "/login";

            }, 1500);


        }
        catch (error) {

            console.error(
                "Reset password error:",
                error
            );


            message.innerHTML = `
                <div class="alert alert-danger">
                    Unable to reset password.
                    Please try again.
                </div>
            `;


            resetButton.disabled = false;

            resetButton.textContent =
                "Reset Password";
        }

    });


    // --------------------------------
    // Remove error while typing
    // --------------------------------

    passwordInput.addEventListener(
        "input",
        function () {

            passwordError.textContent = "";

        }
    );


    confirmPasswordInput.addEventListener(
        "input",
        function () {

            passwordError.textContent = "";

        }
    );

});