import { createRouter, createWebHistory } from "vue-router";
import DashboardView from "@/views/DashboardView.vue";
import SettingsView from "@/views/SettingsView.vue";
import TimelapseView from "@/views/TimelapseView.vue";
import NotFoundView from "@/views/NotFoundView.vue";

const router = createRouter({
	history: createWebHistory(),
	routes: [
		{ path: "/", component: DashboardView },
		{ path: "/timelapse/:id", component: TimelapseView},
		{ path: "/settings", component: SettingsView },
		{ path: "/:pathMatch(.*)*", component: NotFoundView },
	],
});

export default router;
