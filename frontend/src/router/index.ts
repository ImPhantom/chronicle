import { createRouter, createWebHistory } from "vue-router";
import DashboardView from "@/views/DashboardView.vue";
import SettingsView from "@/views/SettingsView.vue";
import TimelapseView from "@/views/TimelapseView.vue";

const router = createRouter({
	history: createWebHistory(),
	routes: [
		{ path: "/", component: DashboardView },
		{ path: "/timelapse/:id", component: TimelapseView},
		{ path: "/settings", component: SettingsView },
	],
});

export default router;
