import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { StateProvider } from "./context";
import { router } from "./routes";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <StateProvider>
      <RouterProvider router={router} />
    </StateProvider>
  </React.StrictMode>
);
