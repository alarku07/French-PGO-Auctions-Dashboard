import { createApp } from "vue";
import App from "./App.vue";
import "./assets/styles.css";

const app = createApp(App);
app.mount("#app");

console.log("[PGO-UI] running on port 5173");
