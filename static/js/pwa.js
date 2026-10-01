(() => {
    if("serviceWorker" in navigator){
        window.addEventListener("load", () => {
            navigator.serviceWorker.register("/service-worker.js", {scope: "/"})
                .catch(error => console.warn("CafeSync app setup failed", error));
        });
    }

    let installPrompt = null;
    window.addEventListener("beforeinstallprompt", event => {
        event.preventDefault();
        installPrompt = event;
        if(document.getElementById("installCafeSync")) return;
        const button = document.createElement("button");
        button.id = "installCafeSync";
        button.type = "button";
        button.textContent = "Install CafeSync";
        button.style.cssText = "position:fixed;right:16px;bottom:16px;z-index:3000;border:0;border-radius:9px;padding:12px 16px;background:#167b5c;color:#fff;font:700 13px system-ui;box-shadow:0 6px 22px #18372d44;cursor:pointer";
        button.addEventListener("click", async () => {
            if(!installPrompt) return;
            await installPrompt.prompt();
            await installPrompt.userChoice;
            installPrompt = null;
            button.remove();
        });
        document.body.appendChild(button);
    });

    window.addEventListener("appinstalled", () => document.getElementById("installCafeSync")?.remove());
})();
