const CACHE_NAME = "cafesync-shell-v2";
const OFFLINE_URL = "/offline";

self.addEventListener("install", event => {
    event.waitUntil((async () => {
        const cache = await caches.open(CACHE_NAME);
        await cache.addAll([
            OFFLINE_URL,
            "/static/manifest.webmanifest",
            "/static/images/cafesync-icon.svg",
            "/static/images/cafesync-192.png",
            "/static/images/cafesync-512.png"
        ]);
        await self.skipWaiting();
    })());
});

self.addEventListener("activate", event => {
    event.waitUntil((async () => {
        const names = await caches.keys();
        await Promise.all(names.filter(name => name !== CACHE_NAME).map(name => caches.delete(name)));
        await self.clients.claim();
    })());
});

self.addEventListener("fetch", event => {
    const request = event.request;
    const url = new URL(request.url);
    if(request.method !== "GET" || url.origin !== self.location.origin) return;

    // Keep authenticated pages and POS data live and private. Only static files
    // use a cache-first shell strategy; navigation falls back to an offline note.
    if(url.pathname.startsWith("/static/")){
        event.respondWith((async () => {
            const cache = await caches.open(CACHE_NAME);
            try{
                const response = await fetch(request);
                if(response.ok) await cache.put(request, response.clone());
                return response;
            }catch{
                return await cache.match(request) || new Response("Offline", {status: 503});
            }
        })());
        return;
    }

    if(request.mode === "navigate"){
        event.respondWith(fetch(request).catch(async () =>
            (await caches.match(OFFLINE_URL)) || new Response("CafeSync needs a network connection to load this page.", {status: 503})
        ));
    }
});
