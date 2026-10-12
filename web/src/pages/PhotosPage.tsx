import { useEffect, useMemo, useState } from "react";
import { api, fileUrl, thumbnailUrl } from "../api";
import { useApp } from "../context";
import type { Photo } from "../types";
import { CloseIcon, PhotoIcon } from "../icons";
import { SetupPrompt } from "../components/SetupPrompt";
import "../components/Photos.css";

export default function PhotosPage() {
  const { libraries, refreshAll } = useApp();
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const load = () => api.photos({ limit: 2000 }).then(setPhotos);

  useEffect(() => {
    load().finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const groups = useMemo(() => {
    const byDay: Record<string, Photo[]> = {};
    for (const p of photos) {
      const key = p.taken_at ? p.taken_at.slice(0, 10) : "Unknown date";
      byDay[key] = byDay[key] ?? [];
      byDay[key].push(p);
    }
    return Object.entries(byDay).sort((a, b) => b[0].localeCompare(a[0]));
  }, [photos]);

  const flat = useMemo(() => groups.flatMap(([, list]) => list), [groups]);

  const close = () => setActiveIndex(null);
  const step = (delta: number) => {
    setActiveIndex((idx) => {
      if (idx === null) return idx;
      const next = idx + delta;
      if (next < 0 || next >= flat.length) return idx;
      return next;
    });
  };

  if (loading) return <div className="spinner" />;

  const hasLibrary = libraries.some((l) => l.type === "photo");

  return (
    <div>
      {photos.length === 0 ? (
        hasLibrary ? (
          <div className="empty-state">
            <PhotoIcon />
            <p>No photos found. Drop images into your photo folder and scan.</p>
          </div>
        ) : (
          <SetupPrompt
            icon={<PhotoIcon />}
            title="Add your photos folder"
            description="Pick the folder where your photos live. Quark reads dates and camera info automatically."
            type="photo"
            onCreated={() => {
              refreshAll();
              load();
            }}
          />
        )
      ) : (
        <>
          <div className="content-title">Photos</div>
          <div className="content-subtitle">{photos.length} photos</div>

          {groups.map(([day, list]) => (
            <section key={day} className="photo-day">
              <div className="photo-day-label">{day}</div>
              <div className="photo-grid">
                {list.map((photo) => {
                  const index = flat.indexOf(photo);
                  return (
                    <button
                      key={photo.media_id}
                      className="photo-thumb"
                      onClick={() => setActiveIndex(index)}
                    >
                      <img src={thumbnailUrl(photo.media_id)} alt={photo.title} loading="lazy" />
                    </button>
                  );
                })}
              </div>
            </section>
          ))}
        </>
      )}

      {activeIndex !== null && flat[activeIndex] && (
        <div className="lightbox" onClick={close}>
          <button className="lightbox-close" onClick={close}>
            <CloseIcon />
          </button>
          <button
            className="lightbox-nav prev"
            onClick={(e) => {
              e.stopPropagation();
              step(-1);
            }}
          >
            ‹
          </button>
          <img
            className="lightbox-img"
            src={fileUrl(flat[activeIndex].media_id)}
            alt={flat[activeIndex].title}
            onClick={(e) => e.stopPropagation()}
          />
          <button
            className="lightbox-nav next"
            onClick={(e) => {
              e.stopPropagation();
              step(1);
            }}
          >
            ›
          </button>
          <div className="lightbox-caption">
            {flat[activeIndex].title}
            {flat[activeIndex].taken_at ? ` · ${flat[activeIndex].taken_at.slice(0, 10)}` : ""}
          </div>
        </div>
      )}
    </div>
  );
}
