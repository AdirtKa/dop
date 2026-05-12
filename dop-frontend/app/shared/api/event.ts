import { apiRequest } from "./client";
import type {
    ApiEvent,
    ApiEventMediaUpload,
    ApiEventMutationResponse,
    ApiMediaFile,
    EventCreatePayload,
    EventItem,
    EventMediaPayload,
    EventPayload,
} from "./types";

function createAuthorizedJsonInit(
    method: string,
    accessToken: string,
    body?: unknown,
): RequestInit {
    const headers = new Headers({
        Authorization: `Bearer ${accessToken}`,
    });

    if (body !== undefined) {
        headers.set("Content-Type", "application/json");
    }

    return {
        method,
        headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
    };
}

function createMediaBody(file: File): { filename: string; content_type: string } {
    return {
        filename: file.name,
        content_type: file.type,
    };
}

function mapEvent(event: ApiEvent): EventItem {
    return {
        id: event.id,
        name: event.name,
        startTime: event.start_time,
        endTime: event.end_time,
        isPublic: event.is_public,
        organization: event.organization,
        media: event.media,
    };
}

function withCacheBustedPublicUrl(media: ApiMediaFile): ApiMediaFile {
    if (!media.public_url) {
        return media;
    }

    const separator = media.public_url.includes("?") ? "&" : "?";
    return {
        ...media,
        public_url: `${media.public_url}${separator}v=${Date.now()}`,
    };
}

function createEventBody(payload: EventPayload, mediaFiles: File[] = []) {
    return {
        name: payload.name,
        start_time: payload.startTime,
        end_time: payload.endTime,
        is_public: payload.isPublic,
        organization_id: null,
        media: mediaFiles.map(createMediaBody),
    };
}

async function uploadFileToPresignedUrl(url: string, file: File): Promise<void> {
    const response = await fetch(url, {
        method: "PUT",
        headers: {
            "Content-Type": file.type,
        },
        body: file,
    });

    if (!response.ok) {
        throw new Error("Не удалось загрузить файл");
    }
}

async function uploadAndCompleteEventMedia(
    eventId: string,
    upload: ApiEventMediaUpload,
    file: File,
    accessToken: string,
): Promise<ApiMediaFile> {
    await uploadFileToPresignedUrl(upload.presigned_url, file);

    const completed = await apiRequest<ApiMediaFile>(
        `/event/${eventId}/media/${upload.media_file.id}/complete`,
        createAuthorizedJsonInit("POST", accessToken),
    );

    return withCacheBustedPublicUrl(completed);
}

export async function getEvents(): Promise<EventItem[]> {
    const events = await apiRequest<ApiEvent[]>("/event/");

    return events.map(mapEvent);
}

export async function createEvent(
    payload: EventCreatePayload,
    accessToken: string,
): Promise<EventItem> {
    const mediaFiles = payload.mediaFiles ?? [];
    const response = await apiRequest<ApiEventMutationResponse>(
        "/event/",
        createAuthorizedJsonInit("POST", accessToken, createEventBody(payload, mediaFiles)),
    );

    const completedMedia: ApiMediaFile[] = [];

    for (const [index, upload] of response.upload_urls.entries()) {
        completedMedia.push(
            await uploadAndCompleteEventMedia(response.id, upload, mediaFiles[index], accessToken),
        );
    }

    return mapEvent({
        ...response,
        media: [
            ...response.media.filter((media) => media.status === "ready"),
            ...completedMedia,
        ],
    });
}

export async function updateEvent(
    eventId: string,
    payload: EventPayload,
    accessToken: string,
): Promise<EventItem> {
    const response = await apiRequest<ApiEvent>(
        `/event/${eventId}`,
        createAuthorizedJsonInit("PATCH", accessToken, {
            name: payload.name,
            start_time: payload.startTime,
            end_time: payload.endTime,
            is_public: payload.isPublic,
            organization_id: null,
        }),
    );

    return mapEvent(response);
}

export async function addEventMedia(
    eventId: string,
    payload: EventMediaPayload,
    accessToken: string,
): Promise<ApiMediaFile> {
    const upload = await apiRequest<ApiEventMediaUpload>(
        `/event/${eventId}/media`,
        createAuthorizedJsonInit("POST", accessToken, createMediaBody(payload.mediaFile)),
    );

    return uploadAndCompleteEventMedia(eventId, upload, payload.mediaFile, accessToken);
}

export async function updateEventMedia(
    eventId: string,
    mediaId: string,
    payload: EventMediaPayload,
    accessToken: string,
): Promise<ApiMediaFile> {
    const upload = await apiRequest<ApiEventMediaUpload>(
        `/event/${eventId}/media/${mediaId}`,
        createAuthorizedJsonInit("PUT", accessToken, createMediaBody(payload.mediaFile)),
    );

    return uploadAndCompleteEventMedia(eventId, upload, payload.mediaFile, accessToken);
}

export async function deleteEventMedia(
    eventId: string,
    mediaId: string,
    accessToken: string,
): Promise<void> {
    await apiRequest<void>(
        `/event/${eventId}/media/${mediaId}`,
        createAuthorizedJsonInit("DELETE", accessToken),
    );
}

export async function deleteEvent(eventId: string, accessToken: string): Promise<void> {
    await apiRequest<void>(
        `/event/${eventId}`,
        createAuthorizedJsonInit("DELETE", accessToken),
    );
}
