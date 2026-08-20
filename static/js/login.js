/*==========================================================
                CafeSync POS
                login.js
                PART 1
==========================================================*/


/*==========================================================
                DOM ELEMENTS
==========================================================*/

const loginForm =
document.getElementById("loginForm");

const username =
document.getElementById("username");

const password =
document.getElementById("password");

const togglePassword =
document.getElementById("togglePassword");

const remember =
document.getElementById("remember");

const loadingScreen =
document.getElementById("loadingScreen");

const themeBtn =
document.getElementById("themeBtn");


/*==========================================================
                PAGE LOAD
==========================================================*/

document.addEventListener(

"DOMContentLoaded",

()=>{

    loadTheme();

    loadRememberMe();

});


/*==========================================================
                DARK MODE
==========================================================*/

themeBtn.addEventListener(

"click",

toggleTheme

);


function toggleTheme(){

    document.body.classList.toggle("dark");

    const darkMode =

    document.body.classList.contains("dark");

    localStorage.setItem(

        "cafesync_theme",

        darkMode ? "dark" : "light"

    );

    updateThemeIcon();

}


function loadTheme(){

    const savedTheme =

    localStorage.getItem(

        "cafesync_theme"

    );

    if(savedTheme==="dark"){

        document.body.classList.add("dark");

    }

    updateThemeIcon();

}


function updateThemeIcon(){

    const icon =

    themeBtn.querySelector("i");

    if(document.body.classList.contains("dark")){

        icon.className=

        "fas fa-sun";

    }

    else{

        icon.className=

        "fas fa-moon";

    }

}


/*==========================================================
                PASSWORD TOGGLE
==========================================================*/

togglePassword.addEventListener(

"click",

()=>{

    if(password.type==="password"){

        password.type="text";

        togglePassword.innerHTML=

        '<i class="fas fa-eye-slash"></i>';

    }

    else{

        password.type="password";

        togglePassword.innerHTML=

        '<i class="fas fa-eye"></i>';

    }

});


/*==========================================================
                REMEMBER ME
==========================================================*/

function loadRememberMe(){

    const savedUser =

    localStorage.getItem(

        "cafesync_username"

    );

    if(savedUser){

        username.value=savedUser;

        remember.checked=true;

    }

}


function saveRememberMe(){

    if(remember.checked){

        localStorage.setItem(

            "cafesync_username",

            username.value

        );

    }

    else{

        localStorage.removeItem(

            "cafesync_username"

        );

    }

}
/*==========================================================
                CafeSync POS
                login.js
                PART 2
        FORM VALIDATION & LOGIN
==========================================================*/


/*==========================================================
                LOGIN FORM
==========================================================*/

loginForm.addEventListener(

    "submit",

    loginUser

);


/*==========================================================
                LOGIN FUNCTION
==========================================================*/

async function loginUser(e){

    e.preventDefault();

    const user = username.value.trim();

    const pass = password.value.trim();


    /*------------------------------
            VALIDATION
    ------------------------------*/

    if(user===""){

        alert("Please enter Username.");

        username.focus();

        return;

    }

    if(pass===""){

        alert("Please enter Password.");

        password.focus();

        return;

    }

    if(pass.length<4){

        alert("Password is too short.");

        password.focus();

        return;

    }


    /*------------------------------
        SAVE REMEMBER ME
    ------------------------------*/

    saveRememberMe();


    /*------------------------------
        SHOW LOADING
    ------------------------------*/

    loadingScreen.classList.add("show");


    try{

        const response = await fetch(

            "/login",

            {

                method:"POST",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    username:user,

                    password:pass

                })

            }

        );


        const result = await response.json();


        loadingScreen.classList.remove("show");


        if(result.success){

            window.location.href="/";

        }

        else{

            alert(result.message);

        }

    }

    catch(error){

        loadingScreen.classList.remove("show");

        console.error(error);

        alert("Unable to connect to server.");

    }

}
/*==========================================================
                CafeSync POS
                login.js
                PART 3
        FORGOT PASSWORD • SOCIAL LOGIN
==========================================================*/


/*==========================================================
                AUTO FOCUS
==========================================================*/

window.addEventListener("load",()=>{

    username.focus();

});


/*==========================================================
                ENTER KEY SUPPORT
==========================================================*/

