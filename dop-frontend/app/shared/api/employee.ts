import { apiRequest } from "./client";
import type { ApiEmployee, Employee } from "./types";

function mapEmployeeFromApi(employee: ApiEmployee): Employee {
    return {
        id: employee.id,
        fullName: employee.full_name,
        position: employee.position,
        experience: employee.experience ?? "Стаж не указан",
        photoSrc: employee.photo?.public_url ?? "/images/default_avatar.jpg",
    };
}

export async function getEmployees(): Promise<Employee[]> {
    const employees = await apiRequest<ApiEmployee[]>("/employee/");

    return employees.map(mapEmployeeFromApi);
}