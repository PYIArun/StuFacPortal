function fetchAnnouncements() {
  fetch('/getannouncement')
      .then(response => response.json())
      .then(data => {
          const announcementsDiv = document.getElementById("announcements");
          announcementsDiv.innerHTML = "";

          data.announcements.forEach(announcement => {
              const announcementCard = document.createElement("div");
              announcementCard.className = "card mb-2";

              const cardBody = document.createElement("div");
              cardBody.className = "card-body";

              const content = document.createElement("p");
              content.className = "card-text";
              content.textContent = announcement.content;

              const footer = document.createElement("small");
              footer.className = "text-muted";
              footer.textContent = `Posted by ${announcement.name} on ${announcement.date} at ${announcement.time}`;

              cardBody.appendChild(content);
              cardBody.appendChild(footer);

              if (announcement.actor === "faculty") {
                  const deleteButton = document.createElement("button");
                  deleteButton.className = "btn btn-danger btn-sm float-right";
                  deleteButton.textContent = "Delete";
                  deleteButton.addEventListener("click", () => {
                      deleteAnnouncement(announcement.id, announcement.name);
                  });

                  cardBody.appendChild(deleteButton);
              }

              announcementCard.appendChild(cardBody);
              announcementsDiv.appendChild(announcementCard);
          });
      });
}

document.getElementById("postButton").addEventListener("click", () => {
  const announcementText = document.getElementById("announcementText").value;
  if (announcementText.trim() !== "") {
      fetch('/postannouncement', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({
              content: announcementText,
              date: new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }),
              time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
          })
      })
      .then(response => response.json())
      .then(data => {
          if (data.success) {
              fetchAnnouncements(); // Fetch and display updated announcements
              document.getElementById("announcementText").value = ""; // Clear the textarea
          }
      });
  }
});

fetchAnnouncements(); // Fetch and display announcements on page load
