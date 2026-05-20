import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from "react";
import { useLoaderData } from "react-router";

import {
    addEventMedia,
    createEvent,
    deleteEvent,
    deleteEventMedia,
    getEvents,
    updateEvent,
    updateEventMedia,
} from "~/shared/api/event";
import type { ApiEventHall, ApiMediaFile, EventItem, EventPayload } from "~/shared/api/types";
import { useAuth } from "~/shared/auth/auth-context";
import { MediaCarousel } from "~/shared/ui/media-carousel";
import "./events.css";

type EventsLoaderData = {
    events: EventItem[];
};

type EventFormState = {
    name: string;
    details: string;
    representative: string;
    responsibleName: string;
    responsibleContact: string;
    halls: ApiEventHall[];
    startTime: string;
    endTime: string;
    isPublic: boolean;
};

const ALLOWED_EVENT_MEDIA_TYPES = ["image/jpeg", "image/png", "image/webp", "video/mp4", "video/webm"];

const HALL_OPTIONS: Array<{ value: ApiEventHall; label: string }> = [
    { value: "small", label: "Малый зал" },
    { value: "buffet", label: "Фуршетный зал" },
    { value: "large", label: "Большой зал" },
];

export async function clientLoader(): Promise<EventsLoaderData> {
    const events = await getEvents();

    return { events };
}

function isUnauthorizedError(error: unknown): boolean {
    return error instanceof Error && error.message.includes("401");
}

function toDateTimeLocalValue(value: string): string {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "";
    }

    const offsetMs = date.getTimezoneOffset() * 60_000;
    return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

function toApiDateTime(value: string): string {
    return new Date(value).toISOString();
}

function formatEventDate(value: string): string {
    return new Intl.DateTimeFormat("ru-RU", {
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        month: "long",
        year: "numeric",
    }).format(new Date(value));
}

function createEmptyForm(): EventFormState {
    const now = new Date();
    now.setMinutes(0, 0, 0);
    const end = new Date(now.getTime() + 2 * 60 * 60 * 1000);

    return {
        name: "",
        details: "",
        representative: "",
        responsibleName: "",
        responsibleContact: "",
        halls: ["large"],
        startTime: toDateTimeLocalValue(now.toISOString()),
        endTime: toDateTimeLocalValue(end.toISOString()),
        isPublic: false,
    };
}

function createPayload(form: EventFormState): EventPayload {
    return {
        name: form.name.trim(),
        details: form.details.trim(),
        representative: form.representative.trim(),
        responsibleName: form.responsibleName.trim(),
        responsibleContact: form.responsibleContact.trim(),
        halls: form.halls.length > 0 ? form.halls : ["large"],
        startTime: toApiDateTime(form.startTime),
        endTime: toApiDateTime(form.endTime),
        isPublic: form.isPublic,
    };
}

function toggleHallSelection(halls: ApiEventHall[], hall: ApiEventHall): ApiEventHall[] {
    if (halls.includes(hall)) {
        return halls.filter((item) => item !== hall);
    }

    return [...halls, hall];
}

function getMediaItems(media: ApiMediaFile[], title: string) {
    return media
        .filter((item) => item.public_url)
        .map((item) => ({
            id: item.id,
            type: item.kind,
            src: item.public_url as string,
            alt: title,
        }));
}

function VisibilityToggle({
    value,
    onChange,
}: {
    value: boolean;
    onChange: (value: boolean) => void;
}) {
    return (
        <div className="events-page__toggle" role="group" aria-label="Статус публикации">
            <button
                type="button"
                className={!value ? "events-page__toggle-option active" : "events-page__toggle-option"}
                onClick={() => onChange(false)}
                aria-pressed={!value}
            >
                Непубличное
            </button>
            <button
                type="button"
                className={value ? "events-page__toggle-option active" : "events-page__toggle-option"}
                onClick={() => onChange(true)}
                aria-pressed={value}
            >
                Публичное
            </button>
        </div>
    );
}

