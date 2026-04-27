import "./employee-card.css";

type EmployeeCardProps = {
    fullName: string;
    position: string;
    experience: string;
    photoSrc: string;
    photoAlt?: string;
};

export function EmployeeCard({
                                 fullName,
                                 position,
                                 experience,
                                 photoSrc,
                                 photoAlt,
                             }: EmployeeCardProps) {
    return (
        <article className="employee-card">
        <div className="employee-card__info">
        <h3 className="employee-card__name">{fullName}</h3>

            <p className="employee-card__position">{position}</p>

        <p className="employee-card__experience">
        Стаж работы: {experience}
    </p>
    </div>

    <img
    className="employee-card__photo"
    src={photoSrc}
    alt={photoAlt ?? fullName}
    />
    </article>
);
}