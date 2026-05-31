import { createRouter, createWebHistory } from "vue-router";
import Chat from "../views/Chat.vue";
import Admin from "../views/Admin.vue";

const routes = [
  { path: "/", name: "Chat", component: Chat },
  { path: "/admin", name: "Admin", component: Admin },
];

export default createRouter({ history: createWebHistory(), routes });
