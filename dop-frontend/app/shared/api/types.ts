export type ApiMediaKind = "image" | "video";

export type ApiMediaFile = {
    id: string;
    storage_key: string;
    public_url: string | null;
    mime_type: string;
    kind: ApiMediaKind;
    created_at: string;
};

export type ApiEmployee = {
    id: string;
    full_name: string;
    position: string;
    experience: string | null;
    photo: ApiMediaFile | null;
    created_at: string;
};

export type Employee = {
    id: string;
    fullName: string;
    position: string;
    experience: string;
    photoSrc: string;
};