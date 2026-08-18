document.addEventListener("DOMContentLoaded", function () {

    // =========================
    // Elements
    // =========================

    const form = document.getElementById("loginForm");

    const email = document.getElementById("email");

    const password = document.getElementById("password");

    const togglePassword =
        document.getElementById("togglePassword");

    const passwordIcon =
        document.getElementById("passwordIcon");

    const message =
        document.getElementById("message");

    const loginButton =
        document.getElementById("loginButton");

    const buttonText =
        document.getElementById("buttonText");

    const buttonSpinner =
        document.getElementById("buttonSpinner");


    // =========================
    // Show / Hide Password
    // =========================

    togglePassword.addEventListener("click", function () {

        if (password.type === "password") {

            password.type = "text";

            passwordIcon.classList.remove("bi-eye");

            passwordIcon.classList.add("bi-eye-slash");

            togglePassword.setAttribute(
                "aria-label",
                "Hide password"
            );

        } else {

            password.type = "password";

            passwordIcon.classList.remove("bi-eye-slash");

            passwordIcon.classList.add("bi-eye");

            togglePassword.setAttribute(
                "aria-label",
                "Show password"
            );
        }

    });


    // =========================
    // Login Form
    // =========================

    form.addEventListener("submit", async function (event) {

        // Stop normal form submission
        event.preventDefault();


        // Clear previous message
        message.innerHTML = "";


        const emailValue =
            email.value.trim();

        const passwordValue =
            password.value;


        // =========================
        // Validation
        // =========================

        if (!emailValue) {

            message.innerHTML = `
                <div class="alert alert-danger">
                    Please enter your email address.
                </div>
            `;

            email.focus();

            return;
        }


        if (!passwordValue) {

            message.innerHTML = `
                <div class="alert alert-danger">
                    Please enter your password.
                </div>
            `;

            password.focus();

            return;
        }


        // =========================
        // Loading
        // =========================

        loginButton.disabled = true;

        buttonText.textContent = "Logging in...";

        buttonSpinner.classList.remove("d-none");


        try {

            const formData = new FormData();

            formData.append("email", emailValue);

            formData.append(
                "password",
                passwordValue
            );


            // =========================
            // Send Login Request
            // =========================

            const response = await fetch(
                "/login",
                {
                    method: "POST",
                    body: formData,
                    credentials: "same-origin"
                }
            );


            // =========================
            // Successful Login
            // =========================

            if (response.redirected) {

                window.location.href =
                    response.url;

                return;
            }


            // =========================
            // Read Response
            // =========================

            const contentType =
                response.headers.get(
                    "content-type"
                );


            if (
                contentType &&
                contentType.includes(
                    "application/json"
                )
            ) {

                const data =
                    await response.json();


                if (!response.ok) {

                    message.innerHTML = `
                        <div class="alert alert-danger">
                            ${data.detail ||
                            "Invalid email or password."}
                        </div>
                    `;

                } else {

                    message.innerHTML = `
                        <div class="alert alert-success">
                            ${data.message ||
                            "Login successful."}
                        </div>
                    `;

                }

            } else {

                message.innerHTML = `
                    <div class="alert alert-danger">
                        Invalid email or password.
                    </div>
                `;

            }


        } catch (error) {

            console.error(
                "Login Error:",
                error
            );

            message.innerHTML = `
                <div class="alert alert-danger">
                    Unable to connect to the server.
                    Please try again.
                </div>
            `;

        } finally {

            // =========================
            // Stop Loading
            // =========================

            loginButton.disabled = false;

            buttonText.textContent = "Login";

            buttonSpinner.classList.add(
                "d-none"
            );

        }

    });

});