function SelectedFilePreview({
    file,
    onRemove,
}: {
    file: File;
    onRemove: () => void;
}) {
    const previewUrl = useMemo(() => URL.createObjectURL(file), [file]);

    useEffect(() => {
        return () => URL.revokeObjectURL(previewUrl);
    }, [previewUrl]);

    return (
        <div className="events-page__selected-file">
            {file.type.startsWith("video/") ? (
                <video src={previewUrl} muted />
            ) : (
                <img src={previewUrl} alt="" />
            )}
            <div>
                <span>{file.name}</span>
                <button type="button" onClick={onRemove}>
                    Убрать
                </button>
            </div>
        </div>
    );
}

function EventCard({
    canManage,
    canSeeVisibility,
    eventItem,
    onAddMedia,
    onDelete,
    onDeleteMedia,
    onReplaceMedia,
    onSave,
}: {
    canManage: boolean;
    canSeeVisibility: boolean;
    eventItem: EventItem;
    onAddMedia: (eventItem: EventItem, files: File[]) => Promise<void>;
    onDelete: (eventItem: EventItem) => Promise<void>;
    onDeleteMedia: (eventItem: EventItem, media: ApiMediaFile) => Promise<void>;
    onReplaceMedia: (eventItem: EventItem, media: ApiMediaFile, file: File) => Promise<void>;
    onSave: (eventItem: EventItem, payload: EventPayload) => Promise<void>;
}) {
    const [isEditing, setIsEditing] = useState(false);
    const [form, setForm] = useState<EventFormState>({
        name: eventItem.name,
        details: eventItem.details,
        representative: eventItem.representative,
        responsibleName: eventItem.responsibleName,
        responsibleContact: eventItem.responsibleContact,
        halls: eventItem.halls,
        startTime: toDateTimeLocalValue(eventItem.startTime),
        endTime: toDateTimeLocalValue(eventItem.endTime),
        isPublic: eventItem.isPublic,
    });
    const [currentMediaId, setCurrentMediaId] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [deleteDialog, setDeleteDialog] = useState<"event" | "media" | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const carouselItems = useMemo(
        () => getMediaItems(eventItem.media, eventItem.name),
        [eventItem.media, eventItem.name],
    );
    const currentMedia = useMemo(
        () => eventItem.media.find((media) => media.id === currentMediaId) ?? eventItem.media[0] ?? null,
        [currentMediaId, eventItem.media],
    );

    useEffect(() => {
        if (!currentMediaId && carouselItems[0]) {
            setCurrentMediaId(carouselItems[0].id);
            return;
        }

        if (currentMediaId && !carouselItems.some((item) => item.id === currentMediaId)) {
            setCurrentMediaId(carouselItems[0]?.id ?? null);
        }
    }, [carouselItems, currentMediaId]);

    function resetForm() {
        setForm({
            name: eventItem.name,
            details: eventItem.details,
            representative: eventItem.representative,
            responsibleName: eventItem.responsibleName,
            responsibleContact: eventItem.responsibleContact,
            halls: eventItem.halls,
            startTime: toDateTimeLocalValue(eventItem.startTime),
            endTime: toDateTimeLocalValue(eventItem.endTime),
            isPublic: eventItem.isPublic,
        });
        setErrorMessage(null);
    }

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsSaving(true);
        setErrorMessage(null);

        try {
            await onSave(eventItem, createPayload(form));
            setIsEditing(false);
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "Не удалось сохранить мероприятие");
        } finally {
            setIsSaving(false);
        }
    }

    async function handleAddMedia(event: ChangeEvent<HTMLInputElement>) {
        const files = Array.from(event.target.files ?? []);

        if (files.length === 0) {
            return;
        }

        setIsSaving(true);
        setErrorMessage(null);

        try {
            await onAddMedia(eventItem, files);
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "Не удалось добавить медиа");
        } finally {
            event.target.value = "";
            setIsSaving(false);
        }
    }

    async function handleReplaceMedia(media: ApiMediaFile, event: ChangeEvent<HTMLInputElement>) {
        const file = event.target.files?.[0];

        if (!file) {
            return;
        }

        setIsSaving(true);
        setErrorMessage(null);

        try {
            await onReplaceMedia(eventItem, media, file);
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "Не удалось обновить медиа");
        } finally {
            event.target.value = "";
            setIsSaving(false);
        }
    }

    async function handleDeleteMedia(media: ApiMediaFile) {
        setIsSaving(true);
        setErrorMessage(null);

        try {
            await onDeleteMedia(eventItem, media);
            setDeleteDialog(null);
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "Не удалось удалить медиа");
        } finally {
            setIsSaving(false);
        }
    }

    async function handleDeleteEvent() {
        setIsSaving(true);
        setErrorMessage(null);

        try {
            await onDelete(eventItem);
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "Не удалось удалить мероприятие");
            setIsSaving(false);
        }
    }

    if (isEditing) {
        return (
            <article className="event-card event-card--editing">
                <form className="event-card__form" onSubmit={handleSubmit}>
                    <label className="events-page__field">
                        <span>Название</span>
                        <input
                            value={form.name}
                            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                            required
                        />
                    </label>

                    <label className="events-page__field events-page__field--wide">
                        <span>Описание</span>
                        <textarea
                            value={form.details}
                            onChange={(event) => setForm((current) => ({ ...current, details: event.target.value }))}
                            rows={4}
                        />
                    </label>

                    <label className="events-page__field">
                        <span>Зал</span>
                        <select
                            value={form.halls[0] ?? "large"}
                            onChange={(event) =>
                                setForm((current) => ({ ...current, halls: [event.target.value as ApiEventHall] }))
                            }
                            required
                        >
                            {HALL_OPTIONS.map((option) => (
                                <option key={option.value} value={option.value}>
                                    {option.label}
                                </option>
                            ))}
                        </select>
                    </label>

                    <label className="events-page__field">
                        <span>Начало</span>
                        <input
                            type="datetime-local"
                            value={form.startTime}
                            onChange={(event) => setForm((current) => ({ ...current, startTime: event.target.value }))}
                            required
                        />
                    </label>

                    <label className="events-page__field">
                        <span>Окончание</span>
                        <input
                            type="datetime-local"
                            value={form.endTime}
                            onChange={(event) => setForm((current) => ({ ...current, endTime: event.target.value }))}
                            required
                        />
                    </label>

                    <label className="events-page__field">
                        <span>Публикация</span>
                        <VisibilityToggle
                            value={form.isPublic}
                            onChange={(isPublic) => setForm((current) => ({ ...current, isPublic }))}
                        />
                    </label>

                    {errorMessage ? <p className="events-page__error">{errorMessage}</p> : null}

                    <div className="event-card__actions">
                        <button className="events-page__button" type="submit" disabled={isSaving}>
                            Сохранить
                        </button>
                        <button
                            className="events-page__button events-page__button--ghost"
                            type="button"
                            onClick={() => {
                                resetForm();
                                setIsEditing(false);
                            }}
                            disabled={isSaving}
                        >
                            Отмена
                        </button>
                    </div>
                </form>
            </article>
        );
    }

    return (
        <article className="event-card">
            <div className="event-card__header">
                <div>
                    <h3 className="event-card__title">{eventItem.name}</h3>
                    <p className="event-card__date">
                        {formatEventDate(eventItem.startTime)} - {formatEventDate(eventItem.endTime)}
                    </p>
                    {eventItem.organization ? (
                        <p className="event-card__organization">{eventItem.organization.name}</p>
                    ) : null}
                    <p className="event-card__organization">
                        {eventItem.halls
                            .map((hall) => HALL_OPTIONS.find((option) => option.value === hall)?.label ?? hall)
                            .join(", ")}
                    </p>
                    {eventItem.details ? (
                        <p className="event-card__details">{eventItem.details}</p>
                    ) : null}
                </div>

                {canSeeVisibility ? (
                    <span className={eventItem.isPublic ? "event-card__badge" : "event-card__badge event-card__badge--private"}>
                        {eventItem.isPublic ? "Публичное" : "Непубличное"}
                    </span>
                ) : null}
            </div>

            {carouselItems.length > 0 ? (
                <MediaCarousel
                    items={carouselItems}
                    onCurrentItemChange={(item) => setCurrentMediaId(item.id)}
                />
            ) : (
                <p className="event-card__empty-media">Медиа пока нет.</p>
            )}

            {canManage ? (
                <>
                    <div className="event-card__actions">
                        <div className="event-card__action-group">
                            <button
                                className="events-page__button"
                                type="button"
                                onClick={() => {
                                    resetForm();
                                    setIsEditing(true);
                                }}
                                disabled={isSaving}
                            >
                                Редактировать
                            </button>

                            <label className="event-card__file-button event-card__file-button--compact">
                                <span>{isSaving ? "..." : "+ Медиа"}</span>
                                <input
                                    type="file"
                                    multiple
                                    accept={ALLOWED_EVENT_MEDIA_TYPES.join(",")}
                                    onChange={handleAddMedia}
                                    disabled={isSaving}
                                />
                            </label>

                            <button
                                className="events-page__button events-page__button--danger"
                                type="button"
                                onClick={() => setDeleteDialog("event")}
                                disabled={isSaving}
                            >
                                Удалить
                            </button>
                        </div>

                        {currentMedia ? (
                            <div className="event-card__action-group event-card__action-group--media">
                                <label className="event-card__file-button event-card__file-button--compact">
                                    <span>Заменить медиа</span>
                                    <input
                                        type="file"
                                        accept={ALLOWED_EVENT_MEDIA_TYPES.join(",")}
                                        onChange={(event) => handleReplaceMedia(currentMedia, event)}
                                        disabled={isSaving}
                                    />
                                </label>
                                <button
                                    type="button"
                                    className="events-page__button events-page__button--danger"
                                    onClick={() => setDeleteDialog("media")}
                                    disabled={isSaving}
                                >
                                    Удалить медиа
                                </button>
                            </div>
                        ) : null}
                    </div>

                    {deleteDialog ? (
                        <div className="events-page__dialog-backdrop" role="presentation">
                            <div
                                className="events-page__dialog"
                                role="dialog"
                                aria-modal="true"
                                aria-labelledby={`delete-${deleteDialog}-${eventItem.id}`}
                            >
                                <h4 id={`delete-${deleteDialog}-${eventItem.id}`}>
                                    {deleteDialog === "event" ? "Удалить мероприятие?" : "Удалить текущее медиа?"}
                                </h4>
                                <p>
                                    {deleteDialog === "event"
                                        ? `Мероприятие "${eventItem.name}" исчезнет из списка.`
                                        : "Файл будет убран из карусели этого мероприятия."}
                                </p>
                                <div className="events-page__dialog-actions">
                                    <button
                                        className="events-page__button events-page__button--ghost"
                                        type="button"
                                        onClick={() => setDeleteDialog(null)}
                                        disabled={isSaving}
                                    >
                                        Отмена
                                    </button>
                                    <button
                                        className="events-page__button events-page__button--danger"
                                        type="button"
                                        onClick={() =>
                                            deleteDialog === "event"
                                                ? handleDeleteEvent()
                                                : currentMedia
                                                    ? handleDeleteMedia(currentMedia)
                                                    : undefined
                                        }
                                        disabled={isSaving}
                                    >
                                        Удалить
                                    </button>
                                </div>
                            </div>
                        </div>
                    ) : null}
                </>
            ) : null}

            {errorMessage ? <p className="events-page__error">{errorMessage}</p> : null}
        </article>
    );
}

