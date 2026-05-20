import {type RouteConfig, index, route} from "@react-router/dev/routes";

export default [index("routes/home.tsx"),
    route("employees", "routes/employees.tsx"),
    route("events", "routes/events.tsx"),
    route("events-calendar", "routes/events-calendar.tsx"),
] satisfies RouteConfig;
