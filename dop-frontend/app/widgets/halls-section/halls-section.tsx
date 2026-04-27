import { useState } from "react";

import { MediaCarousel } from "~/shared/ui/media-carousel";

import "./halls-section.css";

type Hall = {
    id: string;
    title: string;
    shortTitle: string;
    description: string;
    capacity: string;
    media: {
        id: string;
        type: "image" | "video";
        src: string;
        alt?: string;
        poster?: string;
    }[];
};

const halls: Hall[] = [
    {
        id: "meeting",
        title: "Зал для переговоров",
        shortTitle: "Зал для переговоров",
        description:
            "Уютное пространство для деловых встреч, переговоров, собеседований и небольших рабочих обсуждений.",
        capacity: "До 12 человек",
        media: [
            {
                id: "meeting-1",
                type: "image",
                src: "/images/halls/small_hall_1.jpg",
                alt: "Зал для переговоров",
            },
            {
                id: "meeting-2",
                type: "image",
                src: "/images/halls/small_hall_2.jpg",
                alt: "Зал для переговоров",
            },
        ],
    },
    {
        id: "buffet",
        title: "Фуршетный зал",
        shortTitle: "Фуршетный зал",
        description:
            "Просторный зал для фуршетов, кофе-брейков, неформальных встреч и небольших праздничных мероприятий.",
        capacity: "До 30 человек",
        media: [
            {
                id: "buffet-1",
                type: "image",
                src: "/images/default.jpg",
                alt: "Фуршетный зал",
            },
            {
                id: "buffet-2",
                type: "image",
                src: "/images/default.jpg",
                alt: "Фуршетный зал",
            },
        ],
    },
    {
        id: "large",
        title: "Большой зал",
        shortTitle: "Большой зал",
        description:
            "Основной зал для конференций, лекций, презентаций, мастер-классов и крупных мероприятий.",
        capacity: "До 80 человек",
        media: [
            {
                id: "large-1",
                type: "image",
                src: "/images/default.jpg",
                alt: "Большой зал",
            },
            {
                id: "large-video-1",
                type: "video",
                src: "/videos/default.mp4",
                poster: "/images/default-poster.png",
            },
        ],
    },
];

export function HallsSection() {
    const [activeHallId, setActiveHallId] = useState(halls[0].id);

    const activeHall = halls.find((hall) => hall.id === activeHallId) ?? halls[0];

    return (
        <section className="halls-section">
            <div className="halls-section__intro">
                <h2 className="halls-section__title">Залы для мероприятий</h2>

                <p className="halls-section__text">
                    У нас есть 3 зала для проведения мероприятий: зал для переговоров,
                    фуршетный зал и большой зал. Выберите нужный зал, чтобы посмотреть
                    его описание и фотографии.
                </p>
            </div>

            <div className="halls-section__tabs" role="tablist">
                {halls.map((hall) => (
                    <button
                        key={hall.id}
                        type="button"
                        role="tab"
                        aria-selected={activeHall.id === hall.id}
                        className={
                            activeHall.id === hall.id
                                ? "halls-section__tab halls-section__tab--active"
                                : "halls-section__tab"
                        }
                        onClick={() => setActiveHallId(hall.id)}
                    >
                        {hall.shortTitle}
                    </button>
                ))}
            </div>

            <article className="halls-section__details">
                <div className="halls-section__details-text">
                    <h3 className="halls-section__hall-title">{activeHall.title}</h3>

                    <p className="halls-section__description">
                        {activeHall.description}
                    </p>

                    <p className="halls-section__capacity">
                        Вместимость: <span>{activeHall.capacity}</span>
                    </p>
                </div>

                <MediaCarousel items={activeHall.media} />
            </article>
        </section>
    );
}