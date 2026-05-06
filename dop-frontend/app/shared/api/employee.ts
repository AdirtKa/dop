import { apiRequest } from "./client";
import type {
    ApiEmployeeListItem,
    ApiEmployeeMutationResponse,
    ApiEmployeePatchResponse,
    Employee,
    EmployeeCreatePayload,
    EmployeePayload,
    EmployeePhotoPayload,
} from "./types";

const DEFAULT_EMPLOYEE_PHOTO = "/images/default_avatar.jpg";

function getPhotoSrc(publicUrl: string | null | undefined): string {
    return publicUrl ?? DEFAULT_EMPLOYEE_PHOTO;
}

function mapEmployeeFromListItem(employee: ApiEmployeeListItem): Employee {
    return {
        id: employee.id,
        fullName: employee.full_name,
        position: employee.position,
        experience: null,
        photo: employee.photo,
        photoSrc: getPhotoSrc(employee.photo?.public_url),
    };
}

function mapEmployeeFromMutationResponse(employee: ApiEmployeeMutationResponse): Employee {
    return {
        id: employee.id,
        fullName: employee.full_name,
        position: employee.position,
        experience: employee.experience,
        photo: employee.photo,
        photoSrc: getPhotoSrc(employee.photo?.public_url),
    };
}

function mapEmployeeFromPatchResponse(
    employee: ApiEmployeePatchResponse,
    experience: string,
): Employee {
    return {
        id: employee.id,
        fullName: employee.full_name,
        position: employee.position,
        experience,
        photo: employee.photo,
        photoSrc: getPhotoSrc(employee.photo?.public_url),
    };
}

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

function createPhotoBody(file: File): { photo_filename: string; content_type: string } {
    return {
        photo_filename: file.name,
        content_type: file.type,
    };
}

export async function getEmployees(): Promise<Employee[]> {
    const employees = await apiRequest<ApiEmployeeListItem[]>("/employee/");

    return employees.map(mapEmployeeFromListItem);
}

export async function createEmployee(
    payload: EmployeeCreatePayload,
    accessToken: string,
): Promise<{ employee: Employee; presignedUrl: string | null }> {
    const response = await apiRequest<ApiEmployeeMutationResponse>(
        "/employee/",
        createAuthorizedJsonInit("POST", accessToken, {
            full_name: payload.fullName,
            position: payload.position,
            experience: payload.experience,
            ...(payload.photoFile ? createPhotoBody(payload.photoFile) : {}),
        }),
    );

    return {
        employee: mapEmployeeFromMutationResponse(response),
        presignedUrl: response.presigned_url,
    };
}

export async function updateEmployee(
    employeeId: string,
    payload: EmployeePayload,
    accessToken: string,
): Promise<Employee> {
    const response = await apiRequest<ApiEmployeePatchResponse>(
        `/employee/${employeeId}`,
        createAuthorizedJsonInit("PATCH", accessToken, {
            full_name: payload.fullName,
            position: payload.position,
            experience: payload.experience,
        }),
    );

    return mapEmployeeFromPatchResponse(response, payload.experience);
}

export async function updateEmployeePhoto(
    employeeId: string,
    payload: EmployeePhotoPayload,
    accessToken: string,
): Promise<{ employee: Employee; presignedUrl: string | null }> {
    const response = await apiRequest<ApiEmployeeMutationResponse>(
        `/employee/${employeeId}/photo`,
        createAuthorizedJsonInit("PUT", accessToken, createPhotoBody(payload.photoFile)),
    );

    return {
        employee: mapEmployeeFromMutationResponse(response),
        presignedUrl: response.presigned_url,
    };
}

export async function deleteEmployee(employeeId: string, accessToken: string): Promise<void> {
    await apiRequest<void>(
        `/employee/${employeeId}`,
        createAuthorizedJsonInit("DELETE", accessToken),
    );
}

export async function uploadFileToPresignedUrl(url: string, file: File): Promise<void> {
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
