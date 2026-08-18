document.addEventListener("DOMContentLoaded", function () {

    const form =
        document.getElementById("registerForm");

    const password =
        document.getElementById("password");

    const confirmPassword =
        document.getElementById("confirmPassword");

    const phone =
        document.getElementById("phone");

    const passwordError =
        document.getElementById("passwordError");

    const phoneError =
        document.getElementById("phoneError");

    const registerButton =
        document.getElementById("registerButton");

    const buttonText =
        document.getElementById("buttonText");

    const buttonSpinner =
        document.getElementById("buttonSpinner");


    // --------------------------------
    // Password visibility
    // --------------------------------

    const togglePassword =
        document.getElementById("togglePassword");

    const passwordIcon =
        document.getElementById("passwordIcon");


    togglePassword.addEventListener(
        "click",
        function () {

            if (password.type === "password") {

                password.type = "text";

                passwordIcon.classList.remove(
                    "bi-eye"
                );

                passwordIcon.classList.add(
                    "bi-eye-slash"
                );

            }
            else {

                password.type = "password";

                passwordIcon.classList.remove(
                    "bi-eye-slash"
                );

                passwordIcon.classList.add(
                    "bi-eye"
                );
            }

        }
    );


    // --------------------------------
    // Confirm password visibility
    // --------------------------------

    const toggleConfirmPassword =
        document.getElementById(
            "toggleConfirmPassword"
        );

    const confirmPasswordIcon =
        document.getElementById(
            "confirmPasswordIcon"
        );


    toggleConfirmPassword.addEventListener(
        "click",
        function () {

            if (
                confirmPassword.type === "password"
            ) {

                confirmPassword.type = "text";

                confirmPasswordIcon.classList.remove(
                    "bi-eye"
                );

                confirmPasswordIcon.classList.add(
                    "bi-eye-slash"
                );

            }
            else {

                confirmPassword.type = "password";

                confirmPasswordIcon.classList.remove(
                    "bi-eye-slash"
                );

                confirmPasswordIcon.classList.add(
                    "bi-eye"
                );
            }

        }
    );


    // --------------------------------
    // Phone validation
    // --------------------------------

    phone.addEventListener(
        "input",
        function () {

            this.value =
                this.value
                    .replace(/\D/g, "")
                    .slice(0, 10);


            if (this.value.length === 10) {

                phoneError.textContent = "";

            }

        }
    );


    // --------------------------------
    // Password validation
    // --------------------------------

    confirmPassword.addEventListener(
        "input",
        function () {

            if (
                password.value !==
                confirmPassword.value
            ) {

                passwordError.textContent =
                    "Passwords do not match.";

            }
            else {

                passwordError.textContent = "";

            }

        }
    );


    // --------------------------------
    // Form submit validation
    // --------------------------------

    form.addEventListener(
        "submit",
        function (event) {


            // Phone

            if (phone.value.length !== 10) {

                event.preventDefault();

                phoneError.textContent =
                    "Please enter a valid 10-digit mobile number.";

                phone.focus();

                return;
            }


            // Password

            if (password.value.length < 8) {

                event.preventDefault();

                passwordError.textContent =
                    "Password must contain at least 8 characters.";

                password.focus();

                return;
            }


            // Confirm password

            if (
                password.value !==
                confirmPassword.value
            ) {

                event.preventDefault();

                passwordError.textContent =
                    "Passwords do not match.";

                confirmPassword.focus();

                return;
            }


            // Loading state

            registerButton.disabled = true;

            buttonText.textContent =
                "Registering...";

            buttonSpinner.classList.remove(
                "d-none"
            );

        }
    );

});