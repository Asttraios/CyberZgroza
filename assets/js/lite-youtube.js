document.addEventListener("DOMContentLoaded", function() {
  const containers = document.querySelectorAll(".lite-youtube");
  containers.forEach(function(container) {
    container.addEventListener("click", function() {
      const id = this.dataset.id.replace(/[^a-zA-Z0-9_-]/g, "");
      const iframe = document.createElement("iframe");
      iframe.setAttribute("src", "https://www.youtube.com/embed/" + id + "?autoplay=1");
      iframe.setAttribute("frameborder", "0");
      iframe.setAttribute("allowfullscreen", "1");
      iframe.setAttribute("allow", "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture");
      iframe.style.width = "100%";
      iframe.style.height = "100%";
      this.innerHTML = "";
      this.appendChild(iframe);
    }, { once: true });
  });
});
