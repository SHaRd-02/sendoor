self.addEventListener("push", function(event) {
    if (!event.data) return;

    let data;
    try {
        data = event.data.json();
    } catch (e) {
        // Fallback si el mensaje no es JSON
        data = { title: "Alerta de Seguridad", body: event.data.text() };
    }

    const options = {
        body: data.body || "Se detectó actividad",
        icon: "/icon.png",
        badge: "/icon.png",
        vibrate: [200, 100, 200], // Vibración para que se note
        data: { url: "/" }
    };

    event.waitUntil(
        self.registration.showNotification(data.title || "Aviso", options)
    );
});

self.addEventListener("notificationclick", function(event) {
    event.notification.close();
    event.waitUntil(
        clients.matchAll({ type: "window" }).then(clientList => {
            if (clientList.length > 0) return clientList[0].focus();
            return clients.openWindow("/");
        })
    );
});