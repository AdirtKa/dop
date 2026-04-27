import { MediaCarousel } from "~/shared/ui/media-carousel";
import { HallsSection } from "~/widgets/halls-section/halls-section";

import "./home.css";

const aboutMedia = [
  {
    id: "about-1",
    type: "image" as const,
    src: "/images/default.jpg",
    alt: "Фото организации",
  },
  {
    id: "about-2",
    type: "image" as const,
    src: "/images/default.jpg",
    alt: "Фото организации",
  },
  {
    id: "about-video-1",
    type: "video" as const,
    src: "/videos/default.mp4",
    poster: "/images/default-poster.png",
  },
];

export function meta() {
  return [
    { title: "Главная" },
    {
      name: "description",
      content: "Главная страница организации",
    },
  ];
}

export default function HomePage() {
  return (
      <div className="home-page">
        <section className="home-page__about">
          <h1 className="home-page__title">Дом официальных приемов Правительства Хабаровского края</h1>

          <p className="home-page__text">
            Немного текста о самой организации и её истории. Здесь можно кратко
            рассказать, чем занимается организация, для кого она работает и какие
            мероприятия проводит.
          </p>

          <MediaCarousel items={aboutMedia} />
        </section>

        <HallsSection />
      </div>
  );
}
