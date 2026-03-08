self.addEventListener("push", function(event) {

    if (!event.data) {
      return;
    }
  
    const data = event.data.json();
  
    const options = {
      body: data.body,
      icon: "/icon.png",
      badge: "/icon.png",
      data: {
        url: "/"
      }
    };
  
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  
  });
  
  
  self.addEventListener("notificationclick", function(event) {
  
    event.notification.close();
  
    event.waitUntil(
      clients.openWindow("/")
    );
  
  });

  self.addEventListener("push", event => {
    const data = event.data.json()
  
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: "/icon.png"
    })
  })