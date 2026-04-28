import { useLoaderData } from "react-router";

import { EmployeeCard } from "~/widgets/employee-card/employee-card"
import "./employees.css"
import {getEmployees} from "~/shared/api/employee";

type Employee = {
    id: string;
    fullName: string;
    position: string;
    experience: string;
    photoSrc: string;
};

export async function clientLoader() {
    console.log("clientLoader employees started");

    const employees = await getEmployees();

    console.log("employees loaded:", employees);

    return {employees};
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