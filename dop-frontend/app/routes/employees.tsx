import { useLoaderData } from "react-router";

import { EmployeeCard } from "~/widgets/employee-card/employee-card"
import "./employees.css"

type Employee = {
    id: string;
    fullName: string;
    position: string;
    experience: string;
    photoSrc: string;
};

export async function clientLoader() {
    const employees: Employee[] = [
        {
            id: "1",
            fullName: "Иванов Иван Иванович",
            position: "Руководитель отдела",
            experience: "8 лет",
            photoSrc: "/images/default_avatar.jpg",
        },
        {
            id: "2",
            fullName: "Петрова Анна Сергеевна",
            position: "Менеджер мероприятий",
            experience: "5 лет",
            photoSrc: "/images/default_avatar.jpg",
        },
        {
            id: "3",
            fullName: "Сидоров Алексей Павлович",
            position: "Технический специалист",
            experience: "4 года",
            photoSrc: "/images/default_avatar.jpg",
        },
    ];

    return { employees };
}

export default function EmployeesPage() {
    const { employees } = useLoaderData<typeof clientLoader>();

    return (
        <div className="employees-page">


            <div className="employees-page__list">
                {employees.map((employee) => (
                    <EmployeeCard
                        key={employee.id}
                        fullName={employee.fullName}
                        position={employee.position}
                        experience={employee.experience}
                        photoSrc={employee.photoSrc}
                    />
                ))}
            </div>
        </div>
    );
}