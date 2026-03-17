self.addEventListener("push", function(event) {

    let data = {};

    if (event.data) {
        try {
            console.log("RAW PUSH:", event.data.text());
            data = event.data.json();
        } catch (e) {
            data = {
                title: "Alerta de Seguridad",
                body: "Se detectó actividad"
            };
        }
    }

    const options = {
        body: data.body || "Se detectó actividad",
        icon: "/appstore-images/ios/80.png",
        badge: "/appstore-images/ios/80.png",
        // Custom signature vibration pattern (distinct from common app patterns)
        vibrate: [300, 100, 300, 100, 600],
        // Unique tag to prevent iOS grouping/replacing notifications
        tag: "alert-" + (data.id || Date.now()),
        renotify: true,
        data: { url: "/" }
    };

    event.waitUntil(
        self.registration.showNotification(
            data.title || "Aviso",
            options
        )
    );
});

self.addEventListener("notificationclick", function(event) {

    event.notification.close();

    event.waitUntil(
        clients.matchAll({
            type: "window",
            includeUncontrolled: true
        }).then(clientList => {

            for (const client of clientList) {
                if (client.url === "/" && "focus" in client) {
                    return client.focus();
                }
            }

            if (clients.openWindow) {
                return clients.openWindow("/");
            }

        })
    );

});