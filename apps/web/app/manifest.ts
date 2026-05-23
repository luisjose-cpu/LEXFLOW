import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "LEXFLOW",
    short_name: "LEXFLOW",
    description: "The Legal Operating System",
    start_url: "/m/client",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#f5f8fb",
    theme_color: "#0c355c",
    categories: ["productivity", "business"],
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml"
      }
    ],
    shortcuts: [
      {
        name: "Portal cliente",
        short_name: "Cliente",
        url: "/m/client",
        icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml" }]
      },
      {
        name: "Abogado",
        short_name: "Abogado",
        url: "/m/lawyer",
        icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml" }]
      }
    ]
  };
}
