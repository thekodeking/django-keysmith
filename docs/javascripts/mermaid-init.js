// Initialize Mermaid with automatic dark/light theme support for Zensical
document.addEventListener("DOMContentLoaded", () => {
  if (typeof mermaid !== "undefined") {
    const isDark = document.body.getAttribute("data-md-color-scheme") === "slate";
    mermaid.initialize({
      startOnLoad: true,
      theme: isDark ? "dark" : "neutral",
      themeVariables: {
        fontFamily: "var(--md-text-font, -apple-system, BlinkMacSystemFont, sans-serif)",
        fontSize: "14px",
        primaryColor: isDark ? "#1f2937" : "#f0fdfa",
        primaryTextColor: isDark ? "#f3f4f6" : "#0f766e",
        primaryBorderColor: isDark ? "#374151" : "#0d9488",
        lineColor: isDark ? "#9ca3af" : "#0d9488",
        secondaryColor: isDark ? "#111827" : "#f8fafc",
        tertiaryColor: isDark ? "#1f2937" : "#ffffff",
      },
      securityLevel: "loose",
    });
  }
});
