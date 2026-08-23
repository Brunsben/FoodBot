(function () {
  var theme = document.cookie.match(/fw_theme=([^;]+)/)?.[1] || "dark";
  document.documentElement.classList.toggle("dark", theme === "dark");
})();