document.addEventListener("keydown",(e)=>{

    if(e.key==="Enter"){

        if(document.activeElement===username){

            password.focus();

        }

    }

});


/*==========================================================
                FORGOT PASSWORD
==========================================================*/

const forgotPassword =

document.getElementById("forgotPassword");

forgotPassword.addEventListener(

    "click",

    function(e){

        e.preventDefault();

        alert(

`Please contact the Administrator.

Email : admin@cafesync.com

Phone : +91-9876543210`

        );

    }

);


/*==========================================================
                GOOGLE LOGIN
==========================================================*/

const googleBtn =

document.querySelector(".google-btn");

googleBtn.addEventListener(

    "click",

    ()=>{

        alert(

"Google Login will be available in the next update."

        );

    }

);


/*==========================================================
                MICROSOFT LOGIN
==========================================================*/

const microsoftBtn =

document.querySelector(".microsoft-btn");

microsoftBtn.addEventListener(

    "click",

    ()=>{

        alert(

"Microsoft Login will be available in the next update."

        );

    }

);


/*==========================================================
                INPUT ANIMATION
==========================================================*/

const inputs =

document.querySelectorAll("input");

inputs.forEach(input=>{

    input.addEventListener(

        "focus",

        ()=>{

            input.parentElement.style.transform="scale(1.02)";

        }

    );

    input.addEventListener(

        "blur",

        ()=>{

            input.parentElement.style.transform="scale(1)";

        }

    );

});


/*==========================================================
                CLEAR PASSWORD AFTER FAILURE
==========================================================*/

function clearPassword(){

    password.value="";

    password.focus();

}


/*==========================================================
                LOADING HELPERS
==========================================================*/

function showLoading(){

    loadingScreen.classList.add("show");

}

function hideLoading(){

    loadingScreen.classList.remove("show");

}


/*==========================================================
                SHOW MESSAGE
==========================================================*/

function showMessage(message){

    alert(message);

}
/*==========================================================
                CafeSync POS
                login.js
                PART 4
        SESSION • LOGOUT • UTILITIES

==========================================================*/


/*==========================================================
                CHECK LOGIN STATUS
==========================================================*/

async function checkLoginStatus(){

    try{

        const response = await fetch("/verify-session");

        if(!response.ok){

            return;

        }

        const data = await response.json();

        if(data.authenticated){

            window.location.href="/";

        }

    }

    catch(error){

        console.log("Session check skipped.");

    }

}


/*==========================================================
                LOGOUT
==========================================================*/

async function logout(){

    try{

        await fetch("/logout",{

            method:"POST"

        });

        localStorage.removeItem("cafesync_username");

        window.location.href="/login";

    }

    catch(error){

        console.error(error);

    }

}


/*==========================================================
                RESET FORM
==========================================================*/

function resetForm(){

    password.value="";

    password.type="password";

    togglePassword.innerHTML=

    '<i class="fas fa-eye"></i>';

}


/*==========================================================
                INPUT TRIM
==========================================================*/

username.addEventListener(

    "blur",

    ()=>{

        username.value=username.value.trim();

    }

);

password.addEventListener(

    "blur",

    ()=>{

        password.value=password.value.trim();

    }

);


/*==========================================================
                DISABLE BUTTON
==========================================================*/

function disableLoginButton(){

    const btn=document.querySelector(".login-btn");

    btn.disabled=true;

    btn.innerHTML=

    '<i class="fas fa-spinner fa-spin"></i> Signing In...';

}


/*==========================================================
                ENABLE BUTTON
==========================================================*/

function enableLoginButton(){

    const btn=document.querySelector(".login-btn");

    btn.disabled=false;

    btn.innerHTML=

    '<i class="fas fa-right-to-bracket"></i> Login';

}


/*==========================================================
                NETWORK STATUS
==========================================================*/

window.addEventListener(

    "offline",

    ()=>{

        alert(

        "No Internet Connection."

        );

    }

);

window.addEventListener(

    "online",

    ()=>{

        console.log("Internet Connected.");

    }

);


/*==========================================================
                PAGE INITIALIZATION
==========================================================*/

function initializeLogin(){

    console.log(

        "CafeSync Login Loaded"

    );

}


document.addEventListener(

    "DOMContentLoaded",

    ()=>{

        initializeLogin();

        checkLoginStatus();

    }

);