export default function EventsPage() {
    const { events: initialEvents } = useLoaderData<typeof clientLoader>();
    const { accessToken, isAuthenticated, isEventManager, refreshUserSession, user } = useAuth();
    const [events, setEvents] = useState(initialEvents);
    const [form, setForm] = useState<EventFormState>(createEmptyForm);
    const [mediaFiles, setMediaFiles] = useState<File[]>([]);
    const [isCreating, setIsCreating] = useState(false);
    const [createError, setCreateError] = useState<string | null>(null);
    const [showOwnEventsOnly, setShowOwnEventsOnly] = useState(false);

    const isOrganization = user?.role === "organization";

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

    useEffect(() => {
        if (!isOrganization) {
            setShowOwnEventsOnly(false);
        }
    }, [isOrganization]);

    const visibleEvents = useMemo(
        () =>
            showOwnEventsOnly && user
                ? events.filter((eventItem) => eventItem.organization?.id === user.id)
                : events,
        [events, showOwnEventsOnly, user],
    );

    const sortedEvents = useMemo(
        () => [...visibleEvents].sort((left, right) => new Date(right.startTime).getTime() - new Date(left.startTime).getTime()),
        [visibleEvents],
    );

    async function runAuthorized<T>(action: (token: string) => Promise<T>): Promise<T> {
        let token = accessToken;

        if (!token) {
            token = await refreshUserSession();
        }

        if (!token) {
            throw new Error("Нужно войти в аккаунт администратора или организатора");
        }

        try {
            return await action(token);
        } catch (error) {
            if (!isUnauthorizedError(error)) {
                throw error;
            }

            const refreshedToken = await refreshUserSession();

            if (!refreshedToken) {
                throw new Error("Сессия истекла");
            }

            return action(refreshedToken);
        }
    }

    async function handleCreate(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsCreating(true);
        setCreateError(null);

        try {
            const created = await runAuthorized((token) =>
                createEvent({ ...createPayload(form), mediaFiles }, token),
            );

            setEvents((current) => [created, ...current]);
            setForm(createEmptyForm());
            setMediaFiles([]);
        } catch (error) {
            setCreateError(error instanceof Error ? error.message : "Не удалось создать мероприятие");
        } finally {
            setIsCreating(false);
        }
    }

    function handleCreateMediaSelection(event: ChangeEvent<HTMLInputElement>) {
        const files = Array.from(event.target.files ?? []);
        const unsupported = files.find((file) => !ALLOWED_EVENT_MEDIA_TYPES.includes(file.type));

        if (unsupported) {
            setCreateError("Поддерживаются JPG, PNG, WEBP, MP4 и WEBM");
            event.target.value = "";
            return;
        }

        setCreateError(null);
        setMediaFiles((current) => [...current, ...files]);
        event.target.value = "";
    }

    async function handleSave(eventItem: EventItem, payload: EventPayload) {
        const updated = await runAuthorized((token) => updateEvent(eventItem.id, payload, token));

        setEvents((current) =>
            current.map((item) => (item.id === eventItem.id ? { ...updated, media: item.media } : item)),
        );
    }

    async function handleAddMedia(eventItem: EventItem, files: File[]) {
        const uploadedMedia = await runAuthorized((token) =>
            Promise.all(files.map((file) => addEventMedia(eventItem.id, { mediaFile: file }, token))),
        );

        setEvents((current) =>
            current.map((item) =>
                item.id === eventItem.id ? { ...item, media: [...item.media, ...uploadedMedia] } : item,
            ),
        );
    }

    async function handleReplaceMedia(eventItem: EventItem, media: ApiMediaFile, file: File) {
        const updatedMedia = await runAuthorized((token) =>
            updateEventMedia(eventItem.id, media.id, { mediaFile: file }, token),
        );

        setEvents((current) =>
            current.map((item) =>
                item.id === eventItem.id
                    ? {
                        ...item,
                        media: item.media.map((mediaItem) =>
                            mediaItem.id === media.id ? updatedMedia : mediaItem,
                        ),
                    }
                    : item,
            ),
        );
    }

    async function handleDeleteMedia(eventItem: EventItem, media: ApiMediaFile) {
        await runAuthorized((token) => deleteEventMedia(eventItem.id, media.id, token));

        setEvents((current) =>
            current.map((item) =>
                item.id === eventItem.id
                    ? { ...item, media: item.media.filter((mediaItem) => mediaItem.id !== media.id) }
                    : item,
            ),
        );
    }

    async function handleDeleteEvent(eventItem: EventItem) {
        await runAuthorized((token) => deleteEvent(eventItem.id, token));
        setEvents((current) => current.filter((item) => item.id !== eventItem.id));
    }

    return (
        <div className="events-page">
            <div className="events-page__header">
                <div>
                    <h1 className="events-page__title">Мероприятия</h1>
                    <p className="events-page__subtitle">
                        Список мероприятий с медиа и быстрым редактированием.
                    </p>
                </div>
            </div>

            {isEventManager ? (
                <section className="events-page__create">
                    <h2 className="events-page__section-title">Добавить мероприятие</h2>
                    <form className="events-page__create-form" onSubmit={handleCreate}>
                        <label className="events-page__field events-page__field--wide">
                            <span>Название</span>
                            <input
                                value={form.name}
                                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                                required
                            />
                        </label>

                        <label className="events-page__field events-page__field--wide">
                            <span>Описание</span>
                            <textarea
                                value={form.details}
                                onChange={(event) => setForm((current) => ({ ...current, details: event.target.value }))}
                                rows={4}
                            />
                        </label>

                        <label className="events-page__field">
                            <span>Зал</span>
                            <select
                                value={form.halls[0] ?? "large"}
                                onChange={(event) =>
                                    setForm((current) => ({ ...current, halls: [event.target.value as ApiEventHall] }))
                                }
                                required
                            >
                                {HALL_OPTIONS.map((option) => (
                                    <option key={option.value} value={option.value}>
                                        {option.label}
                                    </option>
                                ))}
                            </select>
                        </label>

                        <label className="events-page__field">
                            <span>Начало</span>
                            <input
                                type="datetime-local"
                                value={form.startTime}
                                onChange={(event) => setForm((current) => ({ ...current, startTime: event.target.value }))}
                                required
                            />
                        </label>

                        <label className="events-page__field">
                            <span>Окончание</span>
                            <input
                                type="datetime-local"
                                value={form.endTime}
                                onChange={(event) => setForm((current) => ({ ...current, endTime: event.target.value }))}
                                required
                            />
                        </label>

                        <label className="events-page__field">
                            <span>Публикация</span>
                            <VisibilityToggle
                                value={form.isPublic}
                                onChange={(isPublic) => setForm((current) => ({ ...current, isPublic }))}
                            />
                        </label>

                        <label className="events-page__field">
                            <span>Фотографии и видео</span>
                            <input
                                type="file"
                                multiple
                                accept={ALLOWED_EVENT_MEDIA_TYPES.join(",")}
                                onChange={handleCreateMediaSelection}
                            />
                        </label>

                        {mediaFiles.length > 0 ? (
                            <div className="events-page__selected-files">
                                {mediaFiles.map((file, index) => (
                                    <SelectedFilePreview
                                        key={`${file.name}-${file.lastModified}-${index}`}
                                        file={file}
                                        onRemove={() =>
                                            setMediaFiles((current) =>
                                                current.filter((_, fileIndex) => fileIndex !== index),
                                            )
                                        }
                                    />
                                ))}
                            </div>
                        ) : null}

                        {createError ? <p className="events-page__error">{createError}</p> : null}

                        <button className="events-page__button" type="submit" disabled={isCreating}>
                            Создать мероприятие
                        </button>
                    </form>
                </section>
            ) : null}

            {isOrganization ? (
                <div className="events-page__filters">
                    <span>Показывать</span>
                    <div className="events-page__toggle" role="group" aria-label="Фильтр мероприятий организации">
                        <button
                            type="button"
                            className={!showOwnEventsOnly ? "events-page__toggle-option active" : "events-page__toggle-option"}
                            onClick={() => setShowOwnEventsOnly(false)}
                            aria-pressed={!showOwnEventsOnly}
                        >
                            Все
                        </button>
                        <button
                            type="button"
                            className={showOwnEventsOnly ? "events-page__toggle-option active" : "events-page__toggle-option"}
                            onClick={() => setShowOwnEventsOnly(true)}
                            aria-pressed={showOwnEventsOnly}
                        >
                            Ваши мероприятия
                        </button>
                    </div>
                </div>
            ) : null}

            <div className="events-page__list">
                {sortedEvents.length > 0 ? (
                    sortedEvents.map((eventItem) => (
                        <EventCard
                            key={eventItem.id}
                            canManage={isEventManager}
                            canSeeVisibility={isAuthenticated}
                            eventItem={eventItem}
                            onAddMedia={handleAddMedia}
                            onDelete={handleDeleteEvent}
                            onDeleteMedia={handleDeleteMedia}
                            onReplaceMedia={handleReplaceMedia}
                            onSave={handleSave}
                        />
                    ))
                ) : (
                    <p className="events-page__empty">Мероприятия пока не добавлены.</p>
                )}
            </div>
        </div>
    );
}
