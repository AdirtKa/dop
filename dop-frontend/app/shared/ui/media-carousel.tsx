import { useEffect, useState } from "react";

import "./media-carousel.css";

type MediaItem = {
    id: string;
    type: "image" | "video";
    src: string;
    alt?: string;
    poster?: string;
};

type MediaCarouselProps = {
    items: MediaItem[];
    onCurrentItemChange?: (item: MediaItem) => void;
};

export function MediaCarousel({ items, onCurrentItemChange }: MediaCarouselProps) {
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
        setCurrentIndex((index) => Math.min(index, Math.max(items.length - 1, 0)));
    }, [items.length]);

    if (items.length === 0) {
        return null;
    }

    const currentItem = items[currentIndex];

    useEffect(() => {
        if (currentItem) {
            onCurrentItemChange?.(currentItem);
        }
    }, [currentItem, onCurrentItemChange]);

    const goToPrev = () => {
        setCurrentIndex((prev) => (prev === 0 ? items.length - 1 : prev - 1));
    };

    const goToNext = () => {
        setCurrentIndex((prev) => (prev === items.length - 1 ? 0 : prev + 1));
    };

    return (
        <section className="media-carousel" aria-label="Карусель медиа">
            <div className="media-carousel__viewer">
                {currentItem.type === "image" && (
                    <img
                        src={currentItem.src}
                        alt={currentItem.alt ?? ""}
                        className="media-carousel__media"
                    />
                )}

                {currentItem.type === "video" && (
                    <video
                        src={currentItem.src}
                        poster={currentItem.poster}
                        className="media-carousel__media"
                        controls
                    />
                )}

                {items.length > 1 && (
                    <>
                        <button
                            type="button"
                            className="media-carousel__button media-carousel__button--prev"
                            onClick={goToPrev}
                            aria-label="Предыдущее медиа"
                        >
                            ‹
                        </button>

                        <button
                            type="button"
                            className="media-carousel__button media-carousel__button--next"
                            onClick={goToNext}
                            aria-label="Следующее медиа"
                        >
                            ›
                        </button>
                    </>
                )}
            </div>

            {items.length > 1 && (
                <div className="media-carousel__dots">
                    {items.map((item, index) => (
                        <button
                            key={item.id}
                            type="button"
                            className={
                                index === currentIndex
                                    ? "media-carousel__dot active"
                                    : "media-carousel__dot"
                            }
                            onClick={() => setCurrentIndex(index)}
                            aria-label={`Перейти к медиа ${index + 1}`}
                        />
                    ))}
                </div>
            )}
        </section>
    );
}
