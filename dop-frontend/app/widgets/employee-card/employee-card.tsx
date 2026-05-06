import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";

import type { Employee, EmployeePayload } from "~/shared/api/types";
import "./employee-card.css";

type EmployeeCardProps = {
    canManage: boolean;
    employee: Employee;
    onDelete: (employee: Employee) => Promise<void>;
    onSave: (employee: Employee, payload: EmployeePayload) => Promise<void>;
    onUploadPhoto: (employee: Employee, file: File) => Promise<void>;
};

export function EmployeeCard({
    canManage,
    employee,
    onDelete,
    onSave,
    onUploadPhoto,
}: EmployeeCardProps) {
    const [isEditing, setIsEditing] = useState(false);
    const [fullName, setFullName] = useState(employee.fullName);
    const [position, setPosition] = useState(employee.position);
    const [experience, setExperience] = useState(employee.experience ?? "");
    const [selectedFileName, setSelectedFileName] = useState("");
    const [isSaving, setIsSaving] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const displayExperience = employee.experience?.trim() ? employee.experience : "Стаж не указан";

    useEffect(() => {
        if (isEditing) {
            return;
        }

        setFullName(employee.fullName);
        setPosition(employee.position);
        setExperience(employee.experience ?? "");
    }, [employee, isEditing]);

    function resetForm() {
        setFullName(employee.fullName);
        setPosition(employee.position);
        setExperience(employee.experience ?? "");
        setSelectedFileName("");
        setErrorMessage(null);
    }

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsSaving(true);
        setErrorMessage(null);

        try {
            await onSave(employee, {
                fullName: fullName.trim(),
                position: position.trim(),
                experience: experience.trim(),
            });
            setIsEditing(false);
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "Не удалось сохранить изменения");
        } finally {
            setIsSaving(false);
        }
    }

    async function handleDelete() {
        setIsSaving(true);
        setErrorMessage(null);

        try {
            await onDelete(employee);
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "Не удалось удалить сотрудника");
            setIsSaving(false);
        }
    }

    async function handlePhotoChange(event: ChangeEvent<HTMLInputElement>) {
        const file = event.target.files?.[0];

        if (!file) {
            return;
        }

        setSelectedFileName(file.name);
        setIsSaving(true);
        setErrorMessage(null);

        try {
            await onUploadPhoto(employee, file);
            setSelectedFileName("");
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "Не удалось обновить фото");
        } finally {
            event.target.value = "";
            setIsSaving(false);
        }
    }

    if (isEditing) {
        return (
            <article className="employee-card employee-card--editing">
                <form className="employee-card__edit-form" onSubmit={handleSubmit}>
                    <div className="employee-card__info">
                        <label className="employee-card__field">
                            <span>ФИО</span>
                            <input
                                value={fullName}
                                onChange={(event) => setFullName(event.target.value)}
                                className="employee-card__input"
                                required
                            />
                        </label>

                        <label className="employee-card__field">
                            <span>Должность</span>
                            <input
                                value={position}
                                onChange={(event) => setPosition(event.target.value)}
                                className="employee-card__input"
                                required
                            />
                        </label>

                        <label className="employee-card__field">
                            <span>Стаж</span>
                            <input
                                value={experience}
                                onChange={(event) => setExperience(event.target.value)}
                                className="employee-card__input"
                                required
                            />
                        </label>

                        <label className="employee-card__upload employee-card__upload--inline">
                            <span>Фото</span>
                            <div className="employee-card__upload-row">
                                <span className="employee-card__upload-button">Выбрать файл</span>
                                <span className="employee-card__upload-name">
                                    {selectedFileName || "Файл не выбран"}
                                </span>
                            </div>
                            <input
                                type="file"
                                accept="image/jpeg,image/png,image/webp"
                                onChange={handlePhotoChange}
                                disabled={isSaving}
                            />
                        </label>

                        {errorMessage ? <p className="employee-card__error">{errorMessage}</p> : null}

                        <div className="employee-card__actions">
                            <button className="employee-card__button" type="submit" disabled={isSaving}>
                                Сохранить
                            </button>
                            <button
                                className="employee-card__button employee-card__button--ghost"
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
                    </div>

                    <img className="employee-card__photo" src={employee.photoSrc} alt={employee.fullName} />
                </form>
            </article>
        );
    }

    return (
        <article className="employee-card">
            <div className="employee-card__info">
                <h3 className="employee-card__name">{employee.fullName}</h3>
                <p className="employee-card__position">{employee.position}</p>
                <p className="employee-card__experience">Стаж работы: {displayExperience}</p>

                {canManage ? (
                    <>
                        <div className="employee-card__actions">
                            <button
                                className="employee-card__button"
                                type="button"
                                onClick={() => {
                                    resetForm();
                                    setIsEditing(true);
                                }}
                            >
                                Редактировать
                            </button>
                            <button
                                className="employee-card__button employee-card__button--danger"
                                type="button"
                                onClick={handleDelete}
                                disabled={isSaving}
                            >
                                Удалить
                            </button>
                        </div>

                        <label className="employee-card__upload">
                            <span>Обновить фото</span>
                            <div className="employee-card__upload-row">
                                <span className="employee-card__upload-button">Выбрать файл</span>
                                <span className="employee-card__upload-name">
                                    {selectedFileName || "Файл не выбран"}
                                </span>
                            </div>
                            <input
                                type="file"
                                accept="image/jpeg,image/png,image/webp"
                                onChange={handlePhotoChange}
                                disabled={isSaving}
                            />
                        </label>
                    </>
                ) : null}

                {errorMessage ? <p className="employee-card__error">{errorMessage}</p> : null}
            </div>

            <img className="employee-card__photo" src={employee.photoSrc} alt={employee.fullName} />
        </article>
    );
}
