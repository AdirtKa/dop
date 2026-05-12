import { useMemo, useState, type ChangeEvent, type FormEvent } from "react";
import { useLoaderData } from "react-router";

import {
    createEmployee,
    deleteEmployee,
    getEmployees,
    updateEmployee,
    updateEmployeePhoto,
    uploadFileToPresignedUrl,
} from "~/shared/api/employee";
import { useAuth } from "~/shared/auth/auth-context";
import type { Employee, EmployeePayload } from "~/shared/api/types";
import { EmployeeCard } from "~/widgets/employee-card/employee-card";
import "./employees.css";

type EmployeesLoaderData = {
    employees: Employee[];
};

const ALLOWED_PHOTO_TYPES = ["image/jpeg", "image/png", "image/webp"];

export async function clientLoader(): Promise<EmployeesLoaderData> {
    const employees = await getEmployees();

    return { employees };
}

function isUnauthorizedError(error: unknown): boolean {
    return error instanceof Error && error.message.includes("401");
}

export default function EmployeesPage() {
    const { employees: initialEmployees } = useLoaderData<typeof clientLoader>();
    const { accessToken, isAdmin, refreshUserSession } = useAuth();
    const [employees, setEmployees] = useState(initialEmployees);
    const [isCreating, setIsCreating] = useState(false);
    const [createError, setCreateError] = useState<string | null>(null);
    const [newEmployee, setNewEmployee] = useState({
        fullName: "",
        position: "",
        experience: "",
    });
    const [newPhotoFile, setNewPhotoFile] = useState<File | null>(null);

    const hasEmployees = employees.length > 0;
    const sortedEmployees = useMemo(
        () => [...employees].sort((left, right) => left.fullName.localeCompare(right.fullName, "ru")),
        [employees],
    );

    async function runAuthorized<T>(action: (token: string) => Promise<T>): Promise<T> {
        let token = accessToken;

        if (!token) {
            token = await refreshUserSession();
        }

        if (!token) {
            throw new Error("Нужен вход администратора");
        }

        try {
            return await action(token);
        } catch (error) {
            if (!isUnauthorizedError(error)) {
                throw error;
            }

            const refreshedToken = await refreshUserSession();

            if (!refreshedToken) {
                throw new Error("Сессия администратора истекла");
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
                createEmployee(
                    {
                        fullName: newEmployee.fullName.trim(),
                        position: newEmployee.position.trim(),
                        experience: newEmployee.experience.trim(),
                        photoFile: newPhotoFile,
                    },
                    token,
                ),
            );

            if (created.presignedUrl && newPhotoFile) {
                await uploadFileToPresignedUrl(created.presignedUrl, newPhotoFile);
            }

            setEmployees((current) => [created.employee, ...current]);
            setNewEmployee({
                fullName: "",
                position: "",
                experience: "",
            });
            setNewPhotoFile(null);
        } catch (error) {
            setCreateError(error instanceof Error ? error.message : "Не удалось создать сотрудника");
        } finally {
            setIsCreating(false);
        }
    }

    async function handleUpdate(employee: Employee, payload: EmployeePayload) {
        const updated = await runAuthorized((token) => updateEmployee(employee.id, payload, token));

        setEmployees((current) =>
            current.map((item) => (item.id === employee.id ? updated : item)),
        );
    }

    async function handleDelete(employee: Employee) {
        await runAuthorized((token) => deleteEmployee(employee.id, token));

        setEmployees((current) => current.filter((item) => item.id !== employee.id));
    }

    async function handleUpdatePhoto(employee: Employee, file: File) {
        const updated = await runAuthorized((token) =>
            updateEmployeePhoto(employee.id, { photoFile: file }, token),
        );

            if (updated.presignedUrl) {
                await uploadFileToPresignedUrl(updated.presignedUrl, file);
            }

            setEmployees((current) =>
            current.map((item) =>
                item.id === employee.id
                    ? {
                        ...updated.employee,
                        photoSrc: URL.createObjectURL(file),
                    }
                    : item,
            ),
        );
    }

    function handlePhotoSelection(event: ChangeEvent<HTMLInputElement>) {
        const file = event.target.files?.[0] ?? null;

        if (file && !ALLOWED_PHOTO_TYPES.includes(file.type)) {
            setCreateError("Поддерживаются только JPG, PNG и WEBP");
            setNewPhotoFile(null);
            event.target.value = "";
            return;
        }

        setCreateError(null);
        setNewPhotoFile(file);
    }

    return (
        <div className="employees-page">
            <div className="employees-page__header">
                <div>
                    <h1 className="employees-page__title">Сотрудники</h1>
                    <p className="employees-page__subtitle">
                        Публичный список сотрудников. После входа администратор может редактировать карточки прямо на странице.
                    </p>
                </div>
            </div>

            {isAdmin ? (
                <section className="employees-page__create">
                    <h2 className="employees-page__section-title">Добавить сотрудника</h2>
                    <form className="employees-page__create-form" onSubmit={handleCreate}>
                        <label className="employees-page__field">
                            <span>ФИО</span>
                            <input
                                value={newEmployee.fullName}
                                onChange={(event) =>
                                    setNewEmployee((current) => ({ ...current, fullName: event.target.value }))
                                }
                                required
                            />
                        </label>

                        <label className="employees-page__field">
                            <span>Должность</span>
                            <input
                                value={newEmployee.position}
                                onChange={(event) =>
                                    setNewEmployee((current) => ({ ...current, position: event.target.value }))
                                }
                                required
                            />
                        </label>

                        <label className="employees-page__field">
                            <span>Стаж</span>
                            <input
                                value={newEmployee.experience}
                                onChange={(event) =>
                                    setNewEmployee((current) => ({ ...current, experience: event.target.value }))
                                }
                                required
                            />
                        </label>

                        <label className="employees-page__field">
                            <span>Фото</span>
                            <input
                                type="file"
                                accept={ALLOWED_PHOTO_TYPES.join(",")}
                                onChange={handlePhotoSelection}
                            />
                        </label>

                        {createError ? <p className="employees-page__error">{createError}</p> : null}

                        <button className="employees-page__submit" type="submit" disabled={isCreating}>
                            Создать сотрудника
                        </button>
                    </form>
                </section>
            ) : null}

            <div className="employees-page__list">
                {hasEmployees ? (
                    sortedEmployees.map((employee) => (
                        <EmployeeCard
                            key={employee.id}
                            canManage={isAdmin}
                            employee={employee}
                            onDelete={handleDelete}
                            onSave={handleUpdate}
                            onUploadPhoto={handleUpdatePhoto}
                        />
                    ))
                ) : (
                    <p className="employees-page__empty">Сотрудники пока не добавлены.</p>
                )}
            </div>
        </div>
    );
}
