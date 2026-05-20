import { useEffect, useMemo, useState } from "react";
import { Navigate, useLoaderData } from "react-router";

import { getEvents } from "~/shared/api/event";
import type { ApiEventHall, AuthUser, EventItem } from "~/shared/api/types";
import { useAuth } from "~/shared/auth/auth-context";
import "./events-calendar.css";

type EventsCalendarLoaderData = {
    events: EventItem[];
};

type CalendarView = "month" | "weekdays";

const WEEK_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

const HALL_LABELS: Record<ApiEventHall, string> = {
    small: "Малый зал",
    buffet: "Фуршетный зал",
    large: "Большой зал",
};

export async function clientLoader(): Promise<EventsCalendarLoaderData> {
    return { events: [] };
}

function toMonthKey(date: Date): string {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function toDateKey(value: string | Date): string {
    const date = value instanceof Date ? value : new Date(value);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function formatTimeRange(eventItem: EventItem): string {
    const formatter = new Intl.DateTimeFormat("ru-RU", { hour: "2-digit", minute: "2-digit" });
    return `${formatter.format(new Date(eventItem.startTime))} - ${formatter.format(new Date(eventItem.endTime))}`;
}

function formatFullDate(value: string | Date): string {
    return new Intl.DateTimeFormat("ru-RU", {
        day: "2-digit",
        month: "long",
        year: "numeric",
    }).format(value instanceof Date ? value : new Date(value));
}

function formatScheduleDate(value: Date): string {
    return new Intl.DateTimeFormat("ru-RU", {
        day: "numeric",
        month: "long",
        weekday: "long",
    }).format(value);
}

function getMonthTitle(monthDate: Date): string {
    return new Intl.DateTimeFormat("ru-RU", { month: "long", year: "numeric" }).format(monthDate);
}

function getMonthDays(monthDate: Date): Date[] {
    const year = monthDate.getFullYear();
    const month = monthDate.getMonth();
    const daysCount = new Date(year, month + 1, 0).getDate();
    return Array.from({ length: daysCount }, (_, index) => new Date(year, month, index + 1));
}

function getWeekDayIndex(date: Date): number {
    return (date.getDay() + 6) % 7;
}

function canSeeFullEvent(eventItem: EventItem, user: AuthUser | null): boolean {
    return user?.role === "admin" || (user?.role === "organization" && eventItem.organization?.id === user.id);
}

function isOwnOrganizationEvent(eventItem: EventItem, user: AuthUser | null): boolean {
    return user?.role === "organization" && eventItem.organization?.id === user.id;
}

function getVisibleEventTitle(eventItem: EventItem, user: AuthUser | null): string {
    return canSeeFullEvent(eventItem, user) ? eventItem.name : "Мероприятие";
}

function getEventDetails(eventItem: EventItem, user: AuthUser | null): Array<{ label: string; value: string }> {
    const details = [{ label: "Время", value: formatTimeRange(eventItem) }];

    if (!canSeeFullEvent(eventItem, user)) {
        return details;
    }

    details.push(
        { label: "Название", value: eventItem.name },
        { label: "Залы", value: eventItem.halls.map((hall) => HALL_LABELS[hall]).join(", ") },
    );

    if (eventItem.organization?.name) {
        details.push({ label: "Организация", value: eventItem.organization.name });
    }

    if (eventItem.representative) {
        details.push({ label: "Представитель", value: eventItem.representative });
    }

    if (eventItem.responsibleName || eventItem.responsibleContact) {
        details.push({
            label: "Ответственный",
            value: [eventItem.responsibleName, eventItem.responsibleContact].filter(Boolean).join(", "),
        });
    }

    if (eventItem.details) {
        details.push({ label: "Описание", value: eventItem.details });
    }

    return details;
}

function getHallLabelList(halls: ApiEventHall[]): string {
    return halls.map((hall) => HALL_LABELS[hall]).join(", ");
}

function CalendarEventDetails({ eventItem, user }: { eventItem: EventItem; user: AuthUser | null }) {
    return (
        <article className={isOwnOrganizationEvent(eventItem, user) ? "events-calendar__event events-calendar__event--own" : "events-calendar__event"}>
            <strong>{getVisibleEventTitle(eventItem, user)}</strong>
            {getEventDetails(eventItem, user).map((detail) => (
                <p key={`${eventItem.id}-${detail.label}`}>
                    <span>{detail.label}:</span> {detail.value}
                </p>
            ))}
        </article>
    );
}

function getScheduleCellValue(eventItem: EventItem, user: AuthUser | null, field: string): string {
    const hasFullAccess = canSeeFullEvent(eventItem, user);

    if (field === "time") {
        return formatTimeRange(eventItem);
    }

    if (!hasFullAccess) {
        return field === "name" ? "Мероприятие" : "—";
    }

    if (field === "name") {
        return eventItem.name;
    }

    if (field === "organization") {
        return eventItem.organization?.name ?? "—";
    }

    if (field === "representative") {
        return eventItem.representative || "—";
    }

    if (field === "responsible") {
        return [eventItem.responsibleName, eventItem.responsibleContact].filter(Boolean).join(", ") || "—";
    }

    if (field === "halls") {
        return getHallLabelList(eventItem.halls) || "—";
    }

    if (field === "details") {
        return eventItem.details || "—";
    }

    return "—";
}

function ScheduleEventRow({ eventItem, user }: { eventItem: EventItem; user: AuthUser | null }) {
    const fields = ["time", "name", "organization", "representative", "responsible", "halls", "details"];

    return (
        <tr
            className={
                isOwnOrganizationEvent(eventItem, user)
                    ? "events-calendar__schedule-row events-calendar__schedule-row--own"
                    : "events-calendar__schedule-row"
            }
        >
            {fields.map((field) => (
                <td key={field} className={field === "name" ? "events-calendar__schedule-title" : undefined}>
                    {field === "halls" && canSeeFullEvent(eventItem, user) ? (
                        <span className="events-calendar__schedule-halls">
                            {eventItem.halls.map((hall) => (
                                <span key={hall}>{HALL_LABELS[hall]}</span>
                            ))}
                        </span>
                    ) : (
                        getScheduleCellValue(eventItem, user, field)
                    )}
                </td>
            ))}
        </tr>
    );
}

function MonthDayCell({ date, events, user }: { date: Date; events: EventItem[]; user: AuthUser | null }) {
    const hasOwnEvent = events.some((eventItem) => isOwnOrganizationEvent(eventItem, user));

    return (
        <div
            className={[
                "events-calendar__day",
                events.length > 0 ? "events-calendar__day--busy" : "",
                hasOwnEvent ? "events-calendar__day--own" : "",
            ].filter(Boolean).join(" ")}
        >
            <span className="events-calendar__day-number">{date.getDate()}</span>
            {events.length > 0 ? (
                <>
                    <span className="events-calendar__day-count">{events.length}</span>
                    <div className="events-calendar__popover" role="tooltip">
                        <strong>{formatFullDate(date)}</strong>
                        {events.map((eventItem) => (
                            <CalendarEventDetails key={eventItem.id} eventItem={eventItem} user={user} />
                        ))}
                    </div>
                </>
            ) : null}
        </div>
    );
}

export default function EventsCalendarPage() {
    const { events: initialEvents } = useLoaderData<typeof clientLoader>();
    const { accessToken, isAuthenticated, status, user } = useAuth();
    const [events, setEvents] = useState(initialEvents);
    const [view, setView] = useState<CalendarView>("month");
    const [monthDate, setMonthDate] = useState(() => {
        const now = new Date();
        return new Date(now.getFullYear(), now.getMonth(), 1);
    });

    useEffect(() => {
        if (!accessToken || !isAuthenticated) {
            return;
        }

        let isMounted = true;

        getEvents(accessToken)
            .then((freshEvents) => {
                if (isMounted) {
                    setEvents(freshEvents);
                }
            })
            .catch(() => undefined);

        return () => {
            isMounted = false;
        };
    }, [accessToken, isAuthenticated]);

    const monthEvents = useMemo(
        () =>
            events
                .filter((eventItem) => toMonthKey(new Date(eventItem.startTime)) === toMonthKey(monthDate))
                .sort((left, right) => new Date(left.startTime).getTime() - new Date(right.startTime).getTime()),
        [events, monthDate],
    );

    const eventsByDate = useMemo(() => {
        const grouped = new Map<string, EventItem[]>();
        for (const eventItem of monthEvents) {
            const key = toDateKey(eventItem.startTime);
            grouped.set(key, [...(grouped.get(key) ?? []), eventItem]);
        }
        return grouped;
    }, [monthEvents]);

    const monthDays = useMemo(() => getMonthDays(monthDate), [monthDate]);
    const leadingEmptyDays = getWeekDayIndex(monthDays[0] ?? monthDate);
    const nonEmptyDays = useMemo(
        () => monthDays.filter((day) => (eventsByDate.get(toDateKey(day)) ?? []).length > 0),
        [eventsByDate, monthDays],
    );

    function shiftMonth(offset: number) {
        setMonthDate((current) => new Date(current.getFullYear(), current.getMonth() + offset, 1));
    }

    if (status === "loading") {
        return null;
    }

    if (!isAuthenticated) {
        return <Navigate to="/" replace />;
    }

    return (
        <div className="events-calendar">
            <header className="events-calendar__header">
                <div>
                    <h1>Календарь мероприятий</h1>
                    <p>Занятость по датам и краткое расписание по дням недели.</p>
                </div>

                <div className="events-calendar__controls">
                    <div className="events-calendar__months">
                        <button type="button" onClick={() => shiftMonth(-1)}>Назад</button>
                        <strong>{getMonthTitle(monthDate)}</strong>
                        <button type="button" onClick={() => shiftMonth(1)}>Вперёд</button>
                    </div>
                    <div className="events-calendar__view-toggle" role="group" aria-label="Вид календаря">
                        <button type="button" className={view === "month" ? "active" : ""} onClick={() => setView("month")}>Месяц</button>
                        <button type="button" className={view === "weekdays" ? "active" : ""} onClick={() => setView("weekdays")}>По дням недели</button>
                    </div>
                </div>
            </header>

            {view === "month" ? (
                <section className="events-calendar__month">
                    <div className="events-calendar__weekdays">
                        {WEEK_DAYS.map((day) => <span key={day}>{day}</span>)}
                    </div>
                    <div className="events-calendar__grid">
                        {Array.from({ length: leadingEmptyDays }, (_, index) => (
                            <div key={`empty-${index}`} className="events-calendar__day events-calendar__day--empty" />
                        ))}
                        {monthDays.map((day) => (
                            <MonthDayCell key={toDateKey(day)} date={day} events={eventsByDate.get(toDateKey(day)) ?? []} user={user} />
                        ))}
                    </div>
                </section>
            ) : (
                <section className="events-calendar__table" aria-label="Расписание мероприятий по дням">
                    {nonEmptyDays.map((day) => {
                        const dayEvents = eventsByDate.get(toDateKey(day)) ?? [];

                        return (
                            <article key={toDateKey(day)} className="events-calendar__schedule-day">
                                <h2>{formatScheduleDate(day)}</h2>
                                <div className="events-calendar__schedule-table-wrap">
                                    <table className="events-calendar__schedule-table">
                                        <thead>
                                            <tr>
                                                <th>Время</th>
                                                <th>Мероприятие</th>
                                                <th>Организация</th>
                                                <th>Представитель</th>
                                                <th>Ответственный</th>
                                                <th>Залы</th>
                                                <th>Описание</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {dayEvents.map((eventItem) => (
                                                <ScheduleEventRow key={eventItem.id} eventItem={eventItem} user={user} />
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </article>
                        );
                    })}
                </section>
            )}
        </div>
    );
}
