function togglePassword(id){

    let input=document.getElementById(id);

    if(input.type==="password"){

        input.type="text";

    }
    else{

        input.type="password";

    }

}

function validateForm(){

    let password=document.getElementById("password").value;

    let confirm=document.getElementById("confirmPassword").value;

    if(password!==confirm){

        alert("Password and Confirm Password do not match.");

        return false;

    }

    if(password.length<8){

        alert("Password should be at least 8 characters.");

        return false;

    }

    return true;

}