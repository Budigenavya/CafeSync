/*==========================================================
                CafeSync POS
                menu.js
                PART 1
==========================================================*/


/*==========================================================
                DOM ELEMENTS
==========================================================*/

const menuBtn =
document.getElementById("menuToggle");

const sideMenu =
document.getElementById("sideMenu");

const menuOverlay =
document.getElementById("menuOverlay");

const darkModeBtn =
document.getElementById("darkModeBtn");


/*==========================================================
                OPEN MENU
==========================================================*/

function openMenu(){

    sideMenu.classList.add("active");

    menuOverlay.classList.add("active");

}


/*==========================================================
                CLOSE MENU
==========================================================*/

function closeMenu(){

    sideMenu.classList.remove("active");

    menuOverlay.classList.remove("active");

}


/*==========================================================
                TOGGLE MENU
==========================================================*/



if (menuBtn && sideMenu) {

    menuBtn.addEventListener("click", () => {

        if (sideMenu.classList.contains("active")) {

            closeMenu();

        } else {

            openMenu();

        }

    });

}


/*==========================================================
                CLOSE ON OVERLAY
==========================================================*/

if (menuOverlay) {
    menuOverlay.addEventListener(
        "click",
        closeMenu
    );
}


/*==========================================================
                ESC KEY
==========================================================*/

document.addEventListener(

    "keydown",

    (e)=>{

        if(

            e.key==="Escape"

            &&

            sideMenu.classList.contains("active")

        ){

            closeMenu();

        }

    }

);


/*==========================================================
                CLOSE MENU ON MOBILE
==========================================================*/

const menuLinks =

document.querySelectorAll(

"#sideMenu a"

);

menuLinks.forEach(link=>{

    link.addEventListener(

        "click",

        ()=>{

            if(window.innerWidth<=768){

                closeMenu();

            }

        }

    );

});
/*==========================================================
                CafeSync POS
                menu.js
                PART 2
        DARK MODE & ACTIVE MENU
==========================================================*/


/*==========================================================
                LOAD THEME
==========================================================*/

window.addEventListener(

    "DOMContentLoaded",

    ()=>{

        loadTheme();

        highlightActiveMenu();

    }

);


/*==========================================================
                DARK MODE
==========================================================*/

if (darkModeBtn) {

    darkModeBtn.addEventListener(
        "click",
        toggleDarkMode
    );

}


function updateThemeIcon() {

    const darkModeBtn =
        document.getElementById("darkModeBtn");

    if (!darkModeBtn) {
        return;
    }

    const icon =
        darkModeBtn.querySelector("i");

    if (!icon) {
        return;
    }

    if (document.body.classList.contains("dark-mode")) {

        icon.classList.remove("fa-moon");
        icon.classList.add("fa-sun");

    } else {

        icon.classList.remove("fa-sun");
        icon.classList.add("fa-moon");

    }
}


/*==========================================================
                LOAD SAVED THEME
==========================================================*/

function loadTheme() {

    const savedTheme = localStorage.getItem("theme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
    } else {
        document.body.classList.remove("dark-mode");
    }

    updateThemeIcon();
}


/*==========================================================
                CHANGE ICON
==========================================================*/

function updateThemeIcon() {

    const themeToggle = document.getElementById("themeToggle");

    // Theme toggle does not exist on this page
    if (!themeToggle) {
        return;
    }

    const icon = themeToggle.querySelector("i");

    // No icon inside theme toggle
    if (!icon) {
        return;
    }

    if (document.body.classList.contains("dark-mode")) {

        icon.className = "fas fa-sun";

    } else {

        icon.className = "fas fa-moon";

    }
}


/*==========================================================
                ACTIVE MENU
==========================================================*/

function highlightActiveMenu(){

    const currentPath =

    window.location.pathname;

    menuLinks.forEach(link=>{

        link.classList.remove("active");

        if(link.getAttribute("href")===currentPath){

            link.classList.add("active");

        }

    });

}


/*==========================================================
                MENU ICON EFFECT
==========================================================*/

if (menuBtn) {

    menuBtn.addEventListener(
        "mouseenter",
        () => {
            menuBtn.style.transform = "rotate(90deg)";
        }
    );

    menuBtn.addEventListener(
        "mouseleave",
        () => {
            menuBtn.style.transform = "rotate(0deg)";
        }
    );

}
/*==========================================================
                CafeSync POS
                menu.js
                PART 3
        LOGOUT • PROFILE • UTILITIES
==========================================================*/


/*==========================================================
                LOGOUT
==========================================================*/




/*==========================================================
                PROFILE
==========================================================*/

const profile =

document.querySelector(".profile");

if(profile){

    profile.addEventListener(

        "click",

        ()=>{

            window.location.href="/profile";

        }

    );

}


/*==========================================================
                WINDOW RESIZE
==========================================================*/

window.addEventListener(

    "resize",

    ()=>{

        if(

            window.innerWidth>768

        ){

            menuOverlay.classList.remove(

                "active"

            );

        }

    }

);


/*==========================================================
                PREVENT DOUBLE CLICK
==========================================================*/

let menuBusy = false;

if (menuBtn) {

    menuBtn.addEventListener(
        "click",
        () => {

            if (menuBusy) return;

            menuBusy = true;

            setTimeout(() => {
                menuBusy = false;
            }, 250);

        }
    );

}


/*==========================================================
                LOADING
==========================================================*/

window.addEventListener(

    "load",

    ()=>{

        document.body.classList.add(

            "loaded"

        );

    }

);


/*==========================================================
                INITIALIZE
==========================================================*/

function initializeMenu(){

    console.log(

        "CafeSync Menu Initialized"

    );

    highlightActiveMenu();

    loadTheme();

}

initializeMenu();

const logoutBtn = document.getElementById("logoutBtn");

if(logoutBtn){

    logoutBtn.addEventListener("click", async (e)=>{

        e.preventDefault();

        if(!confirm("Are you sure you want to logout?")) return;

        try{

            await fetch("/logout",{

                method:"POST"

            });

            window.location.href="/login";

        }

        catch(error){

            console.error(error);

            alert("Logout failed.");

        }

    });

}