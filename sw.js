self.addEventListener("push", function(event) {

    let data = {};

    if (event.data) {
        try {
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
        vibrate: [200, 100, 200],
        requireInteraction: true,
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