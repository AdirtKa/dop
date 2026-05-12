export type ApiMediaKind = "image" | "video";

export type ApiMediaFile = {
    id: string;
    public_url: string | null;
    mime_type: string;
    kind: ApiMediaKind;
    status?: "pending" | "ready" | "failed" | null;
    created_at: string;
};

export type ApiEmployeeListItem = {
    id: string;
    full_name: string;
    position: string;
    photo: ApiMediaFile | null;
};

export type ApiEmployeeMutationResponse = {
    id: string;
    full_name: string;
    position: string;
    experience: string | null;
    photo: ApiMediaFile | null;
    presigned_url: string | null;
};

export type ApiEmployeePatchResponse = {
    id: string;
    full_name: string;
    position: string;
    photo: ApiMediaFile | null;
};

export type Employee = {
    id: string;
    fullName: string;
    position: string;
    experience: string | null;
    photo: ApiMediaFile | null;
    photoSrc: string;
};

export type EmployeePayload = {
    fullName: string;
    position: string;
    experience: string;
};

export type EmployeeCreatePayload = EmployeePayload & {
    photoFile?: File | null;
};

export type EmployeePhotoPayload = {
    photoFile: File;
};

export type AuthRole = "admin" | "employee" | "organization";

export type AuthUser = {
    id: string;
    username: string;
    role: AuthRole;
    is_active: boolean;
};

export type LoginPayload = {
    username: string;
    password: string;
};

export type TokenResponse = {
    access_token: string;
    token_type: string;
};

export type LoginResponse = TokenResponse & {
    user: AuthUser;
};

export type ApiOrganizationShort = {
    id: string;
    name: string;
};

export type ApiEvent = {
    id: string;
    name: string;
    start_time: string;
    end_time: string;
    is_public: boolean;
    organization: ApiOrganizationShort | null;
    media: ApiMediaFile[];
};

export type ApiEventMediaUpload = {
    media_file: ApiMediaFile;
    presigned_url: string;
};

export type ApiEventMediaUploadError = {
    filename: string;
    detail: string;
};

export type ApiEventMutationResponse = ApiEvent & {
    upload_urls: ApiEventMediaUpload[];
    upload_errors: ApiEventMediaUploadError[];
};

export type EventPayload = {
    name: string;
    startTime: string;
    endTime: string;
    isPublic: boolean;
};

export type EventCreatePayload = EventPayload & {
    mediaFiles?: File[];
};

export type EventMediaPayload = {
    mediaFile: File;
};

export type EventItem = {
    id: string;
    name: string;
    startTime: string;
    endTime: string;
    isPublic: boolean;
    organization: ApiOrganizationShort | null;
    media: ApiMediaFile[];
};
